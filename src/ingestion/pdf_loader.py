import pdfplumber
import json
import uuid
from pathlib import Path
from src.config import RAW_DIR, TEXTS_DIR, TABLES_DIR
from src.ingestion.text_cleaner import TextCleaner
from src.ingestion.table_extractor import TableExtractor


def processar_documento(nome_arquivo: str):
    """
    Função principal da Etapa 1: Ingestão.
    Lê o PDF, extrai tabelas (Camelot) e textos (pdfplumber), limpa e salva.
    """
    caminho_pdf = RAW_DIR / nome_arquivo
    if not caminho_pdf.exists():
        raise FileNotFoundError(f"Arquivo {nome_arquivo} não encontrado em {RAW_DIR}")

    print(f"--- Iniciando Processamento: {nome_arquivo} ---")

    # 1. Extração de Tabelas (Prioridade alta para garantir integridade estrutural )
    extrator_tabelas = TableExtractor()
    lista_tabelas = extrator_tabelas.extrair_com_camelot(caminho_pdf)

    # Salva tabelas
    for tab in lista_tabelas:
        tab['origem'] = nome_arquivo
        extrator_tabelas.salvar_tabela(tab, TABLES_DIR)

    print(f"   [OK] {len(lista_tabelas)} tabelas extraídas e salvas.")

    # 2. Extração de Texto (Excluindo a área das tabelas se possível, ou bruto)
    print(f"   Extraindo textos com pdfplumber...")

    with pdfplumber.open(caminho_pdf) as pdf:
        for i, pagina in enumerate(pdf.pages):
            # Extrai texto cru
            texto_bruto = pagina.extract_text()

            if texto_bruto:
                # Aplica a limpeza definida em text_cleaner.py
                texto_limpo = TextCleaner.processar(texto_bruto)

                # Prepara objeto JSON
                dados_texto = {
                    "id": str(uuid.uuid4()),
                    "pagina": i + 1,
                    "origem": nome_arquivo,
                    "conteudo": texto_limpo,
                    "tipo": "texto_narrativo"
                }

                # Salva texto
                nome_json = f"text_pg{i + 1}_{dados_texto['id'][:8]}.json"
                with open(TEXTS_DIR / nome_json, 'w', encoding='utf-8') as f:
                    json.dump(dados_texto, f, ensure_ascii=False, indent=4)

    print(f"   [OK] Textos processados e salvos em {TEXTS_DIR}")
    print("--- Fim da Etapa 1 ---")


if __name__ == "__main__":
    # Exemplo de uso para teste rápido
    # processar_documento("relatorio_exemplo.pdf")
    pass
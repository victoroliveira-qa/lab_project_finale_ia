import json
import shutil
from pathlib import Path
from src.config import RAW_DIR, PROCESSED_DIR
from src.ingestion.text_cleaner import limpar_texto
from src.ingestion.table_extractor import extrair_tabelas_camelot
from langchain_community.document_loaders import PDFPlumberLoader


def salvar_json(dados, caminho_arquivo):
    """Salva dados em JSON garantindo a criação das pastas."""
    caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)


def processar_todos_pdfs():
    """
    Lê TODOS os PDFs da pasta data/raw e processa um por um.
    Cria pastas separadas para cada PDF em data/processed/.
    """
    pdfs = list(RAW_DIR.glob("*.pdf"))

    if not pdfs:
        print(f"⚠️ Nenhum PDF encontrado em {RAW_DIR}")
        return []

    print(f"📂 Encontrados {len(pdfs)} arquivos para processar.")

    pdfs_processados = []

    for pdf_path in pdfs:
        nome_pdf = pdf_path.stem  # Ex: 'relatorio_2024'
        print(f"\n--- 🚀 Processando: {pdf_path.name} ---")

        # 1. Cria estrutura de pastas específica para ESTE pdf
        # Ex: data/processed/relatorio_2024/texts
        pdf_dir = PROCESSED_DIR / nome_pdf
        texts_dir = pdf_dir / "texts"
        tables_dir = pdf_dir / "tables"

        # Limpa processamento anterior desse PDF específico se existir
        if pdf_dir.exists():
            shutil.rmtree(pdf_dir)

        texts_dir.mkdir(parents=True, exist_ok=True)
        tables_dir.mkdir(parents=True, exist_ok=True)

        # 2. Extração de Texto (PDFPlumber)
        loader = PDFPlumberLoader(str(pdf_path))
        docs = loader.load()

        print(f"   📄 Extraindo textos de {len(docs)} páginas...")
        for i, doc in enumerate(docs):
            conteudo_limpo = limpar_texto(doc.page_content)
            if not conteudo_limpo: continue

            meta = {
                "content": conteudo_limpo,
                "source": pdf_path.name,  # Guarda o nome do arquivo original
                "page_number": doc.metadata.get("page", 0) + 1,
                "type": "text"
            }
            salvar_json(meta, texts_dir / f"page_{i + 1}.json")

        # 3. Extração de Tabelas (Camelot)
        print(f"   📊 Extraindo tabelas...")
        extrair_tabelas_camelot(pdf_path, tables_dir)

        pdfs_processados.append(nome_pdf)

    return pdfs_processados
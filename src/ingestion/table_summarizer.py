import json
import os
from langchain_core.output_parsers import StrOutputParser
from src.config import TABLES_DIR, SUMMARIES_DIR
from src.models.llm_factory import LLMFactory
from src.prompts.templates import PROMPT_RESUMO


def gerar_resumos_tabelas():
    """
    Lê os arquivos JSON de tabelas extraídas e gera resumos semânticos usando LLM.
    Essencial para que o RAG consiga encontrar tabelas através de perguntas em linguagem natural.
    """
    # Garante que a pasta de saída existe
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

    arquivos_tabela = list(TABLES_DIR.glob("*.json"))

    if not arquivos_tabela:
        print(f"⚠️ Nenhuma tabela encontrada em {TABLES_DIR}. Pule esta etapa se o PDF não tiver tabelas.")
        return

    print(f"--- Iniciando sumarização de {len(arquivos_tabela)} tabelas... ---")

    # Inicializa o LLM (Vai usar Ollama ou OpenAI dependendo do seu config.py)
    # Usamos temperature=0 para resumos factuais
    llm = LLMFactory.create_chat_model(temperature=0)

    # Cria a cadeia: Prompt -> LLM -> Texto
    chain = PROMPT_RESUMO | llm | StrOutputParser()

    for arquivo in arquivos_tabela:
        try:
            # 1. Ler a tabela bruta
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)

            # Algumas tabelas podem vir com chaves diferentes dependendo se vieram do camelot ou unstructured
            # Aqui normalizamos para pegar o conteúdo HTML ou Texto
            conteudo = dados.get("conteudo_html") or dados.get("conteudo_csv") or dados.get("content") or str(dados)
            tabela_id = dados.get("id_tabela") or dados.get("id") or arquivo.stem

            arquivo_saida = SUMMARIES_DIR / f"summary_{tabela_id}.txt"

            # Se o resumo já existe, pula (cache simples)
            if arquivo_saida.exists():
                print(f"   [Cache] Resumo já existe para: {tabela_id}")
                continue

            print(f"   ⏳ Gerando resumo para tabela: {tabela_id}...")

            # 2. Invocar o LLM
            # O prompt espera a variável 'conteudo_tabela' (definida no yaml)
            resumo = chain.invoke({"conteudo_tabela": conteudo})

            # 3. Salvar o resumo
            with open(arquivo_saida, "w", encoding="utf-8") as f:
                f.write(resumo)

        except Exception as e:
            print(f"   ❌ Erro ao resumir {arquivo.name}: {e}")

    print("--- Sumarização Concluída ---")


if __name__ == "__main__":
    gerar_resumos_tabelas()
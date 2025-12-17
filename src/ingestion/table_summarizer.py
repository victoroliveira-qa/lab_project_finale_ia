import json
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.models.llm_factory import LLMFactory
from src.config import PROCESSED_DIR


def gerar_resumos_tabelas():
    """Gera resumos para todas as tabelas de todos os PDFs processados."""

    # Busca todas as pastas de PDF dentro de processed
    pastas_pdfs = [f for f in PROCESSED_DIR.iterdir() if f.is_dir()]

    # Configura o LLM
    llm = LLMFactory.create_chat_model(temperature=0)
    prompt = ChatPromptTemplate.from_template(
        """
        Você é um analista econômico experiente.
        Analise a seguinte tabela em HTML do Banco Central:

        {tabela}

        Tarefa: Gere um resumo narrativo destacando as principais tendências, 
        picos, quedas e números críticos. Não apenas descreva as linhas, 
        interprete o significado econômico.
        """
    )
    chain = prompt | llm | StrOutputParser()

    for pasta in pastas_pdfs:
        dir_tabelas = pasta / "tables"
        dir_resumos = pasta / "summaries"
        dir_resumos.mkdir(exist_ok=True)

        # Pega todos os JSONs de tabela
        arquivos_tabela = list(dir_tabelas.glob("*.json"))

        if not arquivos_tabela: continue

        print(f"   ∑ Resumindo {len(arquivos_tabela)} tabelas de {pasta.name}...")

        for arq in arquivos_tabela:
            try:
                # 1. Ler a tabela original
                with open(arq, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                html_tabela = data.get('content', '')
                if not html_tabela: continue

                # 2. Gerar Resumo via LLM
                resumo = chain.invoke({"tabela": html_tabela})

                # 3. Salvar o Resumo (mantendo metadados para rastreabilidade)
                novo_json = {
                    "content": resumo,  # O conteúdo agora é o texto explicativo
                    "original_table_content": html_tabela,  # Guardamos o original se precisar
                    "source": data.get('source'),
                    "page_number": data.get('page_number'),
                    "type": "table_summary"
                }

                # Salva com prefixo summary_
                caminho_resumo = dir_resumos / f"summary_{arq.name}"
                with open(caminho_resumo, 'w', encoding='utf-8') as f_out:
                    json.dump(novo_json, f_out, ensure_ascii=False, indent=4)

            except Exception as e:
                print(f"      Erro ao resumir {arq.name}: {e}")
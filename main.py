import sys
import os
import json
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from src.config import VECTOR_DB_DIR, PROCESSED_DIR
from src.ingestion.pdf_loader import processar_todos_pdfs
from src.ingestion.table_summarizer import gerar_resumos_tabelas
from src.models.rag_engine import RAGEngine
from src.models.llm_factory import LLMFactory
from src.prompts.templates import PROMPT_RAG_FINAL, PROMPT_EXTRACAO
from src.evaluation.hallucination_check import VerificadorAlucinacao
from src.evaluation.saver import configurar_logger, salvar_relacoes_csv

logger = configurar_logger()


# --- FUNÇÃO NOVA: Formata o contexto para exibir a fonte no Chat ---
def formatar_docs_com_fonte(docs):
    contexto_formatado = []
    for d in docs:
        fonte = d.metadata.get('source', 'Desconhecido')
        pag = d.metadata.get('page', '?')
        tipo = d.metadata.get('type', 'texto')

        # Cria um cabeçalho visível para o LLM e para o usuário
        header = f"\n--- [FONTE: {fonte} | Pág: {pag} | Tipo: {tipo}] ---\n"
        contexto_formatado.append(header + d.page_content)

    return "\n".join(contexto_formatado)


def pipeline_extracao_automatica():
    """Varre todos os dados processados e gera o CSV automaticamente."""
    print("\n🏭 INICIANDO EXTRAÇÃO AUTOMÁTICA DE RELAÇÕES (CSV)...")
    logger.info("Iniciando extração batch automática")

    llm = LLMFactory.create_chat_model(temperature=0)
    chain = PROMPT_EXTRACAO | llm | StrOutputParser()

    # Busca recursiva em todas as pastas
    arquivos = list(PROCESSED_DIR.rglob("texts/*.json"))
    total = len(arquivos)

    count_saved = 0
    for i, arq in enumerate(arquivos):
        try:
            with open(arq, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Só processa se tiver texto substancial
            if len(data.get('content', '')) < 100: continue

            print(f"   Processando {i}/{total}: {data.get('source')} (pág {data.get('page_number')})...", end="\r")

            res = chain.invoke({"texto_input": data['content'], "tabela_input": "Batch Auto"})
            salvar_relacoes_csv(res, fonte=f"AUTO_{data.get('source')}")
            count_saved += 1
        except Exception as e:
            logger.error(f"Erro no batch {arq}: {e}")

    print(f"\n✅ Extração concluída! {count_saved} fragmentos processados e salvos no CSV.")


def pipeline_ingestao_completa():
    # 1. Processa TODOS os PDFs
    pdfs_processados = processar_todos_pdfs()

    if not pdfs_processados:
        print("Nenhum PDF novo processado.")
        return

    # 2. Gera Resumos
    gerar_resumos_tabelas()

    # 3. Indexa Tudo
    engine = RAGEngine()
    engine.indexar_dados()

    # 4. PASSO NOVO: Gera o CSV automaticamente ao final
    pipeline_extracao_automatica()


def pipeline_chat():
    print("\n🤖 CHAT INICIADO (Digite 'sair' para encerrar)")
    engine = RAGEngine()
    retriever = engine.get_retriever()
    llm = LLMFactory.create_chat_model()
    verificador = VerificadorAlucinacao()

    # Chain personalizada com formatação de fonte
    rag_chain = (
            {
                "context": retriever | formatar_docs_com_fonte,
                "question": RunnablePassthrough()
            }
            | PROMPT_RAG_FINAL
            | llm
            | StrOutputParser()
    )

    while True:
        pergunta = input("\n👤 Pergunta: ")
        if pergunta.lower() in ['sair', 'exit']: break

        # 1. Recupera documentos para mostrar as fontes ao usuário
        docs = retriever.invoke(pergunta)

        print("\n🔍 Consultando as seguintes fontes:")
        fontes_usadas = set()
        for d in docs:
            nome = d.metadata.get('source', 'Desconhecido')
            pag = d.metadata.get('page', '?')
            print(f"   📄 {nome} (Pág. {pag})")
            fontes_usadas.add(nome)

        print("⏳ Gerando resposta...", end="\r")
        resposta = rag_chain.invoke(pergunta)

        print(f"\n🤖 ECLADATTA:\n{resposta}")

        # Validação Rápida
        if verificador.verificar_consistencia_numerica(resposta, str(docs)).get("tem_alucinacao"):
            print("⚠️ ALERTA: Verifique os números na fonte original.")


def main():
    print("--- SISTEMA MULTI-PDF ECLADATTA ---")
    print("1. Processar TODOS os PDFs (Gera CSV ao final)")
    print("2. Apenas Chat (Usa dados já processados)")

    opt = input("Opção: ")

    if opt == "1":
        pipeline_ingestao_completa()
        # Opcional: Entrar no chat direto após processar
        if input("\nIr para o chat? (s/n): ").lower() == 's':
            pipeline_chat()
    elif opt == "2":
        if not os.path.exists(VECTOR_DB_DIR):
            print("⚠️ Erro: Nenhum dado processado encontrado. Rode a opção 1 primeiro.")
        else:
            pipeline_chat()


if __name__ == "__main__":
    main()
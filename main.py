import sys
import os
import json
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Imports do Projeto
from src.config import RAW_DIR, VECTOR_DB_DIR
from src.ingestion.pdf_loader import processar_documento
from src.ingestion.table_summarizer import gerar_resumos_tabelas
from src.models.rag_engine import RAGEngine
from src.models.llm_factory import LLMFactory
from src.prompts.templates import PROMPT_RAG_FINAL, PROMPT_EXTRACAO
from src.evaluation.hallucination_check import VerificadorAlucinacao
from src.evaluation.saver import configurar_logger, salvar_relacoes_csv

# Inicializa o Logger Global
logger = configurar_logger()


def verificar_arquivo_entrada():
    """Verifica se existe PDF na pasta raw."""
    arquivos = list(RAW_DIR.glob("*.pdf"))
    if not arquivos:
        logger.error(f"Nenhum PDF encontrado em {RAW_DIR}")
        sys.exit(1)
    return arquivos[0].name


def pipeline_ingestao(nome_arquivo):
    logger.info(f"🚀 INICIANDO INGESTÃO: {nome_arquivo}")

    # 1. Extração
    logger.info("--- [Etapa 1.1] Extração Texto/Tabela ---")
    processar_documento(nome_arquivo)

    # 2. Resumo
    logger.info("--- [Etapa 1.2] Geração de Resumos ---")
    gerar_resumos_tabelas()

    # 3. Indexação
    logger.info("--- [Etapa 2.1] Indexação Vetorial ---")
    motor = RAGEngine()
    motor.indexar_dados()

    logger.info("✅ Ingestão concluída!")


def pipeline_chat():
    logger.info("🤖 SISTEMA ECLADATTA - INICIADO")

    # Carrega Motor
    motor = RAGEngine()
    retriever = motor.get_retriever()
    llm = LLMFactory.create_chat_model(temperature=0)
    verificador = VerificadorAlucinacao()

    # Cadeia de Chat (Conversa)
    rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | PROMPT_RAG_FINAL
            | llm
            | StrOutputParser()
    )

    # Cadeia de Extração (Para popular o CSV)
    # Usa o prompt específico 'extracao_relacoes' do seu YAML
    extraction_chain = (
            PROMPT_EXTRACAO
            | llm
            | StrOutputParser()
    )

    print("\n--- ECLADATTA PRONTO ---")
    print("Digite 'sair' para encerrar.")
    print("Digite 'extrair' para forçar a extração de relações do último contexto.")

    ultimo_contexto = ""

    while True:
        pergunta = input("\n👤 Você: ")
        if pergunta.lower() in ['sair', 'exit']:
            break

        # Opção manual para salvar no CSV (ou poderia ser automático)
        if pergunta.lower() == 'extrair':
            if not ultimo_contexto:
                print("⚠️ Faça uma pergunta primeiro para carregar o contexto.")
                continue

            print("⏳ Extraindo relações estruturadas para CSV...")
            try:
                # Chama o LLM pedindo JSON
                json_resultado = extraction_chain.invoke({
                    "texto_input": ultimo_contexto,
                    "tabela_input": "Verificar contexto acima"
                })
                # Salva no arquivo
                salvar_relacoes_csv(json_resultado, fonte="interacao_usuario")
            except Exception as e:
                logger.error(f"Erro na extração: {e}")
            continue

        # Fluxo Normal de Chat
        logger.info(f"Pergunta recebida: {pergunta}")
        print("⏳ Processando...", end="\r")

        # 1. Recupera Contexto
        docs = retriever.invoke(pergunta)
        contexto_str = "\n".join([d.page_content for d in docs])
        ultimo_contexto = contexto_str  # Guarda para uso na extração

        # 2. Gera Resposta
        resposta = rag_chain.invoke(pergunta)

        # 3. Valida Alucinação
        analise = verificador.verificar_consistencia_numerica(resposta, contexto_str)

        print(f"\n🤖 ECLADATTA: {resposta}")

        if analise.get("tem_alucinacao"):
            logger.warning(f"Alucinação detectada: {analise}")
            print(f"\n⚠️ ALERTA: Possível inconsistência numérica.")

        # Opcional: Extração Automática (Se quiser popular o CSV sempre)
        # salvar_relacoes_csv(extraction_chain.invoke({...}), fonte="auto")


def main():
    if not os.path.exists(VECTOR_DB_DIR):
        print("Banco de dados não encontrado. Iniciando ingestão...")
        arquivo = verificar_arquivo_entrada()
        pipeline_ingestao(arquivo)

    # Menu simples
    print("1. Re-processar documentos")
    print("2. Iniciar Chat")
    escolha = input("Opção: ").strip()

    if escolha == "1":
        arquivo = verificar_arquivo_entrada()
        pipeline_ingestao(arquivo)
        pipeline_chat()
    else:
        pipeline_chat()


if __name__ == "__main__":
    main()
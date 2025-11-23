import uuid
import json
from pathlib import Path
from typing import List, Any

# --- IMPORTS DO LANGCHAIN CORE (Esses funcionam sempre) ---
from langchain_chroma import Chroma
from langchain_core.stores import InMemoryByteStore
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore
from langchain_core.stores import BaseStore
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from pydantic import Field

# Imports Locais
from src.config import PROCESSED_DIR, DATA_DIR, EMBEDDING_PROVIDER
from src.models.embeddings import EmbeddingFactory


# --- CLASSE MANUAL PARA SUBSTITUIR O IMPORT QUEBRADO ---
class LocalMultiVectorRetriever(BaseRetriever):
    """
    Implementação local do MultiVectorRetriever para evitar erros de importação.
    Recupera vetores (resumos) e mapeia para documentos originais (tabelas/textos).
    """
    vectorstore: VectorStore
    byte_store: BaseStore
    id_key: str = "doc_id"
    search_type: str = "similarity"
    search_kwargs: dict = Field(default_factory=dict)

    def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        # 1. Busca os vetores (Resumos)
        sub_docs = self.vectorstore.search(query, self.search_type, **self.search_kwargs)

        # 2. Extrai os IDs dos documentos pais
        ids = []
        for d in sub_docs:
            if self.id_key in d.metadata:
                ids.append(d.metadata[self.id_key])

        # 3. Busca os documentos originais no ByteStore usando os IDs
        # O mget retorna uma lista de valores (ou None se não achar)
        docs = self.byte_store.mget(ids)

        # 4. Filtra Nones e retorna documentos reais
        return [d for d in docs if d is not None]


# --- MOTOR RAG ---
class RAGEngine:
    """
    Motor de Recuperação Aumentada (RAG) Híbrido.
    """

    def __init__(self, persist_dir: str = None):
        # 1. Configura Embeddings
        self.embedding_model = EmbeddingFactory.get_embedding_model(provider=EMBEDDING_PROVIDER)

        if persist_dir is None:
            persist_dir = str(DATA_DIR / "vector_db")

        # 2. Inicializa o Vector Store (ChromaDB)
        self.vectorstore = Chroma(
            collection_name="ecladatta_docs",
            embedding_function=self.embedding_model,
            persist_directory=persist_dir
        )

        # 3. Inicializa o DocStore (Memória)
        self.store = InMemoryByteStore()
        self.id_key = "doc_id"

        # 4. Configura o Retriever (Usando nossa classe local)
        self.retriever = LocalMultiVectorRetriever(
            vectorstore=self.vectorstore,
            byte_store=self.store,
            id_key=self.id_key,
        )

    def indexar_dados(self):
        """
        Lê JSONs e popula o banco de dados.
        """
        print("--- Iniciando Indexação Híbrida ---")

        # A. Indexar Textos
        path_textos = PROCESSED_DIR / "texts"
        textos_objs = []
        ids_textos = []

        if path_textos.exists():
            arquivos_texto = list(path_textos.glob("*.json"))
            for f in arquivos_texto:
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        conteudo = data.get('content') or ""
                        origem = data.get("source") or f.name

                        if conteudo.strip():
                            doc = Document(page_content=conteudo, metadata={"source": origem})
                            textos_objs.append(doc)
                            ids_textos.append(str(uuid.uuid4()))
                except Exception:
                    pass

            if textos_objs:
                docs_para_vetor = [
                    Document(page_content=t.page_content, metadata={self.id_key: ids_textos[i]})
                    for i, t in enumerate(textos_objs)
                ]
                self.vectorstore.add_documents(docs_para_vetor)
                self.store.mset(list(zip(ids_textos, textos_objs)))
                print(f"   [OK] {len(textos_objs)} blocos de texto indexados.")

        # B. Indexar Tabelas
        path_tabelas = PROCESSED_DIR / "tables"
        path_resumos = PROCESSED_DIR / "summaries"

        resumos_objs = []
        tabelas_reais = []
        ids_tabelas = []

        if path_tabelas.exists():
            arquivos_tabela = list(path_tabelas.glob("*.json"))
            for f_tab in arquivos_tabela:
                try:
                    with open(f_tab, 'r', encoding='utf-8') as file:
                        data_tab = json.load(file)

                    tabela_id = data_tab.get('id') or data_tab.get('id_tabela')
                    if not tabela_id: continue

                    f_resumo = path_resumos / f"summary_{tabela_id}.txt"

                    if f_resumo.exists():
                        with open(f_resumo, 'r', encoding='utf-8') as fr:
                            texto_resumo = fr.read()

                        doc_resumo = Document(page_content=texto_resumo, metadata={self.id_key: tabela_id})

                        conteudo_raw = data_tab.get('content') or data_tab.get('conteudo_html') or str(data_tab)
                        conteudo_real = f"DADOS TABULARES DO DOCUMENTO:\n{conteudo_raw}"

                        doc_tabela = Document(
                            page_content=conteudo_real,
                            metadata={"type": "tabela", "source": data_tab.get("source", "desc")}
                        )

                        resumos_objs.append(doc_resumo)
                        tabelas_reais.append(doc_tabela)
                        ids_tabelas.append(tabela_id)
                except Exception:
                    pass

            if resumos_objs:
                self.vectorstore.add_documents(resumos_objs)
                self.store.mset(list(zip(ids_tabelas, tabelas_reais)))
                print(f"   [OK] {len(resumos_objs)} tabelas indexadas.")

    def get_retriever(self):
        return self.retriever
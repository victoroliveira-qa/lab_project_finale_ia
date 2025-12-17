import json
import shutil
from pathlib import Path
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter  # <--- NOVO IMPORT
from src.config import VECTOR_DB_DIR, PROCESSED_DIR


class RAGEngine:
    def __init__(self):
        self.embedding_model = OllamaEmbeddings(model="nomic-embed-text")
        self.vector_store = None

        # Configura o "Fatiador" de texto
        # chunk_size=1000: Tamanho seguro para o modelo nomic
        # chunk_overlap=200: Mantém um pouco do contexto anterior para não cortar frases no meio
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    def carregar_json_recursivo(self, pattern):
        """Busca arquivos JSON em todas as subpastas."""
        docs = []
        arquivos = list(PROCESSED_DIR.rglob(pattern))

        for arq in arquivos:
            try:
                with open(arq, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'content' in data and data['content'].strip():
                        doc = Document(
                            page_content=data['content'],
                            metadata={
                                "source": data.get("source", "desconhecido"),
                                "page": data.get("page_number", 0),
                                "type": data.get("type", "unknown")
                            }
                        )
                        docs.append(doc)
            except Exception as e:
                print(f"Erro ao ler {arq}: {e}")
        return docs

    def indexar_dados(self):
        """Lê textos e resumos, fatia e indexa no ChromaDB."""
        if VECTOR_DB_DIR.exists():
            shutil.rmtree(VECTOR_DB_DIR)

        print("🗄️ Carregando documentos para indexação...")

        docs_texto = self.carregar_json_recursivo("**/texts/*.json")
        docs_tabelas = self.carregar_json_recursivo("**/summaries/*.json")
        todos_docs = docs_texto + docs_tabelas

        if not todos_docs:
            print("⚠️ Nenhum documento encontrado. Verifique 'data/processed'.")
            return

        # --- CORREÇÃO DO ERRO ---
        # Antes de indexar, fatiamos os documentos grandes em pedaços menores
        print(f"✂️ Fatiando {len(todos_docs)} documentos originais...")
        docs_fatiados = self.text_splitter.split_documents(todos_docs)
        print(f"🧩 Indexando {len(docs_fatiados)} chunks (pedaços) no ChromaDB...")

        self.vector_store = Chroma.from_documents(
            documents=docs_fatiados,  # Agora passamos os docs fatiados
            embedding=self.embedding_model,
            persist_directory=str(VECTOR_DB_DIR)
        )
        print("✅ Indexação concluída!")

    def get_retriever(self):
        if not self.vector_store:
            if not VECTOR_DB_DIR.exists():
                print("⚠️ Banco vetorial não encontrado.")
                return None

            self.vector_store = Chroma(
                persist_directory=str(VECTOR_DB_DIR),
                embedding_function=self.embedding_model
            )
        return self.vector_store.as_retriever(search_kwargs={"k": 5})
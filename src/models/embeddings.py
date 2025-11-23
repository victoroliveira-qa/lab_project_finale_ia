from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

# Importa configurações do src/config.py
from src.config import (
    OLLAMA_BASE_URL,
    OPENAI_API_KEY,
    EMBEDDING_PROVIDER,
    EMBEDDING_MODEL_NAME
)


class EmbeddingFactory:
    """
    Fábrica para criar modelos de representação vetorial (Embeddings).
    Suporta:
    1. 'ollama': Execução local (Recomendado: nomic-embed-text).
    2. 'openai': Execução via API (text-embedding-3-small).
    3. 'huggingface': Execução local via CPU/GPU sem servidor (sentence-transformers).

    [cite_start]Referência: Etapa 2 - Processamento e Modelagem[cite: 31].
    """

    @staticmethod
    def get_embedding_model(provider: Optional[str] = None) -> Embeddings:
        """
        Retorna a instância do modelo de embedding configurado.

        Args:
            provider (str, optional): Sobrescreve o provedor definido no config.
                                      Opções: 'ollama', 'openai', 'huggingface'.
        """
        # Se nenhum provedor for passado, usa o do config.py
        target_provider = provider or EMBEDDING_PROVIDER
        target_provider = target_provider.lower()

        print(f"🔌 Inicializando Embeddings Provider: {target_provider.upper()}...")

        # --- OPÇÃO 1: OLLAMA (Local Server) ---
        if target_provider == "ollama":
            # O modelo ideal para embeddings no Ollama é o 'nomic-embed-text'
            # Llama3 puro não é bom para embeddings, apenas para chat.
            return OllamaEmbeddings(
                model=EMBEDDING_MODEL_NAME,  # Ex: nomic-embed-text
                base_url=OLLAMA_BASE_URL  # Ex: http://localhost:11434
            )

        # --- OPÇÃO 2: OPENAI (API) ---
        elif target_provider == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("❌ Erro: API Key da OpenAI não encontrada no .env")

            return OpenAIEmbeddings(
                model=EMBEDDING_MODEL_NAME,  # Ex: text-embedding-3-small
                api_key=OPENAI_API_KEY
            )

        # --- OPÇÃO 3: HUGGINGFACE (Local Libraries) ---
        elif target_provider == "huggingface":
            print("   Carregando modelo Sentence-Transformers (pode demorar na 1ª vez)...")
            # Modelo multilíngue excelente e leve
            model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            return HuggingFaceEmbeddings(model_name=model_name)

        else:
            raise ValueError(f"Provedor '{target_provider}' desconhecido. Use: ollama, openai ou huggingface.")
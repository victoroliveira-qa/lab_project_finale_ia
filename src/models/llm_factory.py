from langchain_ollama import ChatOllama
from src.config import MODEL_NAME, OLLAMA_BASE_URL

class LLMFactory:
    """
    Fábrica de LLMs adaptada para Ollama (Local).
    """

    @staticmethod
    def create_chat_model(temperature: float = 0):
        """
        Cria uma instância do Llama 3 rodando localmente.
        """
        return ChatOllama(
            model=MODEL_NAME,
            temperature=temperature,
            base_url=OLLAMA_BASE_URL,
            # num_predict=-1, # Opcional: define tokens máximos
            # keep_alive="1h" # Opcional: mantém o modelo na RAM para ser rápido
        )
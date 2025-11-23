import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- DIRETÓRIOS (Mantém igual) ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
TEXTS_DIR = PROCESSED_DIR / "texts"
TABLES_DIR = PROCESSED_DIR / "tables"
SUMMARIES_DIR = PROCESSED_DIR / "summaries"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

for path in [RAW_DIR, TEXTS_DIR, TABLES_DIR, SUMMARIES_DIR, VECTOR_DB_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# --- CONFIGURAÇÃO DE MODELOS (ATUALIZADO PARA OLLAMA) ---

# Escolha o provedor aqui: 'ollama' ou 'openai'
LLM_PROVIDER = "ollama"
EMBEDDING_PROVIDER = "ollama"

# Configurações do OLLAMA (Local)
OLLAMA_BASE_URL = "http://localhost:11434"
# Para chat/raciocínio (extração de JSON e resumo)
MODEL_NAME = "llama3"
# Para vetorização (busca no banco de dados)
# IMPORTANTE: Rode 'ollama pull nomic-embed-text' no terminal antes
EMBEDDING_MODEL_NAME = "nomic-embed-text"

# Configurações da OpenAI (Caso precise voltar)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
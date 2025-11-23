# Arquivo: src/prompts/templates.py
import yaml
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# Caminho para o arquivo YAML
CURRENT_DIR = Path(__file__).parent
YAML_PATH = CURRENT_DIR / "system_prompts.yaml"


def load_prompts_from_yaml():
    """
    Carrega os prompts brutos do arquivo YAML.
    Isso facilita a edição dos prompts sem tocar no código Python.
    """
    if not YAML_PATH.exists():
        raise FileNotFoundError(f"Arquivo de prompts não encontrado em: {YAML_PATH}")

    with open(YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Carrega os dicionários uma única vez ao importar o módulo
_prompts_data = load_prompts_from_yaml()


# --- FÁBRICA DE TEMPLATES ---

def get_resumo_tabela_prompt() -> ChatPromptTemplate:
    """Retorna o template para resumir tabelas (Ingestão)."""
    p_data = _prompts_data['resumo_tabela']
    return ChatPromptTemplate.from_messages([
        ("system", p_data['system']),
        ("human", p_data['user'])
    ])


def get_rag_qa_prompt() -> ChatPromptTemplate:
    """Retorna o template para a resposta final ao usuário (RAG)."""
    p_data = _prompts_data['rag_qa_final']
    return ChatPromptTemplate.from_messages([
        ("system", p_data['system']),
        ("human", p_data['user'])
    ])


def get_extracao_relacoes_prompt() -> ChatPromptTemplate:
    """Retorna o template para extração estruturada (JSON)."""
    p_data = _prompts_data['extracao_relacoes']
    return ChatPromptTemplate.from_messages([
        ("system", p_data['system']),
        ("human", p_data['user'])
    ])


# Instâncias prontas para importação direta
PROMPT_RESUMO = get_resumo_tabela_prompt()
PROMPT_RAG_FINAL = get_rag_qa_prompt()
PROMPT_EXTRACAO = get_extracao_relacoes_prompt()
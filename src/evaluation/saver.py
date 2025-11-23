import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Union

# Define o caminho do arquivo de saída
from src.config import DATA_DIR

OUTPUTS_DIR = DATA_DIR.parent / "outputs"
RELATIONS_FILE = OUTPUTS_DIR / "relations_extracted.csv"
LOGS_DIR = OUTPUTS_DIR / "logs"

# Garante que as pastas existam
RELATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def configurar_logger():
    """Configura o log para escrever tanto no arquivo quanto no console."""
    log_filename = LOGS_DIR / f"execution_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # Mantém o print no console
        ]
    )
    return logging.getLogger("ECLADATTA")


def salvar_relacoes_csv(relacoes: Union[str, List[Dict]], fonte: str):
    """
    Salva as relações extraídas no arquivo relations_extracted.csv.
    Recebe uma lista de dicionários ou uma string JSON.
    """
    logger = logging.getLogger("ECLADATTA")

    # 1. Tenta converter string JSON para lista de dicts
    dados_para_salvar = []
    if isinstance(relacoes, str):
        try:
            # Limpa blocos de código markdown se o LLM mandar ```json ... ```
            relacoes_limpo = relacoes.replace("```json", "").replace("```", "").strip()
            dados_para_salvar = json.loads(relacoes_limpo)
        except json.JSONDecodeError as e:
            logger.error(f"Falha ao decodificar JSON para salvar no CSV: {e}")
            return
    elif isinstance(relacoes, list):
        dados_para_salvar = relacoes
    else:
        return

    # Se o JSON for um único dict, transforma em lista
    if isinstance(dados_para_salvar, dict):
        dados_para_salvar = [dados_para_salvar]

    # 2. Escreve no CSV
    arquivo_existe = RELATIONS_FILE.exists()

    with open(RELATIONS_FILE, mode='a', newline='', encoding='utf-8') as f:
        # Define as colunas esperadas (Baseado no seu Prompt de Extração)
        fieldnames = ["entidade_origem", "relacao", "entidade_destino", "valor", "fonte", "data_extracao"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not arquivo_existe:
            writer.writeheader()

        count = 0
        for item in dados_para_salvar:
            # Adiciona metadados extras
            item['fonte'] = fonte
            item['data_extracao'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Filtra apenas chaves que existem no fieldnames para evitar erro
            row = {k: item.get(k, "") for k in fieldnames}
            writer.writerow(row)
            count += 1

    logger.info(f"💾 {count} novas relações salvas em {RELATIONS_FILE}")
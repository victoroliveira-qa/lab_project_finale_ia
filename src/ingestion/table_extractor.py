import camelot
import json
import pandas as pd
from pathlib import Path


def extrair_tabelas_camelot(caminho_pdf, diretorio_saida):
    """
    Extrai tabelas usando Camelot e salva cada uma como JSON.
    Tenta método 'lattice' (com bordas) e 'stream' (sem bordas).
    """
    caminho_pdf = str(caminho_pdf)
    diretorio_saida = Path(diretorio_saida)

    todas_tabelas = []

    try:
        # 1. Tentativa Lattice (Tabelas com linhas de grade)
        # print(f"      ...Tentando método Lattice em {Path(caminho_pdf).name}")
        tabelas_lattice = camelot.read_pdf(caminho_pdf, pages='all', flavor='lattice')
        for t in tabelas_lattice:
            todas_tabelas.append(t)

        # 2. Tentativa Stream (Se Lattice falhar ou para tabelas sem bordas)
        if len(todas_tabelas) == 0:
            # print("      ...Lattice vazio. Tentando método Stream")
            tabelas_stream = camelot.read_pdf(caminho_pdf, pages='all', flavor='stream', edge_tol=500)
            for t in tabelas_stream:
                todas_tabelas.append(t)

        if not todas_tabelas:
            return

        # 3. Processar e Salvar
        for i, tabela in enumerate(todas_tabelas):
            df = tabela.df

            # Limpeza básica: remove linhas totalmente vazias
            df = df.dropna(how='all').fillna("")

            # Ignora tabelas minúsculas (ruído)
            if df.shape[0] < 2:
                continue

            # Converte para HTML (preserva estrutura para o LLM)
            html_content = df.to_html(index=False, border=1)

            # Estrutura do JSON
            dados_tabela = {
                "content": html_content,
                "type": "table",
                "source": Path(caminho_pdf).name,
                "page_number": tabela.page,
                "method": tabela.flavor
            }

            # Salva o arquivo
            nome_arquivo = diretorio_saida / f"table_pg{tabela.page}_{i + 1}.json"
            with open(nome_arquivo, "w", encoding="utf-8") as f:
                json.dump(dados_tabela, f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"      ❌ Erro ao extrair tabelas: {e}")
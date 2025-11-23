import camelot
import pandas as pd
from pathlib import Path
from typing import List, Dict, Union


class TableExtractor:
    """
    Especialista em extrair tabelas de PDFs mantendo a estrutura.
    Utiliza Camelot conforme metodologia.
    """

    @staticmethod
    def extrair_com_camelot(caminho_pdf: Union[str, Path], paginas: str = "all") -> List[Dict]:
        """
        Usa a biblioteca Camelot para extrair tabelas (Requer Ghostscript instalado).
        Modo 'lattice' é ideal para tabelas com bordas definidas (comuns em balanços).
        """
        print(f"   Extratindo tabelas de {caminho_pdf} com Camelot...")
        dados_extraidos = []

        try:
            # Tenta extrair usando o modo lattice (linhas)
            tabelas = camelot.read_pdf(str(caminho_pdf), pages=paginas, flavor='lattice')

            # Se não achar nada, tenta o modo stream (espaçamento em branco)
            if len(tabelas) == 0:
                tabelas = camelot.read_pdf(str(caminho_pdf), pages=paginas, flavor='stream')

            for i, tabela in enumerate(tabelas):
                df = tabela.df

                # Limpeza básica do DataFrame
                df = df.replace(r'\n', ' ', regex=True)  # Remove quebras dentro da célula

                dados_extraidos.append({
                    "id_tabela": f"tab_{tabela.page}_{i}",
                    "pagina": tabela.page,
                    "conteudo_html": df.to_html(index=False, header=False),  # HTML é melhor para LLMs lerem
                    "conteudo_csv": df.to_csv(index=False, header=False),
                    "metodo": "camelot"
                })

        except Exception as e:
            print(f"   Erro no Camelot (pode ser falta do Ghostscript): {e}")
            print("   Tentando fallback...")
            return []

        return dados_extraidos

    @staticmethod
    def salvar_tabela(dados_tabela: Dict, diretorio_saida: Path):
        """Salva a tabela processada em arquivo JSON."""
        import json

        nome_arquivo = f"table_{dados_tabela['id_tabela']}.json"
        caminho_final = diretorio_saida / nome_arquivo

        with open(caminho_final, 'w', encoding='utf-8') as f:
            json.dump(dados_tabela, f, ensure_ascii=False, indent=4)
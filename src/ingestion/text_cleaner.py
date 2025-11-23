import re


class TextCleaner:
    """
    Responsável por higienizar o texto extraído de PDFs econômicos.
    Remove ruídos que podem confundir o LLM.
    """

    @staticmethod
    def limpar_texto_basico(texto: str) -> str:
        if not texto:
            return ""

        # 1. Unificar quebras de linha que separam frases indevidamente
        # Ex: "Eco-\nnomia" vira "Economia"
        texto = re.sub(r'(?<=[a-z])-\n(?=[a-z])', '', texto)

        # 2. Remover quebras de linha excessivas (transformar parágrafo em linha única)
        texto = texto.replace('\n', ' ')

        # 3. Remover múltiplos espaços em branco
        texto = re.sub(r'\s+', ' ', texto)

        return texto.strip()

    @staticmethod
    def remover_cabecalhos_rodape(texto: str) -> str:
        """
        Remove padrões comuns de relatórios do BCB.
        Ex: 'Relatório de Estabilidade Financeira' repetido em todas as páginas.
        """
        padroes_para_remover = [
            r"Relatório de Estabilidade Financeira",
            r"Banco Central do Brasil",
            r"^\d+\s*$",  # Números de página isolados
            r"Page \d+ of \d+"
        ]

        for padrao in padroes_para_remover:
            texto = re.sub(padrao, '', texto, flags=re.IGNORECASE)

        return texto.strip()

    @classmethod
    def processar(cls, texto: str) -> str:
        """Pipeline completo de limpeza."""
        texto = cls.remover_cabecalhos_rodape(texto)
        texto = cls.limpar_texto_basico(texto)
        return texto
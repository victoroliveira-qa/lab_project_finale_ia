import re


def limpar_texto(texto: str) -> str:
    """
    Higieniza o texto extraído de PDFs removendo cabeçalhos, rodapés e ruídos.
    """
    if not texto:
        return ""

    # 1. Remover padrões comuns de cabeçalho/rodapé do BCB
    padroes_para_remover = [
        r"Relatório de Estabilidade Financeira",
        r"Banco Central do Brasil",
        r"Page \d+ of \d+",
        r"^\d+\s*$"  # Números de página isolados em uma linha
    ]

    for padrao in padroes_para_remover:
        texto = re.sub(padrao, '', texto, flags=re.IGNORECASE | re.MULTILINE)

    # 2. Unificar quebras de linha de hifenização (Ex: "Eco-\nnomia" -> "Economia")
    texto = re.sub(r'(?<=[a-z])-\n(?=[a-z])', '', texto)

    # 3. Remover quebras de linha excessivas (transformar parágrafo em linha única)
    texto = texto.replace('\n', ' ')

    # 4. Remover múltiplos espaços em branco gerados pelas remoções acima
    texto_limpo = re.sub(r'\s+', ' ', texto).strip()

    return texto_limpo
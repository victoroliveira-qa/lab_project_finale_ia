# Arquivo: src/evaluation/metrics.py
from typing import List, Set, Dict


class CalculadoraMetricas:
    """
    Calcula métricas de desempenho para a extração de relações Texto-Tabela.
    Compara o JSON extraído pelo modelo com o JSON anotado manualmente (Gold Standard).
    Referência: Validação e análise dos resultados[cite: 35].
    """

    @staticmethod
    def calcular_precision_recall_f1(predito: List[Dict], real: List[Dict]) -> Dict[str, float]:
        """
        Calcula Precisão, Revocação (Recall) e F1-Score.
        Considera uma extração correta se a tripla (Entidade, Relação, Valor) coincidir.
        """

        # Normaliza para conjuntos de strings para facilitar comparação
        # Ex: "Inadimplência|cresceu|3.5%"
        set_predito = CalculadoraMetricas._converter_para_set(predito)
        set_real = CalculadoraMetricas._converter_para_set(real)

        # Verdadeiros Positivos (O que o modelo acertou)
        true_positives = len(set_predito.intersection(set_real))

        # Total Predito (Para precisão)
        total_predito = len(set_predito)

        # Total Real (Para recall)
        total_real = len(set_real)

        # 1. Precision: De tudo que o modelo extraiu, quanto estava certo?
        precision = true_positives / total_predito if total_predito > 0 else 0.0

        # 2. Recall: De tudo que era para extrair, quanto o modelo pegou?
        recall = true_positives / total_real if total_real > 0 else 0.0

        # 3. F1-Score: Média harmônica
        if (precision + recall) > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0.0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "acertos": true_positives,
            "total_esperado": total_real
        }

    @staticmethod
    def _converter_para_set(lista_relacoes: List[Dict]) -> Set[str]:
        """
        Converte lista de dicionários em conjunto de strings únicas para comparação.
        Normaliza texto para minúsculo para evitar erros bobos.
        """
        output_set = set()
        for item in lista_relacoes:
            # Cria uma "assinatura" da relação.
            # Ex: item = {'entidade': 'PIB', 'valor': '2%'} -> "pib|2%"

            entidade = str(item.get('entidade_origem', '')).lower().strip()
            valor = str(item.get('valor', '')).lower().strip()

            # Focamos na entidade e valor, pois a "relação" (verbo) pode variar semanticamente
            assinatura = f"{entidade}|{valor}"
            if entidade and valor:
                output_set.add(assinatura)

        return output_set
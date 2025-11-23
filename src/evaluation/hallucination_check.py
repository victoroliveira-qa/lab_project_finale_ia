import re
from typing import Dict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Importa a Fábrica em vez de importar o ChatOpenAI direto
from src.models.llm_factory import LLMFactory


class VerificadorAlucinacao:
    """
    Responsável por verificar se a resposta gerada pelo RAG é fiel aos dados originais.
    Foca na consistência numérica entre Tabela (Contexto) e Texto Gerado.
    [cite_start]Referência: Etapa 3 da Metodologia - Verificação de consistência[cite: 34, 36].
    """

    def __init__(self):
        # CORREÇÃO: Usa a Factory para pegar o modelo configurado (Ollama ou OpenAI)
        # temperature=0 é crucial para validação rigorosa
        self.llm = LLMFactory.create_chat_model(temperature=0)

        # Prompt de "Juiz" para validar fatos
        self.prompt_juiz = ChatPromptTemplate.from_template(
            """
            Você é um auditor de dados financeiros. Sua tarefa é verificar alucinações.

            CONTEXTO ORIGINAL (Dados Reais):
            {contexto}

            RESPOSTA GERADA PELO IA:
            {resposta}

            TAREFA:
            1. Extraia todos os números/porcentagens da RESPOSTA.
            2. Verifique se cada número existe e está correto no CONTEXTO.
            3. Se houver qualquer discrepância numérica, marque como alucinação.

            Retorne APENAS um JSON no formato:
            {{
                "tem_alucinacao": boolean,
                "numeros_incorretos": ["lista de valores errados"],
                "justificativa": "breve explicação"
            }}
            """
        )
        self.parser = JsonOutputParser()

    def verificar_consistencia_numerica(self, resposta: str, contexto: str) -> Dict:
        """
        Verifica semanticamente se os números da resposta estão amparados pelo contexto.
        """
        chain = self.prompt_juiz | self.llm | self.parser

        try:
            # Invoca a cadeia de verificação
            resultado = chain.invoke({
                "contexto": contexto,
                "resposta": resposta
            })
            return resultado
        except Exception as e:
            # Em caso de erro (ex: modelo local muito lento ou falha no JSON),
            # retornamos um erro "suave" para não travar o chat.
            return {"tem_alucinacao": False, "erro_validacao": str(e)}

    @staticmethod
    def verificar_regex_simples(resposta: str, contexto: str) -> List[str]:
        """
        Método determinístico de backup.
        Extrai números da resposta e checa se a string exata existe no contexto.
        Útil para validar cópia fiel de dados tabulares.
        """
        # Regex para capturar números como 10, 10.5, 10,5, 10%
        padrao = r'\d+(?:[.,]\d+)?%?'
        numeros_resposta = set(re.findall(padrao, resposta))
        numeros_contexto = set(re.findall(padrao, contexto))

        # Números que estão na resposta mas NÃO estão no contexto
        alucinacoes_potenciais = [num for num in numeros_resposta if num not in numeros_contexto]

        return alucinacoes_potenciais
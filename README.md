# IA: Extração de Relações em Documentos Econômicos Híbridos

> **Projeto de Mestrado** - Investigação de métodos de extração conjunta de relações entre texto e tabelas apoiados por LLMs.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-v0.2-green)
![Ollama](https://img.shields.io/badge/Model-Llama3-orange)

## 📋 Sobre o Projeto

[cite_start]O **ECLADATTA** é uma arquitetura de *Retrieval-Augmented Generation* (RAG) desenhada para processar documentos econômicos complexos, como o **Relatório de Estabilidade Financeira (REF)** do Banco Central do Brasil[cite: 1, 6].

O campo econômico apresenta documentos que combinam narrativas textuais e dados tabulares. [cite_start]Ferramentas tradicionais frequentemente falham em interpretar essas tabelas, resultando em "alucinações" numéricas[cite: 7].

Este projeto propõe uma abordagem híbrida que:
1.  [cite_start]**Separa Modalidades:** Processa texto e tabela independentemente para preservar a integridade[cite: 19].
2.  **RAG Semântico-Estrutural:** Utiliza resumos gerados por IA para buscar tabelas, mas entrega os dados brutos (HTML/Markdown) para o modelo responder.
3.  [cite_start]**Validação Automática:** Implementa verificação de alucinações numéricas em tempo real.

---

## 📂 Estrutura de Pastas

[cite_start]A organização do código reflete rigorosamente as três etapas da metodologia proposta na pesquisa:

```plaintext
ECLADATTA_Mestrado/
│
├── data/                          # Armazenamento de dados (Corpus do projeto)
│   ├── raw/                       # [Input] PDFs originais (ex: REF do BCB) 
│   ├── processed/                 # [Etapa 1] Dados limpos e separados (JSON)
│   │   ├── texts/                 # Fragmentos de texto narrativo
│   │   ├── tables/                # Tabelas estruturadas (HTML/Markdown)
│   │   └── summaries/             # Resumos semânticos das tabelas (Gerado por LLM)
│   ├── vector_db/                 # [Etapa 2] Banco Vetorial Persistente (ChromaDB)
│   └── gold_standard/             # [Validação] Dados anotados manualmente para métricas [cite: 37]
│
├── src/                           # Código Fonte (Pipeline)
│   ├── ingestion/                 # [Etapa 1] Módulo de Análise e Preparação [cite: 26]
│   │   ├── pdf_loader.py          # Orquestrador de leitura de PDF
│   │   ├── table_extractor.py     # Extração estrutural (Camelot/Unstructured)
│   │   ├── table_summarizer.py    # Geração de resumos semânticos (Metadata)
│   │   └── text_cleaner.py        # Limpeza de cabeçalhos e ruídos
│   │
│   ├── models/                    # [Etapa 2] Processamento e Modelagem [cite: 30]
│   │   ├── embeddings.py          # Factory de Vetores (Suporta Ollama/OpenAI) [cite: 31]
│   │   ├── llm_factory.py         # Inicialização do LLM (Llama 3 Local)
│   │   └── rag_engine.py          # Motor RAG Híbrido (Multi-Vector Retriever)
│   │
│   ├── prompts/                   # Engenharia de Prompt (Prompt Learning) [cite: 32]
│   │   ├── templates.py           # Carregador de templates Python
│   │   └── system_prompts.yaml    # Definição de personas e instruções JSON
│   │
│   └── evaluation/                # [Etapa 3] Validação e Resultados [cite: 34]
│       ├── hallucination_check.py # Auditoria de consistência numérica (LLM-as-a-Judge)
│       ├── metrics.py             # Cálculo de Precision/Recall
│       └── saver.py               # Persistência de logs e CSV final
│
├── outputs/                       # Resultados Finais
│   ├── logs/                      # Histórico de execução e erros
│   └── relations_extracted.csv    # Corpus final de relações extraídas
│
├── .env                           # Configurações de ambiente
├── main.py                        # Orquestrador Principal (CLI)
├── requirements.txt               # Dependências do Python
└── setup_project.py               # Script de automação de ambiente

## 📋 Sobre o Projeto

[cite_start]O **ECLADATTA** é uma arquitetura de *Retrieval-Augmented Generation* (RAG) desenhada para processar documentos econômicos complexos, como o **Relatório de Estabilidade Financeira (REF)** do Banco Central do Brasil.

O campo econômico apresenta documentos que combinam narrativas textuais e dados tabulares. [cite_start]Ferramentas tradicionais frequentemente falham em interpretar essas tabelas, resultando em "alucinações" numéricas[cite: 6, 7].

Este projeto propõe uma abordagem híbrida que:
1.  [cite_start]**Separa Modalidades:** Processa texto e tabela independentemente para preservar a integridade[cite: 19].
2.  **RAG Semântico-Estrutural:** Utiliza resumos gerados por IA para buscar tabelas, mas entrega os dados brutos (HTML/Markdown) para o modelo responder.
3.  [cite_start]**Validação Automática:** Implementa verificação de alucinações numéricas em tempo real[cite: 36].

---

## 🏗️ Arquitetura do Pipeline

[cite_start]O sistema segue a metodologia dividida em três etapas[cite: 25]:

1.  **Ingestão e Análise:**
    * Separação via `Unstructured` e `Camelot`.
    * Geração de resumos semânticos das tabelas (Metadata Enrichment).
2.  **Processamento e Modelagem:**
    * **Multi-Vector Retriever:** Vetorização dos resumos (busca) vs. Armazenamento das tabelas originais (recuperação).
    * LLM Local: **Llama 3** (via Ollama).
    * Embeddings: **Nomic-Embed-Text**.
3.  **Validação e Extração:**
    * Chat interativo com verificação de consistência (`Hallucination Checker`).
    * [cite_start]Extração em lote (Batch) para construção de corpus (`relations_extracted.csv`)[cite: 22].

---

## ⚙️ Pré-requisitos do Sistema

Como o projeto lida com processamento pesado de PDF e IA Local, você precisará instalar:

### 1. Ferramentas de Sistema (Obrigatório para PDF)
* **Ghostscript** (Para o Camelot ler tabelas):
    * [Download para Windows](https://ghostscript.com/releases/gsdnld.html)
    * Linux: `sudo apt-get install ghostscript`
* **Poppler** (Para o Unstructured processar imagens):
    * [Download para Windows](https://github.com/oschwartz10612/poppler-windows/releases) (Adicione a pasta `bin` ao PATH).

### 2. Ollama (LLM Local)
Este projeto roda 100% localmente para garantir privacidade dos dados.
1.  Baixe e instale o [Ollama](https://ollama.com/).
2.  No terminal, baixe os modelos necessários:
    ```bash
    ollama pull llama3
    ollama pull nomic-embed-text
    ```
---

## 🚀 Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/ecladatta-mestrado.git](https://github.com/seu-usuario/ecladatta-mestrado.git)
    cd ecladatta-mestrado
    ```
2.  **Crie um ambiente virtual (Recomendado):**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
    ```

3.  **Instale as dependências Python:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuração:**
    O projeto já vem configurado para usar o Ollama por padrão em `src/config.py`. Nenhuma chave de API é necessária, a menos que mude para OpenAI.

---

## 🖥️ Como Usar

Execute o orquestrador principal:

```bash
python main.py
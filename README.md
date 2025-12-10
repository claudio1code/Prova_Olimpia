# Prova_Olimpia# 📊 AI Equity Research Agent

Agente autônomo de análise financeira desenvolvido para automatizar a coleta de dados preliminares de empresas de capital aberto (Investment Banking).

## 🚀 Funcionalidades

O sistema utiliza uma arquitetura baseada em Grafos (LangGraph) para orquestrar um pipeline de pesquisa:
1.  **Researcher Node:** Coleta dados fundamentais e notícias recentes via Web Scraping (DuckDuckGo).
2.  **Market Analyst Node:** Consulta cotações em tempo real via Yahoo Finance API.
3.  **Editor Node:** Utiliza LLM (Google Gemini) para sintetizar os dados em um relatório executivo.

## 🛠️ Stack Tecnológico

-   **Orquestração:** LangChain & LangGraph
-   **LLM:** Google Gemini 2.0 Flash / 1.5 Flash
-   **Ferramentas:** DuckDuckGo Search, yFinance
-   **Linguagem:** Python 3.10+

## ⚙️ Como Executar

1.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure sua API Key (Google AI Studio):**
    ```bash
    export GEMINI_API_KEY="sua_chave_aqui"
    ```

3.  **Execute o Agente:**
    ```bash
    python main.py
    ```

---
*Projeto desenvolvido para o processo seletivo - Dezembro/2025*
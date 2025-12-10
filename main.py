# main.py - Versão com DuckDuckGo (sem precisar de Serper)
import os
from tools import StockPriceTool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool

# Imports do LangGraph
from langgraph.prebuilt import create_react_agent

# --- 1. Inicializar as Ferramentas ---
stock_tool = StockPriceTool()

# Usar DuckDuckGo em vez de Serper (não precisa de API key)
search = DuckDuckGoSearchRun()
google_search_tool = Tool(
    name="Web_Search",
    description="Pesquisa na web para obter: 1. Resumo da empresa. 2. Notícias recentes com links.",
    func=search.run
)

tools = [stock_tool, google_search_tool]

# --- 2. Inicializar o LLM ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.0)

# --- 3. Criar o Agente usando LangGraph ---
agent_executor = create_react_agent(llm, tools)

# --- 4. Execução ---
company_name_input = "Ambev"

query = f"""
Você é um analista de Investment Banking. Para a empresa "{company_name_input}", forneça:

1. RESUMO DA EMPRESA: Setor de atuação, breve histórico e principais produtos/serviços
2. NOTÍCIAS RECENTES: Busque 2-3 notícias recentes com título e link
3. VALOR DA AÇÃO: Consulte o preço atual ou mais recente da ação

Compile tudo em um relatório organizado e estruturado no formato:

=== RELATÓRIO DE ANÁLISE: {company_name_input.upper()} ===

📊 1. RESUMO DA EMPRESA
[Setor, histórico, produtos/serviços]

📰 2. NOTÍCIAS RECENTES
• [Título] - [Link]
• [Título] - [Link]
• [Título] - [Link]

💰 3. VALOR DA AÇÃO
[Ticker e preço atual]
"""

print(f"{'='*60}")
print(f"🔍 ANÁLISE DE EMPRESA - {company_name_input.upper()}")
print(f"{'='*60}\n")

try:
    messages = [{"role": "user", "content": query}]
    
    print("⏳ Coletando informações...\n")
    
    # Executa o agente
    result = agent_executor.invoke({"messages": messages})
    
    # Extrai a resposta final
    final_message = result["messages"][-1]
    
    print("\n" + "="*60)
    print("📋 RELATÓRIO FINAL")
    print("="*60)
    print(final_message.content)
    print("\n" + "="*60)
    
except Exception as e:
    print(f"❌ Erro na execução: {e}")
    import traceback
    traceback.print_exc()
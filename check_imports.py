# main_old.py - Para LangChain 0.1.x (após downgrade)
import os
from tools import StockPriceTool 
from langchain.agents import initialize_agent, AgentType
from langchain_community.tools import SerperAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool

# --- 1. Inicializar as Ferramentas ---
stock_tool = StockPriceTool()
search_wrapper = SerperAPIWrapper()
google_search_tool = Tool(
    name="Google_Search_Tool",
    description="Pesquisa na web para obter: 1. Resumo da empresa. 2. Notícias recentes com links.",
    func=search_wrapper.run
)
tools = [stock_tool, google_search_tool]

# --- 2. Inicializar o LLM ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.0)

# --- 3. Criar o Agente ---
agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=10
)

# --- 4. Execução ---
company_name_input = "Ambev" 
query = f"""
Você é um analista de Investment Banking. Para a empresa "{company_name_input}", forneça:

1. RESUMO DA EMPRESA: Setor de atuação, breve histórico e principais produtos/serviços
2. NOTÍCIAS RECENTES: Busque 2-3 notícias recentes com título e link
3. VALOR DA AÇÃO: Consulte o preço atual ou mais recente da ação

Compile tudo em um relatório organizado.
"""

print(f"{'='*60}")
print(f"ANÁLISE DE EMPRESA - {company_name_input.upper()}")
print(f"{'='*60}\n")

try:
    response = agent_executor.invoke({"input": query})
    print("\n" + "="*60)
    print("RELATÓRIO FINAL")
    print("="*60)
    print(response['output'])
    print("\n" + "="*60)
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
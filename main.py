# main.py
import os
from tools import StockPriceTool 

# --- Importações Corrigidas e Robustas ---
# Tenta importar AgentExecutor do local novo, se falhar, tenta o antigo
try:
    from langchain.agents import AgentExecutor
except ImportError:
    from langchain.agents.agent import AgentExecutor

# Tenta importar create_react_agent do local novo, se falhar, tenta o antigo
try:
    from langchain.agents import create_react_agent
except ImportError:
    from langchain.agents.react.agent import create_react_agent

from langchain_community.tools import SerperAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate

# --- 1. Inicializar as Ferramentas ---
stock_tool = StockPriceTool()
search_wrapper = SerperAPIWrapper()
google_search_tool = Tool(
    name="Google_Search_Tool",
    description="Pesquisa na web para obter: 1. Resumo da empresa. 2. Notícias recentes.",
    func=search_wrapper.run
)
tools = [stock_tool, google_search_tool]

# --- 2. Inicializar o LLM ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)

# --- 3. Criar o Prompt (ReAct) ---
template = '''Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}'''

prompt = PromptTemplate.from_template(template)

# --- 4. Criar e Executar o Agente ---
agent = create_react_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True, 
    handle_parsing_errors=True,
    max_iterations=10
)

# --- 5. Execução ---
company_name_input = "Ambev" 
query = f"""
Analista de Investment Banking:
1. Resumo da empresa "{company_name_input}" (setor, histórico).
2. 2-3 Notícias recentes (título e link).
3. Valor ATUAL da ação.
Compile um relatório organizado.
"""

print(f"--- INICIANDO ANÁLISE PARA: {company_name_input} ---")
try:
    response = agent_executor.invoke({"input": query})
    print("\n--- RELATÓRIO FINAL ---")
    print(response['output'])
except Exception as e:
    print(f"Erro na execução: {e}")
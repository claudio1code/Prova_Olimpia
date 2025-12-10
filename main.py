# main.py - Versão LangGraph (LangChain 1.1+)
import os
from tools import StockPriceTool
from langchain_community.tools import SerperAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool

# Imports do LangGraph (novo sistema de agentes no LangChain 1.1+)
from langgraph.prebuilt import create_react_agent

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

# --- 3. Criar o Agente usando LangGraph ---
agent_executor = create_react_agent(llm, tools)

# --- 4. Execução ---
company_name_input = "Ambev"

# Sistema de mensagens para o agente
query = f"""
Você é um analista de Investment Banking. Para a empresa "{company_name_input}", forneça:

1. RESUMO DA EMPRESA: Setor de atuação, breve histórico e principais produtos/serviços
2. NOTÍCIAS RECENTES: Busque 2-3 notícias recentes com título e link
3. VALOR DA AÇÃO: Consulte o preço atual ou mais recente da ação

Compile tudo em um relatório organizado e estruturado no formato:

=== RELATÓRIO DE ANÁLISE ===
Empresa: [Nome]

1. RESUMO
[descrição completa]

2. NOTÍCIAS RECENTES
- [Título 1] - [Link]
- [Título 2] - [Link]
- [Título 3] - [Link]

3. PREÇO DA AÇÃO
[Valor atual com ticker]
"""

print(f"{'='*60}")
print(f"ANÁLISE DE EMPRESA - {company_name_input.upper()}")
print(f"{'='*60}\n")

try:
    # LangGraph usa um formato diferente de input
    messages = [{"role": "user", "content": query}]
    
    print("🔍 Iniciando pesquisa automatizada...\n")
    
    # Executa o agente
    result = agent_executor.invoke({"messages": messages})
    
    # Extrai a resposta final
    final_message = result["messages"][-1]
    
    print("\n" + "="*60)
    print("RELATÓRIO FINAL")
    print("="*60)
    print(final_message.content)
    print("\n" + "="*60)
    
except Exception as e:
    print(f"❌ Erro na execução: {e}")
    import traceback
    traceback.print_exc()
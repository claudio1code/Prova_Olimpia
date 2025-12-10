# main.py
import os
# Importa a sua Custom Tool que está no arquivo tools.py
from tools import StockPriceTool 

# Importa o Agent e o AgentType da comunidade, corrigindo os erros de versão.
from langchain_community.agents import initialize_agent, AgentType 
from langchain_google_genai import ChatGoogleGenerativeAI
# Usaremos a SerperAPIWrapper por ser mais rápida e fácil de configurar que a GoogleSearchAPIWrapper
from langchain_community.tools import SerperAPIWrapper 
from langchain.tools import Tool

# --- CONFIGURAÇÃO ---
# O LangChain vai buscar a chave de API automaticamente na variável de ambiente:
# export GEMINI_API_KEY="..."
# Para a busca, você precisa definir a chave da Serper API:
# export SERPER_API_KEY="..."


# --- 1. Inicializar as Ferramentas ---

# A. Ferramenta para Cotação (Custom Tool)
stock_tool = StockPriceTool()

# B. Ferramenta para Busca na Web (Resumo e Notícias)
# A SerperAPIWrapper é usada para coletar Resumo e Notícias.
search_wrapper = SerperAPIWrapper()
google_search_tool = Tool(
    name="Google_Search_Tool",
    description=(
        "Use esta ferramenta para pesquisar na web. É essencial para obter: "
        "1. Resumo/descrição da empresa (setor, histórico). "
        "2. Notícias recentes (título e link)."
    ),
    func=search_wrapper.run
)

# Lista de todas as ferramentas disponíveis para o Agent
tools = [stock_tool, google_search_tool]


# --- 2. Inicializar o LLM (Gemini) ---
# O 'gemini-2.5-flash' é rápido e excelente para este tipo de raciocínio.
# A chave GEMINI_API_KEY é lida automaticamente do ambiente.
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0) 


# --- 3. Inicializar o Agent (O Orquestrador) ---
# Usamos o AgentType.ZERO_SHOT_REACT_DESCRIPTION, que decide qual tool usar com base na descrição
agent = initialize_agent(
    tools, 
    llm, 
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
    verbose=True, # IMPORTANTE: Mostra o raciocínio do Agent (Ótimo para o print de terminal!)
    handle_parsing_errors=True,
    max_iterations=10
)


# --- 4. O Prompt de Execução (O Desafio) ---

# Este prompt direciona o Agent para usar as ferramentas na ordem correta e formatar a saída.
company_name_input = "Ambev" # Exemplo: Altere o nome aqui

query_template = f"""
Comporte-se como um analista de Investment Banking. Sua tarefa é compilar um relatório rápido e organizado para a empresa "{company_name_input}", realizando OBRIGATORIAMENTE as seguintes etapas:

1. Use a ferramenta de busca para obter um resumo/descrição detalhada da empresa (setor, breve histórico, produtos/serviços).
2. Use a ferramenta de busca para coletar 2 ou 3 notícias RECENTES sobre a empresa, incluindo o título da notícia e, se possível, o link (URL) da matéria original.
3. Use a ferramenta de cotação de ações para consultar o valor ATUAL da ação.

A saída final deve ser o relatório completo e organizado.
"""


# --- 5. Execução e Saída ---
print(f"\n=======================================================")
print(f"  EXECUTANDO ANÁLISE DO AGENT PARA: {company_name_input}")
print(f"=======================================================\n")

# A saída com verbose=True já garante o "print de terminal" com o processo
response = agent.invoke({"input": query_template})

print("\n=====================================================")
print(f"           ✅ RELATÓRIO FINAL: {company_name_input.upper()}")
print("=====================================================")
print(response['output'])
print("=====================================================")
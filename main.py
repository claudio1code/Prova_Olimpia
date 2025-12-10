# main.py
import os
import sys
import time
from typing import TypedDict
from langgraph.graph import StateGraph, END

# --- 1. CONFIGURAÇÃO E SEGURANÇA ---
if "GOOGLE_API_KEY" in os.environ: del os.environ["GOOGLE_API_KEY"]
if "GEMINI_API_KEY" not in os.environ:
    print("❌ ERRO CRÍTICO: Variável GEMINI_API_KEY não definida.")
    print("   Execute no terminal: export GEMINI_API_KEY='sua_chave_L9DE'")
    sys.exit(1)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    from duckduckgo_search import DDGS
    import yfinance as yf
except ImportError as e:
    print(f"❌ Dependência faltando: {e}")
    sys.exit(1)

# --- 2. DEFINIÇÃO DO ESTADO ---
class ResearchState(TypedDict):
    company_name: str
    summary_data: str
    news_data: str
    stock_data: str
    final_report: str

# --- 3. NÓS DO GRAFO (AGENTS) ---

def node_researcher(state: ResearchState):
    """Agente Pesquisador: Busca dados fundamentais e notícias DETALHADAS."""
    company = state["company_name"]
    print(f"\n🕵️  [Researcher] Iniciando varredura na web sobre: {company}...")
    
    summary = ""
    news = ""
    try:
        with DDGS() as ddgs:
            # 1. Resumo (Setor e Histórico)
            print("   ↳ Buscando fundamentos...")
            res_summary = list(ddgs.text(f"{company} resumo setor histórico", max_results=2))
            summary = "\n".join([f"- {r['body']}" for r in res_summary]) if res_summary else "Sem dados fundamentais."
            
            # 2. Notícias (Agora pegando o CONTEÚDO também)
            print("   ↳ Buscando notícias recentes (com resumo)...")
            
            # Tenta busca focada
            res_news = list(ddgs.text(f"{company} notícias recentes finanças brasil", max_results=3))
            
            # Fallback se busca focada falhar
            if not res_news:
                print("     (Busca focada vazia, tentando genérica...)")
                res_news = list(ddgs.text(f"{company} notícias brasil", max_results=3))
            
            # --- MUDANÇA AQUI: Incluindo o 'body' (conteúdo) para o LLM ler ---
            if res_news:
                news_list = []
                for r in res_news:
                    # Formata um bloco rico de informação para o LLM
                    item = f"""
                    - TÍTULO: {r['title']}
                    - CONTEÚDO: {r['body']}
                    - LINK: {r['href']}
                    """
                    news_list.append(item)
                news = "\n".join(news_list)
            else:
                news = "Nenhuma notícia encontrada nos últimos dias."
                
    except Exception as e:
        summary = f"Erro na pesquisa: {e}"
        news = f"Erro ao buscar notícias: {e}"
        
    return {"summary_data": summary, "news_data": news}

def node_market_analyst(state: ResearchState):
    """Agente de Mercado: Consulta cotação com mapa expandido."""
    company = state["company_name"]
    print(f"📊 [Market Analyst] Consultando dados de mercado...")
    
    # Mapa de tickers EXPANDIDO
    ticker_map = {
        "AMBEV": "ABEV3.SA", 
        "PETROBRAS": "PETR4.SA", 
        "VALE": "VALE3.SA",
        "ITAU": "ITUB4.SA", "ITAÚ": "ITUB4.SA", "ITAU UNIBANCO": "ITUB4.SA", "ITAÚ UNIBANCO": "ITUB4.SA",
        "BRADESCO": "BBDC4.SA", "BANCO BRADESCO": "BBDC4.SA",
        "BB": "BBAS3.SA", "BANCO DO BRASIL": "BBAS3.SA",
        "SANTANDER": "SANB11.SA",
        "WEG": "WEGE3.SA", 
        "MAGALU": "MGLU3.SA", "MAGAZINE LUIZA": "MGLU3.SA",
        "NUBANK": "ROXO34.SA", 
        "BTG": "BPAC11.SA", "BTG PACTUAL": "BPAC11.SA",
        "KLABIN": "KLBN11.SA",
        "SUZANO": "SUZB3.SA",
        "B3": "B3SA3.SA"
    }
    
    name_upper = company.upper().strip()
    ticker = ticker_map.get(name_upper)
    
    if not ticker: ticker = f"{name_upper}.SA"
            
    price_info = f"Não encontrado ({ticker})"
    
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info.last_price
        
        if not price:
            hist = stock.history(period="1d")
            if not hist.empty: price = hist['Close'].iloc[-1]
                
        if price: 
            price_info = f"R$ {price:.2f} (Ticker: {ticker})"
            print(f"   ↳ Cotação encontrada: {price_info}")
        else:
            print(f"   ↳ Aviso: Preço não disponível para {ticker}")
            
    except Exception as e:
        price_info = f"Erro na cotação: {e}"
        
    return {"stock_data": price_info}

def node_editor(state: ResearchState):
    """Editor Chefe: Compila relatório com links E resumos."""
    print(f"✍️  [Editor] Compilando relatório executivo...")
    
    # Modelo 2.5 Flash
    MODELO = "gemini-2.5-flash" 
    
    llm = ChatGoogleGenerativeAI(
        model=MODELO, 
        temperature=0.1,
        google_api_key=os.environ["GEMINI_API_KEY"]
    )
    
    # --- MUDANÇA NO PROMPT: Pedindo resumo do conteúdo ---
    prompt = f"""
    Atue como um Analista de Investment Banking Sênior.
    Produza um relatório sobre {state['company_name']} com base nos dados abaixo.
    
    --- DADOS BRUTOS ---
    1. Fundamentos: {state['summary_data']}
    2. Notícias (Com conteúdo): {state['news_data']}
    3. Cotação: {state['stock_data']}
    --------------------
    
    FORMATO DE SAÍDA (Markdown):
    # Relatório de Análise: {state['company_name']}
    
    ## 🏢 Visão Geral & Setor
    (Sintetize o setor e o perfil da empresa em 1 parágrafo denso)
    
    ## 📰 Destaques Recentes
    (Liste as notícias. Para CADA notícia, escreva uma frase resumindo o "CONTEÚDO" e coloque o link clicável no final.)
    * Exemplo: O banco anunciou lucro recorde no trimestre... [Ler mais](Link)
    
    ## 💰 Dados de Mercado
    * **Preço Atual:** (Valor da cotação)
    """
    
    # Retry Logic
    max_tentativas = 3
    for i in range(max_tentativas):
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            return {"final_report": response.content}
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                wait_time = 80 
                print(f"⚠️ Cota do Google cheia. Aguardando {wait_time}s... ({i+1}/{max_tentativas})")
                time.sleep(wait_time)
            else:
                return {"final_report": f"Erro fatal ao gerar relatório: {e}"}
    
    return {"final_report": "Erro: Limite de cota da API excedido."}

# --- 4. CONSTRUÇÃO DO GRAFO ---
workflow = StateGraph(ResearchState)
workflow.add_node("Researcher", node_researcher)
workflow.add_node("MarketAnalyst", node_market_analyst)
workflow.add_node("Editor", node_editor)

workflow.set_entry_point("Researcher")
workflow.add_edge("Researcher", "MarketAnalyst")
workflow.add_edge("MarketAnalyst", "Editor")
workflow.add_edge("Editor", END)
app = workflow.compile()

# --- 5. EXECUÇÃO INTERATIVA ---
if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*60)
    print("      📊 AGENTE DE INVESTMENT BANKING (PREMIUM)")
    print("="*60)
    
    try:
        if len(sys.argv) > 1:
            empresa_alvo = " ".join(sys.argv[1:])
        else:
            empresa_alvo = input("\n👉 Digite o nome da empresa: ").strip()
        
        if not empresa_alvo: sys.exit(0)

        print(f"\n🚀 INICIANDO ANÁLISE PARA: {empresa_alvo.upper()}")
        print("-" * 60)

        result = app.invoke({"company_name": empresa_alvo})
        
        print("\n" + "="*60)
        print("✅ RELATÓRIO FINAL GERADO")
        print("="*60 + "\n")
        print(result["final_report"])
        print("\n" + "="*60)
        
    except KeyboardInterrupt: print("\nCancelado.")
    except Exception as e: print(f"\n❌ Erro: {e}")
# main.py
import os
import sys
import time
import re
from typing import TypedDict
from langgraph.graph import StateGraph, END

# --- 1. CONFIGURAÇÃO ---
if "GOOGLE_API_KEY" in os.environ: del os.environ["GOOGLE_API_KEY"]
if "GEMINI_API_KEY" not in os.environ:
    print("❌ ERRO: Defina GEMINI_API_KEY.")
    sys.exit(1)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    from duckduckgo_search import DDGS
    import yfinance as yf
except ImportError as e:
    print(f"❌ Dependência faltando: {e}")
    sys.exit(1)

# --- 2. ESTADO ---
class ResearchState(TypedDict):
    company_name: str
    ticker: str
    summary_data: str
    news_data: str
    stock_data: str
    final_report: str

# --- 3. NÓS DO GRAFO ---

def node_ticker_finder(state: ResearchState):
    """
    PASSO 1: Sniper de Ticker.
    Busca o nome da empresa DENTRO do Status Invest ou Investing.com para extrair o código real.
    """
    company = state["company_name"]
    print(f"\n🔎 [Ticker Finder] Validando identidade de: {company}...")
    
    found_ticker = None
    
    try:
        with DDGS() as ddgs:
            # ESTRATÉGIA DE OURO:
            # Pesquisa apenas em sites que TEM que ter o ticker no título.
            print("   ↳ Consultando bases de dados (Status Invest / Investing)...")
            query = f'site:statusinvest.com.br OR site:br.investing.com "{company}" cotação ação'
            
            # Pega os primeiros resultados (geralmente a página da ação é a primeira)
            results = list(ddgs.text(query, max_results=3))
            
            # Regex para capturar padrões como (PETR4), (VALE3), [ITUB4]
            # Procura por 4 letras seguidas de 3, 4 ou 11
            ticker_pattern = re.compile(r'\b([A-Z]{4}[3|4|11])\b')
            
            for r in results:
                # O título do Status Invest é geralmente: "Petrobras (PETR4) - Cotação..."
                title_clean = r['title'].upper()
                match = ticker_pattern.search(title_clean)
                
                if match:
                    found_ticker = match.group(0) + ".SA"
                    print(f"   🎯 Ticker Confirmado: {found_ticker} (Fonte: {r['title'][:30]}...)")
                    break
            
            # Se não achar no título, tenta no corpo do texto
            if not found_ticker:
                for r in results:
                    match = ticker_pattern.search(r['body'].upper())
                    if match:
                        found_ticker = match.group(0) + ".SA"
                        print(f"   🎯 Ticker Encontrado no texto: {found_ticker}")
                        break

    except Exception as e:
        print(f"   ❌ Erro na busca do ticker: {e}")

    # Fallback (Último recurso se os sites falharem)
    if not found_ticker:
        # Pega a primeira palavra do nome e chuta o final 3
        clean_name = company.upper().strip().split()[0]
        guess = f"{clean_name[:4]}3.SA"
        print(f"   ⚠️ Ticker não identificado nas bases oficiais. Tentando palpite: {guess}")
        found_ticker = guess
        
    return {"ticker": found_ticker}

def node_researcher(state: ResearchState):
    """
    PASSO 2: Busca Notícias usando o TICKER.
    Isso elimina ambiguidades (ex: Vale empresa vs Vale refeição).
    """
    company = state["company_name"]
    ticker_clean = state["ticker"].replace(".SA", "")
    
    print(f"🕵️  [Researcher] Buscando inteligência para: {ticker_clean}...")
    
    summary = ""
    news = ""
    
    try:
        with DDGS() as ddgs:
            # 1. Resumo (Busca institucional)
            res_sum = list(ddgs.text(f"{company} {ticker_clean} ri sobre", max_results=2))
            summary = "\n".join([f"- {r['body']}" for r in res_sum]) if res_sum else "Sem dados."

            # 2. Notícias (Busca Cirúrgica)
            # Pesquisa pelo Ticker OU Nome + "Ações"
            print("   ↳ Varrendo principais portais financeiros...")
            
            # Prioridade: Bloomberg, Investing, InfoMoney, Valor, BrazilJournal
            sites = "site:br.investing.com OR site:bloomberg.com OR site:infomoney.com.br OR site:valor.globo.com OR site:braziljournal.com"
            query_news = f'{sites} "{ticker_clean}"'
            
            res_news = list(ddgs.text(query_news, max_results=4))
            
            # Se falhar, busca aberta focada em mercado
            if not res_news:
                print("     (Busca premium vazia. Ampliando para mercado geral...)")
                q2 = f'"{company}" "{ticker_clean}" notícias mercado financeiro'
                res_news = list(ddgs.text(q2, max_results=3))

            if res_news:
                news_list = []
                for r in res_news:
                    # Limpa o título (tira o nome do site)
                    title = r['title'].split(" - ")[0].split(" | ")[0]
                    item = f"FONTE: {title}\nURL: {r['href']}\nRESUMO: {r['body']}\n"
                    news_list.append(item)
                news = "\n".join(news_list)
            else:
                news = "Nenhuma notícia relevante encontrada."

    except Exception as e:
        summary = f"Erro: {e}"
        news = "Indisponível"
        
    return {"summary_data": summary, "news_data": news}

def node_market_analyst(state: ResearchState):
    """PASSO 3: Cotação via Yahoo Finance."""
    ticker = state["ticker"]
    print(f"📊 [Market Analyst] Cotando ativo: {ticker}...")
    
    price_info = f"Erro ({ticker})"
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info.last_price
        
        # Fallback histórico
        if not price:
            hist = stock.history(period="1d")
            if not hist.empty: price = hist['Close'].iloc[-1]
        
        if price:
            price_info = f"R$ {price:.2f}"
            print(f"   ↳ Preço Atual: {price_info}")
        else:
            print(f"   ↳ Aviso: Sem dados no Yahoo para {ticker}")
    except:
        price_info = "N/A"
        
    return {"stock_data": price_info}

def node_editor(state: ResearchState):
    """PASSO 4: Relatório Final."""
    print(f"✍️  [Editor] Gerando relatório...")
    
    MODELO = "gemini-2.5-flash"
    
    llm = ChatGoogleGenerativeAI(
        model=MODELO, 
        temperature=0.1,
        google_api_key=os.environ["GEMINI_API_KEY"]
    )
    
    prompt = f"""
    Você é um Analista de Equity Research. Gere um relatório sobre: {state['company_name']} ({state['ticker']}).
    
    INPUTS:
    - Resumo: {state['summary_data']}
    - Notícias: {state['news_data']}
    - Cotação: {state['stock_data']}
    
    OUTPUT (Markdown):
    # Equity Research: {state['company_name']}
    
    ## 🏢 Perfil Corporativo
    (Resumo do negócio em 1 parágrafo)
    
    ## 📰 Notícias Relevantes
    (Liste as 3 mais importantes. OBRIGATÓRIO: Link clicável no final).
    * [Título da Matéria](Link) - Resumo de 1 linha.
    
    ## 💰 Dados do Ativo
    * **Ticker:** {state['ticker']}
    * **Preço:** {state['stock_data']}
    """
    
    for i in range(3):
        try:
            res = llm.invoke([HumanMessage(content=prompt)])
            return {"final_report": res.content}
        except Exception as e:
            if "429" in str(e): 
                print(f"⚠️ Cota cheia. Aguardando 60s...")
                time.sleep(60)
            else: return {"final_report": f"Erro: {e}"}
            
    return {"final_report": "Erro de cota."}

# --- 4. GRAFO ---
workflow = StateGraph(ResearchState)
workflow.add_node("TickerFinder", node_ticker_finder)
workflow.add_node("Researcher", node_researcher)
workflow.add_node("MarketAnalyst", node_market_analyst)
workflow.add_node("Editor", node_editor)

workflow.set_entry_point("TickerFinder")
workflow.add_edge("TickerFinder", "Researcher")
workflow.add_edge("Researcher", "MarketAnalyst")
workflow.add_edge("MarketAnalyst", "Editor")
workflow.add_edge("Editor", END)

app = workflow.compile()

# --- 5. EXECUÇÃO ---
if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*60)
    print(" 📊 AGENTE SNIPER: STATUS INVEST & AUTO-DISCOVERY")
    print("="*60)
    
    try:
        if len(sys.argv) > 1: target = " ".join(sys.argv[1:])
        else: target = input("\n👉 Empresa: ").strip()
        if not target: sys.exit()

        print(f"\n🚀 START: {target.upper()}")
        print("-" * 60)
        
        res = app.invoke({"company_name": target})
        
        print("\n" + "="*60)
        print(res["final_report"])
        print("="*60 + "\n")
        
    except KeyboardInterrupt: print("\nFim.")
    except Exception as e: print(f"\nErro: {e}")
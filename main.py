# main.py
import os
import sys
import time
import re
import warnings
from contextlib import contextmanager
from typing import TypedDict
from langgraph.graph import StateGraph, END

# --- 0. CONFIGURAÇÃO VISUAL E SILENCIAMENTO ---

# Classe de Cores ANSI (Funciona na maioria dos terminais)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Silencia warnings
warnings.filterwarnings("ignore")
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

@contextmanager
def suppress_stdout_stderr():
    """Cala a boca de bibliotecas fofoqueiras."""
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

# --- 1. CONFIGURAÇÃO ---
if "GOOGLE_API_KEY" in os.environ: del os.environ["GOOGLE_API_KEY"]
if "GEMINI_API_KEY" not in os.environ:
    print(f"{Colors.FAIL}❌ ERRO: Defina GEMINI_API_KEY.{Colors.ENDC}")
    sys.exit(1)

try:
    with suppress_stdout_stderr():
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        from duckduckgo_search import DDGS
        import yfinance as yf
except ImportError as e:
    print(f"{Colors.FAIL}❌ Dependência faltando: {e}{Colors.ENDC}")
    sys.exit(1)

# --- 2. ESTADO ---
class ResearchState(TypedDict):
    company_name: str
    ticker: str
    summary_data: str
    news_data: str
    stock_data: str
    final_report: str

# --- 3. NÓS DO GRAFO (AGENTS COLORIDOS) ---

def node_ticker_finder(state: ResearchState):
    company = state["company_name"]
    # Cor CIANO para o Sherlock
    print(f"\n{Colors.CYAN}🔎 [Ticker Finder]{Colors.ENDC} Identificando ativo para: {Colors.BOLD}{company}{Colors.ENDC}...")
    
    found_ticker = None
    clean_input = company.upper().strip()
    clean_input = re.sub(r'\[\d+;?\d*[A-Z]', '', clean_input).replace('^', '').strip()

    # Estratégia 0: Input Direto
    direct_match = re.search(r'\b([A-Z]{4})(3|4|11)\b', clean_input)
    if direct_match:
        found_ticker = direct_match.group(0) + ".SA"
        print(f"   {Colors.GREEN}🎯 Ticker identificado diretamente:{Colors.ENDC} {found_ticker}")
        return {"ticker": found_ticker}

    # Estratégia 1: Busca Oficial
    try:
        with suppress_stdout_stderr():
            with DDGS() as ddgs:
                query = f'site:statusinvest.com.br OR site:br.investing.com "{company}" código ação'
                results = list(ddgs.text(query, region='br-pt', max_results=3))
                for r in results:
                    match = re.search(r'\b([A-Z]{4}(?:3|4|11))\b', r['title'].upper())
                    if match:
                        found_ticker = match.group(1) + ".SA"
                        break
                
                if not found_ticker:
                    q2 = f'qual o ticker código da ação da empresa {company} B3'
                    res2 = list(ddgs.text(q2, region='br-pt', max_results=2))
                    for r in res2:
                        match = re.search(r'\b([A-Z]{4}(?:3|4|11))\b', r['body'].upper())
                        if match:
                            found_ticker = match.group(1) + ".SA"
                            break
        if found_ticker: 
            print(f"   {Colors.GREEN}🎯 Ticker Confirmado:{Colors.ENDC} {found_ticker}")
    except: pass

    # Estratégia 2: Palpite
    if not found_ticker:
        if len(clean_input) >= 5 and clean_input[-1] in ['3', '4']:
            guess = f"{clean_input[:4]}{clean_input[-1]}.SA"
            print(f"   {Colors.WARNING}⚠️ Input parece conter erro. Corrigindo para:{Colors.ENDC} {guess}")
            found_ticker = guess
        else:
            clean_name = ''.join(e for e in clean_input if e.isalpha())
            guess = f"{clean_name[:4]}3.SA"
            print(f"   {Colors.WARNING}⚠️ Ticker não encontrado. Usando palpite padrão:{Colors.ENDC} {guess}")
            found_ticker = guess
        
    return {"ticker": found_ticker}

def node_researcher(state: ResearchState):
    company = state["company_name"]
    ticker_clean = state["ticker"].replace(".SA", "")
    # Cor AZUL para o Pesquisador
    print(f"{Colors.BLUE}🕵️  [Researcher]{Colors.ENDC} Buscando inteligência para: {Colors.BOLD}{ticker_clean}{Colors.ENDC}...")
    
    summary = ""
    news = ""
    try:
        with suppress_stdout_stderr():
            with DDGS() as ddgs:
                res_sum = list(ddgs.text(f"{company} {ticker_clean} ri institucional", region='br-pt', max_results=2))
                summary = "\n".join([f"- {r['body']}" for r in res_sum]) if res_sum else "Sem dados."

                sites = "site:br.investing.com OR site:bloomberg.com OR site:infomoney.com.br OR site:valor.globo.com OR site:braziljournal.com"
                query_news = f'{sites} "{ticker_clean}"'
                res_news = list(ddgs.text(query_news, region='br-pt', max_results=4))
                
                if not res_news:
                    q2 = f'"{company}" ações mercado financeiro notícias'
                    res_news = list(ddgs.text(q2, region='br-pt', max_results=3))

                if res_news:
                    news_list = []
                    for r in res_news:
                        title = r['title'].split(" - ")[0].split(" | ")[0]
                        item = f"FONTE: {title}\nURL: {r['href']}\nRESUMO: {r['body']}\n"
                        news_list.append(item)
                    news = "\n".join(news_list)
                else: news = "Nenhuma notícia relevante encontrada."
        print(f"   ↳ {Colors.GREEN}Dados coletados com sucesso.{Colors.ENDC}")
    except:
        summary = "Erro na coleta."
        news = "Indisponível"
        print(f"   {Colors.FAIL}⚠️ Falha parcial na coleta de notícias.{Colors.ENDC}")
    return {"summary_data": summary, "news_data": news}

def node_market_analyst(state: ResearchState):
    ticker = state["ticker"]
    # Cor MAGENTA para Mercado
    print(f"{Colors.HEADER}📊 [Market Analyst]{Colors.ENDC} Cotando ativo: {ticker}...")
    price_info = f"Erro ({ticker})"
    with suppress_stdout_stderr():
        try:
            stock = yf.Ticker(ticker)
            price = stock.fast_info.last_price
            if not price:
                hist = stock.history(period="1d")
                if not hist.empty: price = hist['Close'].iloc[-1]
            if price: price_info = f"R$ {price:.2f}"
        except: pass
    
    if "R$" in price_info: 
        print(f"   ↳ {Colors.GREEN}Preço Atual: {price_info}{Colors.ENDC}")
    else: 
        print(f"   ↳ {Colors.WARNING}Aviso: Cotação indisponível.{Colors.ENDC}")
    return {"stock_data": price_info}

def node_editor(state: ResearchState):
    # Cor AMARELA para o Editor
    print(f"{Colors.WARNING}✍️  [Editor]{Colors.ENDC} Gerando relatório...")
    
    MODELO = "gemini-2.0-flash-lite"
    
    try:
        llm = ChatGoogleGenerativeAI(
            model=MODELO, 
            temperature=0.1,
            google_api_key=os.environ["GEMINI_API_KEY"]
        )
        
        prompt = f"""
        Analista de Equity Research. Relatório sobre: {state['company_name']} ({state['ticker']}).
        
        DADOS:
        - Resumo: {state['summary_data']}
        - Notícias: {state['news_data']}
        - Cotação: {state['stock_data']}
        
        MARKDOWN OUTPUT:
        # Equity Research: {state['company_name']}
        
        ## 🏢 Perfil Corporativo
        (Resumo do negócio em 1 parágrafo)
        
        ## 📰 Notícias Relevantes
        (3 bullets com Link clicável no final).
        * [Título](Link) - Resumo.
        
        ## 💰 Mercado
        * **Ticker:** {state['ticker']}
        * **Preço:** {state['stock_data']}
        """
        
        max_tentativas = 3
        tempo_espera = 60
        
        for i in range(max_tentativas):
            try:
                res = llm.invoke([HumanMessage(content=prompt)])
                return {"final_report": res.content}
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"{Colors.FAIL}⚠️ Cota cheia (Tentativa {i+1}/{max_tentativas}). Aguardando {tempo_espera}s...{Colors.ENDC}")
                    time.sleep(tempo_espera)
                    tempo_espera += 30
                else: 
                    return {"final_report": f"Erro: {e}"}
    except:
        return {"final_report": "Erro interno no Editor."}
            
    return {"final_report": "Erro: Limite de cota excedido."}

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
    print(f"{Colors.HEADER}{'='*60}")
    print(" 📊 AGENTE DE ELITE: V10 (COLORFUL EDITION)")
    print(f"{'='*60}{Colors.ENDC}")
    
    try:
        if len(sys.argv) > 1: target = " ".join(sys.argv[1:])
        else: target = input(f"\n👉 {Colors.BOLD}Empresa: {Colors.ENDC}").strip()
        
        target = re.sub(r'\[\d+;?\d*[A-Z]', '', target).replace('^', '').strip()
        if not target: sys.exit()

        print(f"\n🚀 {Colors.BOLD}START: {target.upper()}{Colors.ENDC}")
        print("-" * 60)
        res = app.invoke({"company_name": target})
        print("\n" + f"{Colors.GREEN}{'='*60}")
        print(res["final_report"])
        print(f"{'='*60}{Colors.ENDC}" + "\n")
    except KeyboardInterrupt: print(f"\n{Colors.FAIL}Fim.{Colors.ENDC}")
    except Exception as e: print(f"\n{Colors.FAIL}Erro: {e}{Colors.ENDC}")
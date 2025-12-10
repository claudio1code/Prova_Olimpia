import os
import sys
import re
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from duckduckgo_search import DDGS
import yfinance as yf

# Mapeamento de empresas conhecidas
TICKER_MAP = {
    "PETROBRAS": "PETR4.SA", "VALE": "VALE3.SA", "ITAU": "ITUB4.SA",
    "ITAÚ": "ITUB4.SA", "AMBEV": "ABEV3.SA", "BRADESCO": "BBDC4.SA",
    "BB": "BBAS3.SA", "BANCO DO BRASIL": "BBAS3.SA", "MINERVA": "BEEF3.SA"
}

class State(TypedDict):
    company: str
    ticker: str
    summary: str
    news: str
    price: str
    report: str

def find_ticker(state: State):
    company = state["company"].upper()
    print(f"\n🔎 Buscando ticker: {company}...")
    
    # Verifica mapeamento local primeiro
    for key, ticker in TICKER_MAP.items():
        if key in company:
            print(f"   ✓ Encontrado: {ticker}")
            return {"ticker": ticker}
    
    # Busca em sites confiáveis brasileiros
    sites = [
        "statusinvest.com.br/acoes/",
        "br.investing.com/equities/",
        "fundamentus.com.br/detalhes.php"
    ]
    
    ticker = None
    for site in sites:
        try:
            results = DDGS().text(f'site:{site} "{company}"', max_results=2)
            for r in results:
                # Regex para capturar ticker brasileiro (4 letras + 3/4/11)
                match = re.search(r'\b([A-Z]{4}[34](?:11)?)\b', r['title'] + r['body'])
                if match:
                    ticker = match.group(1) + ".SA"
                    print(f"   ✓ Encontrado em {site}: {ticker}")
                    return {"ticker": ticker}
        except:
            continue
    
    # Fallback
    ticker = f"{company[:4]}3.SA"
    print(f"   ⚠ Não encontrado. Usando: {ticker}")
    return {"ticker": ticker}

def search_news(state: State):
    ticker = state["ticker"].replace(".SA", "")
    print(f"📰 Buscando notícias: {ticker}...")
    
    # Sites de notícias financeiras confiáveis BR
    query = f'site:infomoney.com.br OR site:valor.globo.com OR site:br.investing.com OR site:moneytimes.com.br "{ticker}"'
    
    try:
        results = DDGS().text(query, max_results=4)
        if not results:
            # Fallback para busca geral
            results = DDGS().text(f'"{state["company"]}" ações Brasil notícias', max_results=3)
        
        news_list = []
        for r in results:
            title = r['title'].split(' - ')[0].split(' | ')[0][:80]
            news_list.append(f"• {title}\n  {r['href']}\n")
        
        news = "\n".join(news_list) if news_list else "Sem notícias recentes."
        
        # Busca resumo da empresa
        summary_results = DDGS().text(f'"{state["company"]}" sobre a empresa setor atuação', max_results=2)
        summary = summary_results[0]['body'][:300] if summary_results else "N/A"
        
        return {"news": news, "summary": summary}
    except Exception as e:
        return {"news": "Erro na busca", "summary": "N/A"}

def get_price(state: State):
    ticker = state["ticker"]
    print(f"💰 Cotação: {ticker}...")
    
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info.last_price
        
        if not price:
            hist = stock.history(period="1d")
            price = hist['Close'].iloc[-1] if not hist.empty else None
        
        return {"price": f"R$ {price:.2f}" if price else "N/A"}
    except:
        return {"price": "N/A"}

def generate_report(state: State):
    print(f"✍️  Gerando relatório...\n")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.1,
        google_api_key=os.environ["GEMINI_API_KEY"]
    )
    
    prompt = f"""Você é um analista de Investment Banking. Gere um relatório sobre {state['company']}.

DADOS COLETADOS:
Ticker: {state['ticker']}
Preço: {state['price']}
Resumo: {state['summary']}
Notícias: {state['news']}

FORMATO DO RELATÓRIO:
# 📊 Relatório: {state['company'].upper()}

## 1. RESUMO DA EMPRESA
[Setor, histórico, principais produtos - 2-3 parágrafos]

## 2. NOTÍCIAS RECENTES
[Liste 2-3 notícias com título e link clicável]

## 3. VALOR DA AÇÃO
**Ticker:** {state['ticker']}
**Preço Atual:** {state['price']}

Seja objetivo e profissional."""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return {"report": response.content}
    except Exception as e:
        return {"report": f"Erro ao gerar relatório: {e}"}

# Construir grafo
workflow = StateGraph(State)
workflow.add_node("ticker", find_ticker)
workflow.add_node("news", search_news)
workflow.add_node("price", get_price)
workflow.add_node("report", generate_report)

workflow.set_entry_point("ticker")
workflow.add_edge("ticker", "news")
workflow.add_edge("news", "price")
workflow.add_edge("price", "report")
workflow.add_edge("report", END)

app = workflow.compile()

# Executar
if __name__ == "__main__":
    os.system('clear')
    print("="*60)
    print("📊 ANÁLISE AUTOMATIZADA DE EMPRESAS - LANGCHAIN")
    print("="*60)
    
    try:
        company = input("\n👉 Nome da empresa: ").strip()
        if not company:
            sys.exit()
        
        print(f"\n🚀 Analisando: {company.upper()}")
        print("-"*60)
        
        result = app.invoke({"company": company})
        
        print("\n" + "="*60)
        print(result["report"])
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nProcesso interrompido.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
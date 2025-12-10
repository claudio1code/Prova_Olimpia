# main.py - VERSÃO ECONÔMICA (1 CHAMADA APENAS)
import os
import sys
import time

# --- 1. CONFIGURAÇÃO DE CHAVE ---
if "GOOGLE_API_KEY" in os.environ: del os.environ["GOOGLE_API_KEY"]
if "GEMINI_API_KEY" not in os.environ:
    print("❌ ERRO: Defina GEMINI_API_KEY no comando.")
    sys.exit(1)

# Importações
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

try:
    from duckduckgo_search import DDGS
except ImportError:
    print("❌ Erro: pip install -U duckduckgo-search")
    sys.exit(1)

# --- 2. COLETA DE DADOS MANUAL (CUSTO ZERO DE TOKEN) ---

def search_web_manual(query):
    """Busca no DuckDuckGo sem gastar IA."""
    print(f"🔎 Pesquisando: '{query}'...")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results: return "Sem resultados."
        return "\n".join([f"- {r['title']}: {r['href']}\n  Resumo: {r['body']}" for r in results])
    except Exception as e:
        return f"Erro na busca: {e}"

def get_stock_manual(ticker):
    """Pega cotação sem gastar IA."""
    print(f"💰 Consultando ação: {ticker}...")
    import yfinance as yf
    try:
        s = yf.Ticker(ticker + ".SA")
        # Tenta pegar preço de várias formas
        p = s.fast_info.last_price
        if not p:
             hist = s.history(period="1d")
             if not hist.empty: p = hist['Close'].iloc[-1]
        
        return f"R$ {p:.2f}" if p else "Preço não disponível."
    except Exception as e:
        return f"Erro cotação: {e}"

# --- 3. ORQUESTRAÇÃO MANUAL ---

company = "Ambev"
print(f"🚀 INICIANDO MODO ECONOMICO PARA: {company}\n")

# Passo 1: Coletar dados (Python puro, rápido e grátis)
dados_resumo = search_web_manual(f"{company} resumo setor histórico produtos")
time.sleep(2) # Pausa para não bloquear o DuckDuckGo

dados_noticias = search_web_manual(f"{company} notícias recentes economia negócios")
time.sleep(2)

dados_acao = get_stock_manual("ABEV3")

print("\n📦 Dados coletados! Montando o prompt para o Gemini...")

# Passo 2: Montar o Prompt com os dados já mastigados
prompt_final = f"""
Você é um analista financeiro. Eu já coletei os dados brutos sobre a empresa {company}. 
Sua tarefa é APENAS formatar esses dados em um relatório profissional.

--- DADOS COLETADOS ---
1. SOBRE A EMPRESA:
{dados_resumo}

2. NOTÍCIAS RECENTES (Use os links fornecidos):
{dados_noticias}

3. COTAÇÃO ATUAL:
{dados_acao}
-----------------------

SAÍDA ESPERADA:
Crie um relatório organizado em Markdown com:
- Título
- Resumo Executivo (Setor e Histórico)
- Seção de Notícias (Com Título e Link)
- Destaque do Valor da Ação
"""

# --- 4. CHAMADA ÚNICA AO LLM ---

# Usando o modelo que apareceu na sua lista como disponível
# 'gemini-2.5-flash' é o mais novo e costuma ter cota livre.
MODELO = "gemini-2.5-flash" 

print(f"🔌 Enviando para o Gemini ({MODELO}) - 1 ÚNICA CHAMADA...")

try:
    llm = ChatGoogleGenerativeAI(
        model=MODELO,
        temperature=0.2,
        google_api_key=os.environ["GEMINI_API_KEY"]
    )
    
    resposta = llm.invoke(prompt_final)
    
    print("\n" + "="*50)
    print("✅ RELATÓRIO FINAL GERADO COM SUCESSO")
    print("="*50)
    print(resposta.content)
    print("="*50)

except Exception as e:
    print(f"\n❌ Erro na chamada: {e}")
    if "404" in str(e):
        print("💡 Dica: Tente mudar a variável MODELO para 'gemini-2.0-flash' no código.")
    if "429" in str(e):
        print("💡 Dica: Espere 1 minuto. Sua conta está 100% cheia.")
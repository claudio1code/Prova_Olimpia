import os
import re

import yfinance as yf
from duckduckgo_search import DDGS
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import Colors
from ..state import ResearchState
from ..utils import suppress_stdout_stderr


def node_ticker_finder(state: ResearchState):
    company = state["company_name"]
    # Cor CIANO para o Sherlock
    print(
        f"\n{Colors.CYAN}🔎 [Ticker Finder]{Colors.ENDC} Identificando ativo para: {Colors.BOLD}{company}{Colors.ENDC}..."
    )

    def validate(candidate):
        """Verifica se o ticker existe na B3 via yfinance."""
        try:
            with suppress_stdout_stderr():
                t = yf.Ticker(candidate)
                return bool(t.fast_info.last_price) or not t.history(period="1d").empty
        except:
            return False

    found_ticker = None
    clean_input = company.upper().strip()
    clean_input = re.sub(r"\[\d+;?\d*[A-Z]", "", clean_input).replace("^", "").strip()

    # Estratégia 0: Input Direto
    direct_match = re.search(r"\b([A-Z]{4})(3|4|11)\b", clean_input)
    if direct_match:
        candidate = direct_match.group(0) + ".SA"
        if validate(candidate):
            found_ticker = candidate
            print(
                f"   {Colors.GREEN}🎯 Ticker identificado diretamente:{Colors.ENDC} {found_ticker}"
            )
            return {"ticker": found_ticker}

    # Estratégia 0.5: Mapa de Conhecimento (Correção para nomes comuns)
    KNOWN_TICKERS = {
        "MAGAZINE LUIZA": "MGLU3.SA",
        "MAGALU": "MGLU3.SA",
        "MGLU": "MGLU3.SA",
        "PETROBRAS": "PETR4.SA",
        "PETRO": "PETR4.SA",
        "VALE": "VALE3.SA",
        "ITAU": "ITUB4.SA",
        "ITAU UNIBANCO": "ITUB4.SA",
        "BRADESCO": "BBDC4.SA",
        "AMBEV": "ABEV3.SA",
        "BANCO DO BRASIL": "BBAS3.SA",
        "BB": "BBAS3.SA",
        "B3": "B3SA3.SA",
        "WEG": "WEGE3.SA",
        "LOCALIZA": "RENT3.SA",
        "SUZANO": "SUZB3.SA",
        "GERDAU": "GGBR4.SA",
        "RAIA DROGASIL": "RADL3.SA",
        "RD SAUDE": "RADL3.SA",
        "RUMO": "RAIL3.SA",
        "VIBRA": "VBBR3.SA",
        "COSAN": "CSAN3.SA",
        "TELEFONICA": "VIVT3.SA",
        "VIVO": "VIVT3.SA",
        "CCR": "CCRO3.SA",
        "HAPVIDA": "HAPV3.SA",
        "SABESP": "SBSP3.SA",
        "EQUATORIAL": "EQTL3.SA",
        "KLABIN": "KLBN11.SA",
        "LOJAS RENNER": "LREN3.SA",
        "RENNER": "LREN3.SA",
        "EMBRAER": "EMBR3.SA",
        "HYPERA": "HYPE3.SA",
        "MINERVA": "BEEF3.SA",
        "MARFRIG": "MRFG3.SA",
        "JBS": "JBSS3.SA",
        "BRF": "BRFS3.SA",
        "SANEPAR": "SAPR11.SA",
        "SAPR": "SAPR11.SA",
        "CEMIG": "CMIG4.SA",
        "COPEL": "CPLE6.SA",
        "ELETROBRAS": "ELET3.SA",
        "ELET": "ELET3.SA",
    }

    # Verifica match no dicionário
    for key, val in KNOWN_TICKERS.items():
        if key in clean_input or clean_input in key:
            # Prioriza match exato ou início forte
            if clean_input == key or key == clean_input.split()[0]:
                found_ticker = val
                break

    if found_ticker:
        print(
            f"   {Colors.GREEN}🎯 Ticker Conhecido (Database):{Colors.ENDC} {found_ticker}"
        )
        return {"ticker": found_ticker}

    # Estratégia 1: Busca Oficial
    try:
        with suppress_stdout_stderr():
            with DDGS() as ddgs:
                # Sem aspas para permitir fuzzy search (correção de KBLN4 -> KLBN4)
                query = f"site:statusinvest.com.br OR site:br.investing.com {company} código ação"
                results = list(ddgs.text(query, region="br-pt", max_results=3))
                for r in results:
                    match = re.search(r"\b([A-Z]{4}(?:3|4|11))\b", r["title"].upper())
                    if match:
                        candidate = match.group(1) + ".SA"
                        if validate(candidate):
                            found_ticker = candidate
                            break

                if not found_ticker:
                    # Estratégia Typos: Se a entrada parece um ticker (ex: KBLN4), busca correção
                    if re.search(r"\b[A-Z]{4}\d\b", clean_input):
                        q_typo = f"ticker correto da empresa {company} statusinvest"
                        res_typo = list(
                            ddgs.text(q_typo, region="br-pt", max_results=2)
                        )
                        for r in res_typo:
                            match = re.search(
                                r"\b([A-Z]{4}(?:3|4|11))\b", r["title"].upper()
                            )
                            if match:
                                candidate = match.group(1) + ".SA"
                                if validate(candidate):
                                    found_ticker = candidate
                                    break

                if not found_ticker:
                    q2 = f"qual o ticker código da ação da empresa {company} B3"
                    res2 = list(ddgs.text(q2, region="br-pt", max_results=2))
                    for r in res2:
                        match = re.search(
                            r"\b([A-Z]{4}(?:3|4|11))\b", r["body"].upper()
                        )
                        if match:
                            candidate = match.group(1) + ".SA"
                            if validate(candidate):
                                found_ticker = candidate
                                break
        if found_ticker:
            print(f"   {Colors.GREEN}🎯 Ticker Confirmado:{Colors.ENDC} {found_ticker}")
    except:
        pass

    # Estratégia 1.5: Inteligência Artificial (Gemini)
    if not found_ticker and "GEMINI_API_KEY" in os.environ:
        print(f"   {Colors.BLUE}🧠 Consultando IA sobre ticker...{Colors.ENDC}")
        keys = os.environ["GEMINI_API_KEY"].split(",")
        for key in keys:
            key = key.strip()
            if not key:
                continue
            try:
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash", temperature=0.0, google_api_key=key
                )
                prompt = f"Qual o código de negociação (Ticker) principal da ação da empresa '{company}' na Bolsa do Brasil (B3)? Responda APENAS o código (ex: PETR4). Se não souber, responda N/A."
                res = llm.invoke([HumanMessage(content=prompt)])
                candidate_raw = res.content.strip().upper()

                # Extrai ticker da resposta
                match = re.search(r"\b([A-Z]{4}(?:3|4|11))\b", candidate_raw)
                if match:
                    candidate = match.group(1) + ".SA"
                    if validate(candidate):
                        found_ticker = candidate
                        print(
                            f"   {Colors.GREEN}🎯 IA Identificou:{Colors.ENDC} {found_ticker}"
                        )
                        return {"ticker": found_ticker}
                break  # Se a API respondeu, encerra o loop de chaves
            except:
                continue

    # Estratégia 2: Palpite
    if not found_ticker:
        if len(clean_input) >= 5 and clean_input[-1] in ["3", "4"]:
            guess = f"{clean_input[:4]}{clean_input[-1]}.SA"
            if validate(guess):
                print(
                    f"   {Colors.WARNING}⚠️ Input parece conter erro. Corrigindo para:{Colors.ENDC} {guess}"
                )
                found_ticker = guess
        else:
            clean_name = "".join(e for e in clean_input if e.isalpha())
            guess = f"{clean_name[:4]}3.SA"
            if validate(guess):
                print(
                    f"   {Colors.WARNING}⚠️ Ticker não encontrado. Usando palpite padrão:{Colors.ENDC} {guess}"
                )
                found_ticker = guess

    if not found_ticker:
        print(
            f"   {Colors.FAIL}❌ Ticker não identificado ou inválido na B3.{Colors.ENDC}"
        )
        found_ticker = "N/A"

    return {"ticker": found_ticker}

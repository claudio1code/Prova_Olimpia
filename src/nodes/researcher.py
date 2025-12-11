import os

import requests
from duckduckgo_search import DDGS
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import Colors
from ..state import ResearchState
from ..utils import suppress_stdout_stderr


def node_researcher(state: ResearchState):
    company = state["company_name"]
import os

import requests
from duckduckgo_search import DDGS
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import Colors
from ..state import ResearchState
from ..utils import suppress_stdout_stderr


def node_researcher(state: ResearchState):
    company = state["company_name"]
    ticker_obj = state["ticker"]  # Usar o objeto ticker completo
    ticker_clean = ticker_obj.replace(".SA", "") if ticker_obj and ticker_obj != "N/A" else company

    # Cor AZUL para o Pesquisador
    print(
        f"{Colors.BLUE}🕵️  [Researcher]{Colors.ENDC} Buscando inteligência para: {Colors.BOLD}{ticker_clean}{Colors.ENDC}... (Ticker: {ticker_obj if ticker_obj else 'N/A'})"
    )

    summary = ""
    news = ""
    try:
        with suppress_stdout_stderr():
            # Filtros de exclusão (Anti-SAC e Site Oficial)
            company_slug = "".join(e for e in company if e.isalnum()).lower()
            exclusions = f"-site:{company_slug}.com.br -site:reclameaqui.com.br -site:consumidor.gov.br -site:expressmag.com.br"
            sites = "site:br.investing.com OR site:infomoney.com.br OR site:valor.globo.com OR site:braziljournal.com OR site:moneytimes.com.br"

            candidates = []
            seen_urls = set()

            def add_candidates(results):
                for r in results:
                    # Normalização Google vs DDG
                    url = r.get("href") or r.get("link")
                    body = r.get("body") or r.get("snippet")
                    title = r.get("title")

                    if not url or url in seen_urls:
                        continue
                    if "/tag/" in url or "/cotacao/" in url:
                        continue
                    # Filtros de exclusão simples
                    if "expressmag.com.br" in url or "reclameaqui.com.br" in url:
                        continue

                    seen_urls.add(url)
                    candidates.append({"title": title, "href": url, "body": body})

            # --- ESTRATÉGIA HÍBRIDA (GOOGLE / DDG) ---
            USE_GOOGLE = (
                "GOOGLE_CSE_ID" in os.environ and "GOOGLE_API_KEY" in os.environ
            )

            search_query_base = ""
            if ticker_obj and ticker_obj != "N/A":
                search_query_base = f'"{ticker_clean}"'
            else:
                search_query_base = f'"{company}"'


            if USE_GOOGLE:
                print(
                    f"   {Colors.BLUE}📡 Usando Google Search API (Oficial)...{Colors.ENDC}"
                )
                search = GoogleSearchAPIWrapper()

                # Resumo
                res_sum = search.results(
                    f"{company} {ticker_clean} ri institucional", num_results=2
                )
                summary = (
                    "\n".join([f"- {r['snippet']}" for r in res_sum])
                    if res_sum
                    else "Sem dados."
                )

                # Busca Notícias (Camadas)
                keywords = "lucro OR resultado OR recomendação OR dividendo"
                q1 = f'{sites} {search_query_base} {keywords}'
                res1 = search.results(q1, num_results=5)
                add_candidates(res1)

                if len(candidates) < 5:
                    q2 = f'{sites} {search_query_base}'
                    res2 = search.results(q2, num_results=5)
                    add_candidates(res2)

                if len(candidates) < 8:
                    q3 = f'"{company}" ações mercado financeiro {exclusions}' # Busca mais ampla com nome da empresa
                    res3 = search.results(q3, num_results=5)
                    add_candidates(res3)

            else:
                # Fallback: DuckDuckGo
                with DDGS() as ddgs:
                    # Resumo
                    res_sum = list(
                        ddgs.text(
                            f"{company} {ticker_clean} ri institucional",
                            region="br-pt",
                            max_results=2,
                        )
                    )
                    summary = (
                        "\n".join([f"- {r['body']}" for r in res_sum])
                        if res_sum
                        else "Sem dados."
                    )

                    # Coleta em Camadas (DDG)
                    # 1. Busca Restrita
                    keywords = "lucro OR resultado OR recomendação OR dividendo"
                    q1 = f'{sites} "{ticker_clean}" {keywords}'
                    res1 = list(
                        ddgs.text(q1, region="br-pt", max_results=5, timelimit="y")
                    )
                    add_candidates(res1)

                    # 2. Busca Anual
                    if len(candidates) < 5:
                        q2 = f'{sites} "{company}"' # Usa nome da empresa se ticker falhar
                        res2 = list(
                            ddgs.text(q2, region="br-pt", max_results=5, timelimit="y")
                        )
                        add_candidates(res2)

                    # 3. Busca Aberta
                    if len(candidates) < 8:
                        q3 = f'"{company}" ações mercado financeiro {exclusions}'
                        res3 = list(ddgs.text(q3, region="br-pt", max_results=5))
                        add_candidates(res3)

                # 4. Validação de Links (Anti-404) nos candidatos selecionados
                valid_candidates = []
                print(f"   ↳ Analisando {len(candidates)} notícias brutas...")

                for r in candidates[:10]:  # Limita a 10 para análise
                    try:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                        }
                        resp = requests.get(
                            r["href"], headers=headers, timeout=2, stream=True
                        )
                        if resp.status_code < 400:
                            valid_candidates.append(r)
                        resp.close()
                    except Exception:
                        continue

                if valid_candidates:
                    # --- AI CURATION ---
                    print(
                        f"   ↳ {Colors.CYAN}🧠 IA Curando as {len(valid_candidates)} melhores notícias...{Colors.ENDC}"
                    )

                    curated_news = ""

                    # Rotação de chaves (Mesma lógica do Editor)
                    if "GEMINI_API_KEY" in os.environ:
                        keys = os.environ["GEMINI_API_KEY"].split(",")
                        for key in keys:
                            key = key.strip()
                            if not key:
                                continue

                            try:
                                llm = ChatGoogleGenerativeAI(
                                    model="gemini-2.5-flash",
                                    temperature=0.1,
                                    google_api_key=key,
                                )

                                # Prepara input para IA
                                news_feed = "\n\n".join(
                                    [
                                        f"ID {i + 1}:\nTitulo: {n['title']}\nLink: {n['href']}\nSnippet: {n['body']}"
                                        for i, n in enumerate(valid_candidates)
                                    ]
                                )

                                prompt = f"""
                                Você é um Editor Chefe de Investment Banking.
                                Sua tarefa é selecionar as 3 notícias mais relevantes para um investidor sobre: {company} ({ticker_clean}).

                                LISTA DE NOTÍCIAS BRUTAS:
                                {news_feed}

                                INSTRUÇÕES:
                                1. Ignore notícias repetidas, velhas ou irrelevantes (ex: 2ª via, atendimento).
                                2. Priorize: Resultados Financeiros, Fusões, Dividendos, Análises de Mercado.
                                3. Retorne APENAS 3 itens formatados em Markdown.

                                FORMATO DE SAÍDA:
                                * **[Título Resumido da Notícia](Link Original)**
                                  > Resumo executivo de 2 linhas explicando o impacto para a ação.
                                """

                                res = llm.invoke([HumanMessage(content=prompt)])
                                curated_news = res.content
                                break  # Sucesso
                            except Exception:
                                continue  # Tenta próxima chave

                    if curated_news:
                        news = curated_news
                    else:
                        # Fallback Mecânico (se IA falhar ou sem chave)
                        print(
                            f"   ↳ {Colors.WARNING}⚠️ Curadoria IA indisponível. Usando seleção mecânica.{Colors.ENDC}"
                        )
                        news_list = []
                        for r in valid_candidates[:3]:
                            title = r["title"].split(" - ")[0].split(" | ")[0]
                            item = f"* **[{title}]({r['href']})**\n  > {r['body']}\n"
                            news_list.append(item)
                        news = "\n".join(news_list)
                else:
                    news = "Nenhuma notícia relevante encontrada."
        print(f"   ↳ {Colors.GREEN}Dados coletados com sucesso.{Colors.ENDC}")
    except:
        summary = "Erro na coleta."
        news = "Indisponível"
        print(f"   {Colors.FAIL}⚠️ Falha parcial na coleta de notícias.{Colors.ENDC}")
    return {"summary_data": summary, "news_data": news}

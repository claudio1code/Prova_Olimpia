import os
import time

import requests
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Importação atualizada do DuckDuckGo
try:
    from ddgs import DDGS  # Novo pacote
except ImportError:
    from duckduckgo_search import DDGS  # Fallback para versão antiga

from ..config import Colors
from ..state import ResearchState
from ..utils import suppress_stdout_stderr


def node_researcher(state: ResearchState):
    company = state["company_name"]
    ticker_obj = state["ticker"]
    ticker_clean = ticker_obj.replace(".SA", "") if ticker_obj and ticker_obj != "N/A" else company

    print(
        f"{Colors.BLUE}🕵️  [Researcher]{Colors.ENDC} Buscando inteligência para: {Colors.BOLD}{ticker_clean}{Colors.ENDC}... (Ticker: {ticker_obj if ticker_obj else 'N/A'})"
    )

    summary = ""
    news = ""
    
    try:
        # Filtros de exclusão AMPLIADOS (bloqueia páginas de cotação)
        company_slug = "".join(e for e in company if e.isalnum()).lower()
        exclusions = f"-site:{company_slug}.com.br -site:reclameaqui.com.br -site:consumidor.gov.br -site:statusinvest.com.br -site:investidor10.com.br -cotacao -indicadores"
        
        # Sites de NOTÍCIAS financeiras (não cotação)
        news_sites = "site:infomoney.com.br/onde-investir OR site:valor.globo.com/financas OR site:braziljournal.com OR site:moneytimes.com.br/mercados OR site:einvestidor.estadao.com.br"

        candidates = []
        seen_urls = set()

        def add_candidates(results):
            """Filtra apenas URLs de NOTÍCIAS (não cotação)"""
            for r in results:
                url = r.get("href") or r.get("link")
                body = r.get("body") or r.get("snippet", "")
                title = r.get("title", "")

                if not url or url in seen_urls:
                    continue
                
                # FILTROS CRÍTICOS - Bloqueia páginas de cotação
                blocklist = [
                    "/cotacoes/", "/cotacao/", "/acoes/", "/indicadores/",
                    "statusinvest.com", "investidor10.com", "fundamentus.com",
                    "/tag/", "reclameaqui.com"
                ]
                
                if any(block in url.lower() for block in blocklist):
                    continue
                
                # Só adiciona se parecer notícia (tem palavras-chave)
                text_content = f"{title} {body}".lower()
                news_keywords = ["lucro", "resultado", "trimestre", "banco central", "dividendo", "reporta", "anuncia", "balanço"]
                
                if not any(kw in text_content for kw in news_keywords):
                    continue

                seen_urls.add(url)
                candidates.append({"title": title, "href": url, "body": body})

        # Estratégia híbrida
        USE_GOOGLE = "GOOGLE_CSE_ID" in os.environ and "GOOGLE_API_KEY" in os.environ

        # Ajusta query base para buscar NOTÍCIAS
        if ticker_obj and ticker_obj != "N/A":
            search_base = f"{company} {ticker_clean}"
        else:
            search_base = f"{company}"

        if USE_GOOGLE:
            print(f"   {Colors.BLUE}📡 Usando Google Search API...{Colors.ENDC}")
            try:
                search = GoogleSearchAPIWrapper()

                # Busca resumo
                res_sum = search.results(f"{company} {ticker_clean} ri institucional", num_results=2)
                summary = "\n".join([f"- {r['snippet']}" for r in res_sum]) if res_sum else "Sem dados."

                # Query para NOTÍCIAS
                keywords = "lucro OR resultado OR balanço OR dividendo OR anuncia"
                q1 = f'{news_sites} {search_base} {keywords}'
                print(f"   🔍 Query 1: {q1[:80]}...")
                res1 = search.results(q1, num_results=8)
                print(f"   ↳ {len(res1)} resultados brutos")
                add_candidates(res1)

                if len(candidates) < 3:
                    q2 = f'"{search_base}" notícia mercado financeiro {exclusions}'
                    print(f"   🔍 Query 2: {q2[:80]}...")
                    res2 = search.results(q2, num_results=8)
                    print(f"   ↳ {len(res2)} resultados brutos")
                    add_candidates(res2)
                    
            except Exception as e:
                print(f"   {Colors.FAIL}❌ Erro Google: {e}{Colors.ENDC}")
                USE_GOOGLE = False

        if not USE_GOOGLE:
            print(f"   {Colors.BLUE}📡 Usando DuckDuckGo...{Colors.ENDC}")
            try:
                with DDGS() as ddgs:
                    # Busca resumo
                    print(f"   🔍 Buscando resumo corporativo...")
                    res_sum = list(ddgs.text(f"{company} sobre empresa", region="br-pt", max_results=2))
                    summary = "\n".join([f"- {r['body']}" for r in res_sum]) if res_sum else "Sem dados."

                    # Camada 1: Notícias específicas de mercado
                    keywords = "lucro OR resultado OR balanço OR dividendo"
                    q1 = f'{search_base} {keywords} notícia {exclusions}'
                    print(f"   🔍 Query 1: {q1[:80]}...")
                    res1 = list(ddgs.text(q1, region="br-pt", max_results=8, timelimit="m"))
                    print(f"   ↳ {len(res1)} resultados brutos")
                    add_candidates(res1)

                    # Camada 2: Busca com foco em portais financeiros
                    if len(candidates) < 3:
                        q2 = f'{news_sites} {search_base}'
                        print(f"   🔍 Query 2: {q2[:80]}...")
                        res2 = list(ddgs.text(q2, region="br-pt", max_results=8, timelimit="m"))
                        print(f"   ↳ {len(res2)} resultados brutos")
                        add_candidates(res2)

                    # Camada 3: Busca aberta sem restrição de tempo
                    if len(candidates) < 3:
                        q3 = f'{search_base} notícias mercado financeiro {exclusions}'
                        print(f"   🔍 Query 3: {q3[:80]}...")
                        res3 = list(ddgs.text(q3, region="br-pt", max_results=10))
                        print(f"   ↳ {len(res3)} resultados brutos")
                        add_candidates(res3)
                        
            except Exception as e:
                print(f"   {Colors.FAIL}❌ Erro DuckDuckGo: {e}{Colors.ENDC}")

        print(f"   ↳ Total de candidatos válidos: {len(candidates)}")

        # Validação de links
        valid_candidates = []
        
        if candidates:
            print(f"   ↳ Validando {len(candidates)} links...")
            
            for idx, r in enumerate(candidates[:15], 1):  # Aumentado para 15
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                    resp = requests.head(r["href"], headers=headers, timeout=5, allow_redirects=True)
                    
                    if resp.status_code < 400:
                        valid_candidates.append(r)
                        print(f"   [{idx}] ✓ {r['title'][:60]}...")
                    else:
                        print(f"   [{idx}] ✗ Status {resp.status_code}")
                except Exception as e:
                    continue

            print(f"   ↳ {Colors.GREEN}{len(valid_candidates)} notícias válidas{Colors.ENDC}")

        # Se não encontrou nada, busca genérica
        if not valid_candidates:
            print(f"   {Colors.WARNING}⚠️ Buscando de forma mais ampla...{Colors.ENDC}")
            try:
                with DDGS() as ddgs:
                    emergency = list(ddgs.text(f"{company} notícia mercado", region="br-pt", max_results=10))
                    
                    for r in emergency:
                        url = r.get("href", "")
                        # Aplica os mesmos filtros
                        blocklist = ["/cotacoes/", "/cotacao/", "/acoes/", "statusinvest", "investidor10"]
                        if any(b in url.lower() for b in blocklist):
                            continue
                        
                        try:
                            headers = {"User-Agent": "Mozilla/5.0"}
                            resp = requests.head(url, headers=headers, timeout=3, allow_redirects=True)
                            if resp.status_code < 400:
                                valid_candidates.append(r)
                                if len(valid_candidates) >= 5:
                                    break
                        except:
                            continue
                    
                    print(f"   ↳ Busca ampla: {len(valid_candidates)} válidos")
            except:
                pass

        if valid_candidates:
            # Curadoria com IA
            if "GEMINI_API_KEY" in os.environ:
                print(f"   ↳ {Colors.CYAN}🧠 IA selecionando as 3 melhores...{Colors.ENDC}")
                
                keys = os.environ["GEMINI_API_KEY"].split(",")
                curated_news = ""
                
                for k_idx, key in enumerate(keys):
                    key = key.strip()
                    if not key:
                        continue

                    try:
                        llm = ChatGoogleGenerativeAI(
                            model="gemini-2.5-flash",
                            temperature=0.1,
                            google_api_key=key,
                        )

                        news_feed = "\n\n".join([
                            f"ID {i + 1}:\nTítulo: {n['title']}\nLink: {n['href']}\nResumo: {n['body'][:200]}"
                            for i, n in enumerate(valid_candidates)
                        ])

                        prompt = f"""Você é Editor de Investment Banking. Selecione as 3 MELHORES notícias sobre: {company}.

LISTA:
{news_feed}

CRITÉRIOS:
- Priorize: Resultados financeiros, dividendos, análises, M&A
- IGNORE: Páginas de cotação, tutoriais, cursos
- Retorne EXATAMENTE 3 itens

FORMATO OBRIGATÓRIO (Markdown):
* **[Título da Notícia](URL completa)**
  > Resumo executivo em 1-2 linhas sobre o impacto.

REGRA: Mantenha os links COMPLETOS sem alteração."""

                        res = llm.invoke([HumanMessage(content=prompt)])
                        curated_news = res.content.strip()
                        
                        # Valida que tem 3 itens
                        if curated_news.count("**[") >= 3:
                            print(f"   {Colors.GREEN}✓ IA selecionou 3 notícias{Colors.ENDC}")
                            break
                        else:
                            print(f"   ⚠️ IA retornou {curated_news.count('**[')} itens, tentando novamente...")
                            continue
                            
                    except Exception as e:
                        print(f"   ✗ Erro chave #{k_idx + 1}")
                        continue

                if curated_news and "**[" in curated_news:
                    news = curated_news
                else:
                    # Fallback mecânico
                    print(f"   {Colors.WARNING}⚠️ Fallback: Top 3 automático{Colors.ENDC}")
                    news_list = []
                    for r in valid_candidates[:3]:
                        title = r["title"].split(" - ")[0].split(" | ")[0][:80]
                        snippet = r.get("body", "Sem descrição")[:120]
                        news_list.append(f"* **[{title}]({r['href']})**\n  > {snippet}...")
                    news = "\n\n".join(news_list)
            else:
                # Sem IA
                print(f"   {Colors.WARNING}⚠️ Sem IA: Top 3 automático{Colors.ENDC}")
                news_list = []
                for r in valid_candidates[:3]:
                    title = r["title"].split(" - ")[0][:80]
                    snippet = r.get("body", "")[:120]
                    news_list.append(f"* **[{title}]({r['href']})**\n  > {snippet}...")
                news = "\n\n".join(news_list)
        else:
            news = "⚠️ Nenhuma notícia recente encontrada nos portais financeiros monitorados."
            print(f"   {Colors.FAIL}❌ Nenhuma notícia válida{Colors.ENDC}")

        print(f"   ↳ {Colors.GREEN}Pesquisa concluída{Colors.ENDC}")
        
    except Exception as e:
        summary = "Erro na coleta."
        news = f"⚠️ Erro: {str(e)}"
        print(f"   {Colors.FAIL}❌ Erro crítico: {str(e)}{Colors.ENDC}")
    
    return {"summary_data": summary, "news_data": news}
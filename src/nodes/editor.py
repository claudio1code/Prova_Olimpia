import os
import time

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import Colors
from ..state import ResearchState


def node_editor(state: ResearchState):
    # Cor AMARELA para o Editor
    print(f"{Colors.WARNING}✍️  [Editor]{Colors.ENDC} Gerando relatório...")

    def make_fallback(reason="Template Automático"):
        return f"""# 🏛️ Equity Research: {state["company_name"].upper()}

{state["stock_data"]}

## 🏢 Perfil Corporativo
{state["summary_data"]}

## 📰 Notícias Recentes
{state["news_data"]}

---
*Relatório gerado via {reason} (Dados reais coletados)*"""

    # Verifica se estamos em MOCK MODE (sem chave definida)
    if "GEMINI_API_KEY" not in os.environ:
        time.sleep(1.5)
        print(
            f"   {Colors.GREEN}⚠️  Modo MOCK: Gerando relatório com dados reais.{Colors.ENDC}"
        )
        return {"final_report": make_fallback("Modo Mock")}

    MODELO = "gemini-2.5-flash"

    # Rotação de chaves
    keys = os.environ["GEMINI_API_KEY"].split(",")

    for k_idx, key in enumerate(keys):
        key = key.strip()
        if not key:
            continue

        print(f"   🔑 Tentando API Key #{k_idx + 1}...")

        try:
            llm = ChatGoogleGenerativeAI(
                model=MODELO,
                temperature=0.1,
                google_api_key=key,
            )

            prompt = f"""
            Analista Sênior de Investment Banking. Gere um relatório executivo sobre: {state["company_name"]} ({state["ticker"]}).

            INPUTS:
            [DASHBOARD FINANCEIRO]:
            {state["stock_data"]}

            [RESUMO]:
            {state["summary_data"]}

            [NOTÍCIAS]:
            {state["news_data"]}

            OUTPUT OBRIGATÓRIO (MARKDOWN):
            # 🏛️ Equity Research: {state["company_name"].upper()}

            {state["stock_data"]}

            ## 🏢 Perfil Corporativo
            (Escreva um parágrafo sólido e profissional sobre o negócio da empresa, focado em investidores).

            ## 📰 Notícias Recentes
            (Liste as 3 notícias mais relevantes. Use Citação '>' para o resumo).

            * **[Título da Notícia](Link)**
              > Resumo do impacto ou fato relevante contido na notícia.

            ---
            *Relatório gerado por AI (Olimpia Agent).*
            """

            try:
                res = llm.invoke([HumanMessage(content=prompt)])
                return {"final_report": res.content}
            except Exception as e:
                print(f"      ❌ Erro na Key #{k_idx + 1}: {str(e)[:100]}...")
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    continue  # Tenta próxima chave
                else:
                    break  # Erro fatal
        except:
            pass

    print(f"{Colors.FAIL}⚠️ Todas as chaves falharam. Usando Fallback.{Colors.ENDC}")
    return {"final_report": make_fallback("Fallback (Todas as chaves esgotadas)")}

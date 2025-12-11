import datetime
import math

import yfinance as yf

from ..config import Colors
from ..state import ResearchState
from ..utils import suppress_stdout_stderr


def node_market_analyst(state: ResearchState):
    ticker = state["ticker"]
    # Cor MAGENTA para Mercado
    print(f"{Colors.HEADER}📊 [Market Analyst]{Colors.ENDC} Cotando ativo: {ticker}...")

    stock_data_str = "Dados Indisponíveis"
    with suppress_stdout_stderr():
        try:
            stock = yf.Ticker(ticker)

            # Coleta dados históricos HÍBRIDOS (Nominal e Ajustado)
            # 1. Nominal: Para Min/Max de tela (sem descontar dividendos)
            hist_nominal = stock.history(period="1y", auto_adjust=False)
            # 2. Ajustado: Para cálculo de Rentabilidade Real (com dividendos)
            hist_adjusted = stock.history(period="1y", auto_adjust=True)

            # Preço Atual (Nominal)
            price = stock.fast_info.last_price
            if not price and not hist_nominal.empty:
                price = hist_nominal["Close"].iloc[-1]

            # Cálculos Estatísticos
            if not hist_nominal.empty:
                # MÍNIMA/MÁXIMA (Usa Nominal - Preço de Tela)
                clean_hist = hist_nominal[hist_nominal["Low"] > 0.01]
                if clean_hist.empty:
                    clean_hist = hist_nominal

                low52 = clean_hist["Low"].min()
                high52 = clean_hist["High"].max()

                # VARIAÇÃO 12M (Usa Ajustado - Retorno Total)
                if not hist_adjusted.empty:
                    start_adj = hist_adjusted["Close"].iloc[0]
                    end_adj = hist_adjusted["Close"].iloc[-1]
                    chg52 = (end_adj - start_adj) / start_adj if start_adj else 0
                else:
                    chg52 = 0

                # Dividend Yield (Prioridade: Info da API > Cálculo Manual)
                div_yield = 0

                # 1. Tenta pegar do .info
                try:
                    info_dy = stock.info.get("dividendYield")
                    if info_dy is not None:
                        div_yield = info_dy
                except:
                    pass

                # 2. Se falhou ou veio zerado/estranho, calcula na mão (Soma 12m)
                if not div_yield:
                    try:
                        dividends = stock.dividends
                        if not dividends.empty:
                            # Remove timezone para evitar erros de compatibilidade
                            dividends.index = dividends.index.tz_localize(None)
                            cutoff = datetime.datetime.now() - datetime.timedelta(
                                days=365
                            )
                            last_year_divs = dividends[dividends.index >= cutoff]
                            div_yield = last_year_divs.sum() / price if price else 0
                    except:
                        pass
            else:
                # Fallback se não tiver histórico
                info = stock.info
                price = info.get("currentPrice") or info.get("regularMarketPrice")
                low52 = info.get("fiftyTwoWeekLow")
                high52 = info.get("fiftyTwoWeekHigh")
                div_yield = info.get("dividendYield")
                chg52 = info.get("52WeekChange")

            # Filtros de sanidade
            if div_yield and div_yield < 0:
                div_yield = None
            if low52 and low52 <= 0.01:
                low52 = None

            def fmt(val, prefix="", suffix="", mult=1):
                if (
                    val is None
                    or val == "-"
                    or (isinstance(val, float) and math.isnan(val))
                ):
                    return "N/A"
                return f"{prefix}{val * mult:.2f}{suffix}"

            current = fmt(price, prefix="R$ ")
            min_52 = fmt(low52, prefix="R$ ")
            max_52 = fmt(high52, prefix="R$ ")
            # Ajuste de escala: Se > 0.6, assumimos que já é porcentagem (ex: 11.45)
            dy_mult = 100
            if div_yield and div_yield > 0.6:
                dy_mult = 1
            dy = fmt(div_yield, suffix="%", mult=dy_mult)
            var_12m = fmt(chg52, suffix="%", mult=100)

            # Dashboard Alinhado (ASCII Art Clean)
            stock_data_str = (
                f"┌{'─' * 14}┬{'─' * 14}┬{'─' * 14}┬{'─' * 14}┬{'─' * 14}┐\n"
                f"│ {'PREÇO ATUAL':^12} │ {'MIN 52 SEM':^12} │ {'MAX 52 SEM':^12} │ {'DIV. YIELD':^12} │ {'VAR. 12M':^12} │\n"
                f"├{'─' * 14}┼{'─' * 14}┼{'─' * 14}┼{'─' * 14}┼{'─' * 14}┤\n"
                f"│ {current:^12} │ {min_52:^12} │ {max_52:^12} │ {dy:^12} │ {var_12m:^12} │\n"
                f"└{'─' * 14}┴{'─' * 14}┴{'─' * 14}┴{'─' * 14}┴{'─' * 14}┘"
            )

        except Exception:
            pass

    if "PREÇO" in stock_data_str:
        print(
            f"   ↳ {Colors.GREEN}Métricas financeiras coletadas (Dashboard).{Colors.ENDC}"
        )
    else:
        print(f"   ↳ {Colors.WARNING}Aviso: Cotação indisponível.{Colors.ENDC}")
    return {"stock_data": stock_data_str}

import yfinance as yf
from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field

# --- Mapeamento de Empresas Brasileiras para Tickers (simplificado) ---
# Você pode expandir esta lista conforme a necessidade
TICKER_MAP = {
    "PETROBRAS": "PETR4.SA",
    "VALE": "VALE3.SA",
    "ITAÚ": "ITUB4.SA",
    "MINERVA": "BEEF3.SA",
    "AMBEV": "ABEV3.SA",
    # Adicione mais conforme os exemplos da prova:
    "PETROBRAS": "PETR4.SA", # Já incluído, mas para referência
    "VALE": "VALE3.SA",     # Já incluído
    "ITAU": "ITUB4.SA",      # Adicionei a variação sem acento
    "BB": "BBAS3.SA",
    "BRADESCO": "BBDC4.SA"
}

# --- 1. Definir o Schema de Entrada (Pydantic) ---
class StockPriceToolInput(BaseModel):
    """Schema de entrada para a StockPriceTool."""
    company_name: str = Field(description="O nome da empresa (ex: 'Petrobras', 'Vale').")


# --- 2. Criar a Custom Tool (BaseTool) ---
class StockPriceTool(BaseTool):
    """
    Ferramenta para obter o preço atual da ação de empresas brasileiras...
    """
    name: str = "stock_price_checker"
    description: str = (
        "Útil para encontrar o valor atual ou de fechamento mais recente da ação "
        "de uma empresa brasileira de capital aberto. "
        "A entrada deve ser o NOME da empresa, ex: 'Petrobras'."
    )
    # A classe de input que o LangChain espera deve ser o seu próprio schema
    # Pydantic (StockPriceToolInput)
    args_schema: Type[StockPriceToolInput] = StockPriceToolInput

    def _run(self, company_name: str) -> str:
        """Use a ferramenta de forma síncrona."""
        
        # 1. Normalizar a entrada (para ignorar caixa e acentos simples)
        normalized_name = company_name.upper().replace("Ú", "U").replace("Ã", "A")

        ticker = TICKER_MAP.get(normalized_name)

        if not ticker:
            return f"Erro: Ticker para a empresa '{company_name}' não encontrado no mapeamento."

        try:
            stock = yf.Ticker(ticker)
            # Obter os dados mais recentes (geralmente o preço de fechamento de hoje ou de ontem)
            data = stock.history(period="1d") 
            
            if data.empty:
                 # Tenta buscar o preço atual/último
                 info = stock.info
                 price = info.get('currentPrice') or info.get('regularMarketPrice')
                 if price:
                     return f"Ticker: {ticker}. Preço Atual/Mercado: R$ {price:.2f}"
                 else:
                     return f"Erro: Não foi possível obter dados de preço para o ticker {ticker}."
            
            # Se a data history retornar dados, usa o preço de fechamento
            last_close = data['Close'].iloc[-1]
            return f"Ticker: {ticker}. Preço de Fechamento Mais Recente: R$ {last_close:.2f}"

        except Exception as e:
            return f"Erro ao consultar yfinance para {ticker}: {e}"

    def _arun(self, company_name: str) -> str:
        """Use a ferramenta de forma assíncrona (não implementado para este exemplo)."""
        raise NotImplementedError("Esta ferramenta não suporta execução assíncrona.")
		


		teste
		
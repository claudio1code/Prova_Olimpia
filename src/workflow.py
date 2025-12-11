from langgraph.graph import END, StateGraph

from .nodes.editor import node_editor
from .nodes.market import node_market_analyst
from .nodes.researcher import node_researcher
from .nodes.ticker import node_ticker_finder
from .state import ResearchState

# --- DEFINIÇÃO DO GRAFO ---
workflow = StateGraph(ResearchState)

# Adiciona os nós (Agentes)
workflow.add_node("TickerFinder", node_ticker_finder)
workflow.add_node("Researcher", node_researcher)
workflow.add_node("MarketAnalyst", node_market_analyst)
workflow.add_node("Editor", node_editor)

# Define o fluxo de execução (Pipeline Linear)
workflow.set_entry_point("TickerFinder")
workflow.add_edge("TickerFinder", "Researcher")
workflow.add_edge("Researcher", "MarketAnalyst")
workflow.add_edge("MarketAnalyst", "Editor")
workflow.add_edge("Editor", END)

# Compila a aplicação pronta para execução
app = workflow.compile()

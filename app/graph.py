from langgraph.graph import StateGraph, END
from app.state import AgentState
from app.nodes import scrape_node, summarize_node, save_node, error_node


def route_after_scrape(state: AgentState) -> str:
    return "error" if state.get("error") else "summarize"


def route_after_summarize(state: AgentState) -> str:
    return "error" if state.get("error") else "save"


def build_graph():
    """Builds and compiles the LangGraph pipeline: scrape -> summarize
    -> save, with conditional routing to an error node if any stage
    fails."""
    graph = StateGraph(AgentState)

    graph.add_node("scrape", scrape_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("save", save_node)
    graph.add_node("error", error_node)

    graph.set_entry_point("scrape")

    graph.add_conditional_edges(
        "scrape", route_after_scrape, {"summarize": "summarize", "error": "error"}
    )
    graph.add_conditional_edges(
        "summarize", route_after_summarize, {"save": "save", "error": "error"}
    )

    graph.add_edge("save", END)
    graph.add_edge("error", END)

    return graph.compile()
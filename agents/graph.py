"""LangGraph pipeline: compute → safety → build_prompt."""
from langgraph.graph import END, StateGraph
from agents.nodes import build_prompt_node, compute_metrics_node, safety_check_node
from agents.state import AHAAState


def _create_graph():
    g = StateGraph(AHAAState)
    g.add_node("compute_metrics", compute_metrics_node)
    g.add_node("safety_check", safety_check_node)
    g.add_node("build_prompt", build_prompt_node)

    g.set_entry_point("compute_metrics")
    g.add_edge("compute_metrics", "safety_check")
    g.add_edge("safety_check", "build_prompt")
    g.add_edge("build_prompt", END)

    return g.compile()


ahaa_graph = _create_graph()

"""LangGraph StateGraph: assembles all workflow nodes into a pipeline."""
from langgraph.graph import StateGraph, START, END
from src.workflow.state import PipelineState
from src.workflow.nodes.load_resources import load_resources
from src.workflow.nodes.web_search import web_search
from src.workflow.nodes.compute_strength import compute_strength
from src.workflow.nodes.generate_solution import generate_solution
from src.workflow.nodes.score_resources import score_resources
from src.workflow.nodes.generate_report import generate_report

_cached_graph = None


def build_pipeline():
    """Build and compile the LangGraph pipeline (cached).

    Pipeline:
        Load Resources → Web Search → Compute Strength
        → Generate Solution → Score Resources → Generate Report

    Returns:
        A compiled StateGraph ready for .invoke().
    """
    global _cached_graph
    if _cached_graph is not None:
        return _cached_graph

    graph = StateGraph(PipelineState)
    graph.add_node("load_resources", load_resources)
    graph.add_node("web_search", web_search)
    graph.add_node("compute_strength", compute_strength)
    graph.add_node("generate_solution", generate_solution)
    graph.add_node("score_resources", score_resources)
    graph.add_node("generate_report", generate_report)

    graph.add_edge(START, "load_resources")
    graph.add_edge("load_resources", "web_search")
    graph.add_edge("web_search", "compute_strength")
    graph.add_edge("compute_strength", "generate_solution")
    graph.add_edge("generate_solution", "score_resources")
    graph.add_edge("score_resources", "generate_report")
    graph.add_edge("generate_report", END)

    _cached_graph = graph.compile()
    return _cached_graph

"""Tests for Node 2: Web Search + LLM Skill Extraction."""
import src.workflow.nodes.web_search as web_search_node
from src.workflow.nodes.web_search import web_search


def test_web_search_returns_required_skills():
    state = {"problem_statement": "Build a legal AI platform"}
    result = web_search(state)
    assert "search_results" in result
    sr = result["search_results"]
    assert "required_skills" in sr
    assert isinstance(sr["required_skills"], list)
    assert len(sr["required_skills"]) > 0
    assert "search_context" in sr
    assert "difficulty" in sr


def test_web_search_mock_has_known_skills():
    """In TESTING mode, mock returns predictable skill list."""
    state = {"problem_statement": "Build a legal AI platform"}
    result = web_search(state)
    skills = result["search_results"]["required_skills"]
    assert "Python" in skills
    assert "AWS" in skills


def test_web_search_live_fallback_extracts_query_skills(monkeypatch):
    """Live mode extracts baseline skills if LLM extraction fails."""
    monkeypatch.setenv("env", "LOCAL")
    monkeypatch.setattr(
        web_search_node,
        "tavily_search",
        lambda _query: {"results": []},
    )
    monkeypatch.setattr(
        web_search_node,
        "_llm_extract_skills",
        lambda *_args: web_search_node._fallback_extract_skills(*_args),
    )
    state = {
        "problem_statement": (
            "Build a LlamaIndex and LangGraph streaming visualization app "
            "with input and output guardrails"
        )
    }
    result = web_search(state)
    skills = result["search_results"]["required_skills"]
    assert "LangGraph" in skills
    assert "LlamaIndex" in skills
    assert "Guardrails" in skills

"""Tests for the pipeline state type definition."""
from src.workflow.state import PipelineState


def test_state_keys_are_defined():
    """PipelineState should declare all expected keys."""
    annotations = PipelineState.__annotations__
    assert "problem_statement" in annotations
    assert "users" in annotations
    assert "skills" in annotations
    assert "levels" in annotations
    assert "user_skills" in annotations
    assert "search_results" in annotations
    assert "skill_strength_scores" in annotations
    assert "generic_solution" in annotations
    assert "ranked_resources" in annotations
    assert "report_bytes" in annotations


def test_state_works_as_plain_dict():
    """State is used as a dict at runtime, not a class instance."""
    state: PipelineState = {
        "problem_statement": "Build a legal AI platform",
        "users": [],
        "skills": [],
        "levels": [],
        "user_skills": [],
        "search_results": {},
        "skill_strength_scores": [],
        "generic_solution": [],
        "ranked_resources": [],
        "report_bytes": None,
    }
    assert state["problem_statement"] == "Build a legal AI platform"
    assert state["users"] == []
    assert state["report_bytes"] is None

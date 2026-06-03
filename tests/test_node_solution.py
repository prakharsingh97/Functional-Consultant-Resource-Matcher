"""Tests for Node 4: Generate Skill-Biased Generic Solution."""
import src.workflow.nodes.generate_solution as solution_node
from src.workflow.nodes.generate_solution import generate_solution


def test_generate_solution_mock():
    state = {
        "problem_statement": "Build a legal AI platform",
        "skill_strength_scores": [
            {"skill_name": "Python", "strength_score": 7.25},
            {"skill_name": "AWS", "strength_score": 6.50},
        ],
    }
    result = generate_solution(state)
    assert "generic_solution" in result
    assert len(result["generic_solution"]) > 0


def test_solution_steps_have_required_fields():
    state = {
        "problem_statement": "Build a legal AI platform",
        "skill_strength_scores": [
            {"skill_name": "Python", "strength_score": 7.25},
        ],
    }
    result = generate_solution(state)
    for step in result["generic_solution"]:
        assert "step" in step
        assert "action" in step
        assert "technology" in step
        assert "skill_strength_score" in step


def test_generate_solution_falls_back_when_live_llm_fails(monkeypatch):
    """Live mode still returns useful steps if the model call fails."""
    monkeypatch.setenv("env", "LOCAL")

    def fail_solution(*_args, **_kwargs):
        raise RuntimeError("model failed")

    monkeypatch.setattr(
        solution_node, "_call_llm_for_solution", fail_solution,
    )
    state = {
        "problem_statement": "Build conversational insights with agents",
        "skill_strength_scores": [
            {"skill_name": "Python", "strength_score": 7.25},
            {"skill_name": "LangGraph", "strength_score": 6.50},
        ],
    }
    result = generate_solution(state)
    assert len(result["generic_solution"]) >= 5
    assert "guardrails" in result["generic_solution"][-1]["action"].lower()

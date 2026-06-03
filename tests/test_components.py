"""Tests for UI component helper functions."""
from src.ui.components import (
    WORKFLOW_STEPS, format_resource_card, format_solution_step,
    format_task_recommendation,
)


def test_workflow_steps_defined():
    assert len(WORKFLOW_STEPS) == 5
    assert WORKFLOW_STEPS[0]["icon"] == "🔄"
    assert WORKFLOW_STEPS[-1]["icon"] == "✅"
    assert "gathering" in WORKFLOW_STEPS[0]["key"]
    assert "finalizing" in WORKFLOW_STEPS[-1]["key"]


def test_format_solution_step():
    step = {
        "step": 1, "action": "Deploy API",
        "technology": "AWS", "skill_strength_score": 6.5,
    }
    result = format_solution_step(step)
    assert "AWS" in result
    assert "6.5" in result
    assert "Step 1" in result


def test_format_resource_card():
    resource = {
        "full_name": "Alice Chen", "fit_score": 0.85,
        "priority": "P1", "availability": 35,
    }
    result = format_resource_card(resource)
    assert "Alice Chen" in result
    assert "P1" in result
    assert "0.85" in result


def test_format_task_recommendation():
    task = {
        "task_id": 1,
        "task": "Build streaming backend",
        "required_skills": ["Python", "FastAPI"],
        "strength_score": 4.2,
        "resources": [
            {"full_name": "Alice", "fit_score": 0.91,
             "availability": 30, "recommendation": "Primary"},
        ],
    }
    result = format_task_recommendation(task)
    assert "Build streaming backend" in result
    assert "Python, FastAPI" in result
    assert "Alice" in result
    assert "fit 0.91" in result

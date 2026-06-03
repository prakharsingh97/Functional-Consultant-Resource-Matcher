"""Tests for Node 6: Generate .docx report."""
from src.workflow.nodes.generate_report import generate_report


def test_generate_report_produces_bytes():
    state = {
        "problem_statement": "Build a legal AI platform",
        "generic_solution": [
            {"step": 1, "action": "Deploy API",
             "technology": "AWS", "skill_strength_score": 6.50},
        ],
        "ranked_resources": [
            {"user_id": "U01", "full_name": "Alice",
             "fit_score": 0.85, "priority": "P1",
             "availability": 30, "risk_flag": False},
        ],
        "skill_strength_scores": [
            {"skill_name": "AWS", "strength_score": 6.50},
        ],
    }
    result = generate_report(state)
    assert "report_bytes" in result
    assert isinstance(result["report_bytes"], bytes)
    assert len(result["report_bytes"]) > 100

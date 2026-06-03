"""Tests for Node 3: Compute Skill Strength Scores (semantic)."""
from src.workflow.nodes.compute_strength import compute_strength


def test_compute_strength_scores():
    state = {
        "skills": [
            {"skill_id": "SK01", "skill_name": "Python",
             "category": "Engineering"},
            {"skill_id": "SK02", "skill_name": "AWS",
             "category": "Cloud"},
        ],
        "levels": [
            {"level_id": 1, "score_weight": 0.25},
            {"level_id": 2, "score_weight": 0.50},
            {"level_id": 3, "score_weight": 0.75},
            {"level_id": 4, "score_weight": 1.00},
        ],
        "user_skills": [
            {"user_id": "U01", "skill_id": "SK01", "level_id": 3},
            {"user_id": "U02", "skill_id": "SK01", "level_id": 4},
            {"user_id": "U01", "skill_id": "SK02", "level_id": 3},
        ],
        "search_results": {
            "required_skills": ["Python", "AWS"],
        },
    }
    result = compute_strength(state)
    scores = result["skill_strength_scores"]
    assert len(scores) >= 2
    # Python matched with sim ~0.95, strength > 0
    python = next(s for s in scores if s["skill_name"] == "Python")
    assert python["strength_score"] > 0
    # Sorted descending
    assert scores[0]["strength_score"] >= scores[1]["strength_score"]

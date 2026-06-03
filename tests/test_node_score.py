"""Tests for Node 5: Score, rank, and flag resources (semantic)."""
from src.workflow.nodes.score_resources import score_resources


def test_score_resources_ranks_by_fit():
    state = {
        "users": [
            {"user_id": "U01", "full_name": "Alice",
             "availability": 30},
            {"user_id": "U02", "full_name": "Bob",
             "availability": 10},
        ],
        "levels": [
            {"level_id": 1, "score_weight": 0.25},
            {"level_id": 3, "score_weight": 0.75},
            {"level_id": 4, "score_weight": 1.00},
        ],
        "user_skills": [
            {"user_id": "U01", "skill_id": "SK01", "level_id": 4},
            {"user_id": "U01", "skill_id": "SK02", "level_id": 3},
            {"user_id": "U02", "skill_id": "SK01", "level_id": 1},
        ],
        "skills": [
            {"skill_id": "SK01", "skill_name": "Python"},
            {"skill_id": "SK02", "skill_name": "AWS"},
        ],
        "search_results": {
            "required_skills": ["Python", "AWS"],
        },
        "skill_strength_scores": [],
        "generic_solution": [],
    }
    result = score_resources(state)
    ranked = result["ranked_resources"]
    assert len(ranked) == 2
    # Alice ranked first (higher fit)
    assert ranked[0]["full_name"] == "Alice"
    assert ranked[0]["fit_score"] > ranked[1]["fit_score"]


def test_low_availability_gets_risky_flag():
    state = {
        "users": [
            {"user_id": "U01", "full_name": "Alice",
             "availability": 5},
        ],
        "levels": [{"level_id": 3, "score_weight": 0.75}],
        "user_skills": [
            {"user_id": "U01", "skill_id": "SK01", "level_id": 3},
        ],
        "skills": [
            {"skill_id": "SK01", "skill_name": "Python"},
        ],
        "search_results": {
            "required_skills": ["Python"],
        },
        "skill_strength_scores": [],
        "generic_solution": [],
    }
    result = score_resources(state)
    res = result["ranked_resources"][0]
    assert res["risk_flag"] is True
    assert "P3" in res["priority"]


def test_fit_score_is_normalized():
    """Fit score should be between 0 and 1."""
    state = {
        "users": [
            {"user_id": "U01", "full_name": "Expert",
             "availability": 40},
        ],
        "levels": [{"level_id": 4, "score_weight": 1.00}],
        "user_skills": [
            {"user_id": "U01", "skill_id": "SK01", "level_id": 4},
        ],
        "skills": [
            {"skill_id": "SK01", "skill_name": "Python"},
        ],
        "search_results": {
            "required_skills": ["Python"],
        },
        "skill_strength_scores": [],
        "generic_solution": [],
    }
    result = score_resources(state)
    fit = result["ranked_resources"][0]["fit_score"]
    assert 0.0 <= fit <= 1.0


def test_score_resources_builds_task_recommendations():
    """Task recommendations should staff each solution step."""
    state = {
        "users": [
            {"user_id": "U01", "full_name": "Alice",
             "role": "Engineer", "availability": 30},
            {"user_id": "U02", "full_name": "Bob",
             "role": "QA", "availability": 20},
        ],
        "levels": [
            {"level_id": 3, "score_weight": 0.75},
            {"level_id": 4, "score_weight": 1.00},
        ],
        "user_skills": [
            {"user_id": "U01", "skill_id": "SK01", "level_id": 4},
            {"user_id": "U02", "skill_id": "SK02", "level_id": 4},
        ],
        "skills": [
            {"skill_id": "SK01", "skill_name": "Python"},
            {"skill_id": "SK02", "skill_name": "QA"},
        ],
        "search_results": {
            "required_skills": ["Python", "QA"],
        },
        "skill_strength_scores": [
            {"skill_name": "Python", "strength_score": 2.5},
            {"skill_name": "QA", "strength_score": 1.5},
        ],
        "generic_solution": [
            {"step": 1, "action": "Build backend", "technology": "Python"},
            {"step": 2, "action": "Test release", "technology": "QA"},
        ],
    }
    result = score_resources(state)
    tasks = result["task_recommendations"]
    assert len(tasks) == 2
    assert tasks[0]["resources"][0]["recommendation"] == "Primary"
    assert "P3" not in str(tasks)
    assert "P4" not in str(tasks)

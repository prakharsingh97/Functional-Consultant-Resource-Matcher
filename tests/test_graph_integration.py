"""Integration test: full LangGraph pipeline run with mocks."""
import pytest
from src.workflow.graph import build_pipeline
from src.db import excel_db


@pytest.fixture(autouse=True)
def mock_env_and_db(
    sample_users_df, sample_skills_df,
    sample_levels_df, sample_user_skills_df, monkeypatch,
):
    monkeypatch.setenv("env", "TESTING")
    excel_db._sheets_cache = {
        "users": sample_users_df,
        "skills": sample_skills_df,
        "levels": sample_levels_df,
        "user_skills": sample_user_skills_df,
    }
    yield
    excel_db._sheets_cache = {}


def test_full_pipeline_returns_report():
    graph = build_pipeline()
    result = graph.invoke(
        {"problem_statement": "Build a legal AI platform"}
    )
    assert "users" in result
    assert "search_results" in result
    assert "skill_strength_scores" in result
    assert "generic_solution" in result
    assert "ranked_resources" in result
    assert "task_recommendations" in result
    assert "report_bytes" in result
    assert len(result["task_recommendations"]) > 0
    assert isinstance(result["report_bytes"], bytes)
    assert len(result["report_bytes"]) > 100


def test_pipeline_ranks_resources():
    graph = build_pipeline()
    result = graph.invoke(
        {"problem_statement": "Build a legal AI platform"}
    )
    ranked = result["ranked_resources"]
    assert len(ranked) > 0
    # Sorted descending by fit_score
    for i in range(len(ranked) - 1):
        assert ranked[i]["fit_score"] >= ranked[i + 1]["fit_score"]

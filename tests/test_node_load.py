"""Tests for Node 1: Load Resources from Excel."""
from src.workflow.nodes.load_resources import load_resources
from src.db import excel_db


def test_load_resources_populates_state(
    sample_users_df, sample_skills_df,
    sample_levels_df, sample_user_skills_df,
):
    excel_db._sheets_cache = {
        "users": sample_users_df,
        "skills": sample_skills_df,
        "levels": sample_levels_df,
        "user_skills": sample_user_skills_df,
    }
    state = {"problem_statement": "Build a legal AI platform"}
    result = load_resources(state)
    assert len(result["users"]) == 3
    assert len(result["skills"]) == 4
    assert len(result["levels"]) == 4
    assert len(result["user_skills"]) == 5

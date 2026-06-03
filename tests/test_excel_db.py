"""Tests for Excel data access functions."""
import pytest
from src.db.excel_db import (
    load_sheet, get_all_users, get_user_by_id,
    get_all_skills, get_skill_strength_scores,
    get_all_levels, get_all_user_skills,
    get_user_skills_enriched, create_user, delete_user,
)


@pytest.fixture
def mock_db(monkeypatch, sample_users_df, sample_skills_df,
            sample_levels_df, sample_user_skills_df):
    """Patch _load_db to return mock DataFrames."""
    sheets = {
        "users": sample_users_df,
        "skills": sample_skills_df,
        "levels": sample_levels_df,
        "user_skills": sample_user_skills_df,
    }
    monkeypatch.setattr("src.db.excel_db._sheets_cache", sheets)
    return sheets


def test_get_all_users_returns_all(mock_db):
    users = get_all_users()
    assert len(users) == 3
    assert users[0]["full_name"] == "Alice Chen"


def test_get_user_by_id_found(mock_db):
    user = get_user_by_id("U01")
    assert user is not None
    assert user["email"] == "alice@example.com"


def test_get_user_by_id_not_found(mock_db):
    user = get_user_by_id("U99")
    assert user is None


def test_get_all_skills_returns_all(mock_db):
    skills = get_all_skills()
    assert len(skills) == 4


def test_get_all_levels_returns_all(mock_db):
    levels = get_all_levels()
    assert len(levels) == 4
    assert levels[0]["score_weight"] == 0.25


def test_get_all_user_skills_returns_all(mock_db):
    user_skills = get_all_user_skills()
    assert len(user_skills) == 5


def test_get_skill_strength_scores(mock_db):
    scores = get_skill_strength_scores()
    # Python (SK01): U01 Advanced(0.75) + U02 Advanced(0.75) = 1.50
    python_score = next(s for s in scores if s["skill_id"] == "SK01")
    assert python_score["strength_score"] == 1.50
    # AWS (SK02): U01 Expert(1.00) + U03 Advanced(0.75) = 1.75
    aws_score = next(s for s in scores if s["skill_id"] == "SK02")
    assert aws_score["strength_score"] == 1.75


def test_get_user_skills_enriched(mock_db):
    result = get_user_skills_enriched("U01")
    assert result["user"]["user_id"] == "U01"
    assert len(result["skills"]) == 2


def test_create_user(mock_db):
    new_user = create_user({
        "full_name": "Dave Park",
        "email": "dave@example.com",
        "role": "Consultant",
        "availability": 25,
        "timezone": "US/Pacific",
    })
    assert new_user["full_name"] == "Dave Park"
    assert new_user["user_id"]


def test_delete_user(mock_db):
    result = delete_user("U01")
    assert result is True
    assert get_user_by_id("U01") is None

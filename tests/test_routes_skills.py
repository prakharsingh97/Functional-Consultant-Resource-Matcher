"""Tests for /v1/skills and /v1/skills/strength endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.db import excel_db


@pytest.fixture
def client():
    from src.api.app import create_app
    return TestClient(create_app())


@pytest.fixture(autouse=True)
def mock_db(sample_users_df, sample_skills_df,
            sample_levels_df, sample_user_skills_df):
    excel_db._sheets_cache = {
        "users": sample_users_df,
        "skills": sample_skills_df,
        "levels": sample_levels_df,
        "user_skills": sample_user_skills_df,
    }
    yield
    excel_db._sheets_cache = {}


def test_get_all_skills(client):
    resp = client.get("/v1/skills")
    assert resp.status_code == 200
    assert len(resp.json()) == 4


def test_get_skill_strength(client):
    resp = client.get("/v1/skills/strength")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    # Scores should be sorted descending
    assert data[0]["strength_score"] >= data[-1]["strength_score"]

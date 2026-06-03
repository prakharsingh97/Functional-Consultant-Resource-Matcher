"""Tests for /v1/user-skills endpoints."""
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


def test_get_all_user_skills(client):
    resp = client.get("/v1/user-skills")
    assert resp.status_code == 200
    assert len(resp.json()) == 5

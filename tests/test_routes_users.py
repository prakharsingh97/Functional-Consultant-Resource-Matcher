"""Tests for /v1/users endpoints."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Test client with mock data layer."""
    from src.api.app import create_app
    app = create_app()
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_db(sample_users_df, sample_skills_df,
            sample_levels_df, sample_user_skills_df):
    """Patch the data layer with in-memory mock data."""
    from src.db import excel_db
    excel_db._sheets_cache = {
        "users": sample_users_df,
        "skills": sample_skills_df,
        "levels": sample_levels_df,
        "user_skills": sample_user_skills_df,
    }
    yield
    excel_db._sheets_cache = {}


def test_read_all_users(client):
    resp = client.get("/v1/users")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3


def test_read_single_user(client):
    resp = client.get("/v1/users/U01")
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Alice Chen"


def test_read_single_user_not_found(client):
    resp = client.get("/v1/users/U99")
    assert resp.status_code == 404


def test_create_user(client):
    resp = client.post("/v1/users", json={
        "full_name": "Eve Park",
        "email": "eve@example.com",
        "role": "Consultant",
        "availability": 20,
        "timezone": "UTC",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == "Eve Park"
    assert data["user_id"]


def test_delete_user(client):
    resp = client.delete("/v1/users/U01")
    assert resp.status_code == 200
    # Verify it's gone
    resp2 = client.get("/v1/users/U01")
    assert resp2.status_code == 404


def test_user_skills_enriched(client):
    resp = client.get("/v1/users/U01/skills")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["user_id"] == "U01"
    assert len(data["skills"]) == 2

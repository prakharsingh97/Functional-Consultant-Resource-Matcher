"""Shared test fixtures for mock-first testing."""
import pytest
import pandas as pd
from io import BytesIO


@pytest.fixture
def sample_users_df():
    """Mock users sheet data."""
    return pd.DataFrame({
        "user_id": ["U01", "U02", "U03"],
        "full_name": ["Alice Chen", "Bob Kumar", "Carol Smith"],
        "email": ["alice@example.com", "bob@example.com", "carol@example.com"],
        "role": ["Senior Consultant", "Lead Architect", "Junior Developer"],
        "availability": [30, 20, 40],
        "timezone": ["UTC", "Asia/Singapore", "US/Eastern"],
        "created_at": ["2025-01-01", "2025-01-02", "2025-01-03"],
    })


@pytest.fixture
def sample_skills_df():
    """Mock skills sheet data."""
    return pd.DataFrame({
        "skill_id": ["SK01", "SK02", "SK03", "SK04"],
        "skill_name": ["Python", "AWS", "Azure", "LangChain"],
        "category": ["Engineering", "Cloud", "Cloud", "AI/ML"],
        "description": ["Python programming", "Amazon Web Services", "Microsoft Azure", "LangChain framework"],
    })


@pytest.fixture
def sample_levels_df():
    """Mock levels sheet data."""
    return pd.DataFrame({
        "level_id": [1, 2, 3, 4],
        "level_name": ["Beginner", "Intermediate", "Advanced", "Expert"],
        "score_weight": [0.25, 0.50, 0.75, 1.00],
    })


@pytest.fixture
def sample_user_skills_df():
    """Mock user_skills sheet data."""
    return pd.DataFrame({
        "id": ["US01", "US02", "US03", "US04", "US05"],
        "user_id": ["U01", "U01", "U02", "U02", "U03"],
        "skill_id": ["SK01", "SK02", "SK01", "SK03", "SK02"],
        "level_id": [3, 4, 3, 2, 3],
        "years_exp": [5, 4, 3, 2, 4],
        "last_used": ["2025-05-01", "2025-04-15", "2025-03-01", "2025-01-01", "2025-05-10"],
    })


@pytest.fixture
def sample_excel_bytes(sample_users_df, sample_skills_df, sample_levels_df, sample_user_skills_df):
    """Create an in-memory Excel file with all 4 sheets."""
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        sample_users_df.to_excel(writer, sheet_name="users", index=False)
        sample_skills_df.to_excel(writer, sheet_name="skills", index=False)
        sample_levels_df.to_excel(writer, sheet_name="levels", index=False)
        sample_user_skills_df.to_excel(writer, sheet_name="user_skills", index=False)
    buf.seek(0)
    return buf

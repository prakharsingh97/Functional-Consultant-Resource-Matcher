"""Tests for Pydantic data contracts."""
import pytest
from src.models.schemas import (
    User, UserCreate, Skill, SkillStrength, Level,
    UserSkill, UserSkillCreate, UserWithSkills,
    TaskResourceAssignment, TaskRecommendation,
)


def test_user_model_valid():
    user = User(
        user_id="U01", full_name="Alice", email="alice@test.com",
        role="Consultant", availability=30, timezone="UTC",
        created_at="2025-01-01",
    )
    assert user.user_id == "U01"
    assert user.availability == 30


def test_user_create_model_valid():
    user = UserCreate(
        full_name="Alice", email="alice@test.com",
        role="Consultant", availability=30, timezone="UTC",
    )
    assert user.full_name == "Alice"


def test_skill_model_valid():
    skill = Skill(
        skill_id="SK01", skill_name="Python",
        category="Engineering", description="Python programming",
    )
    assert skill.skill_name == "Python"


def test_level_model_valid():
    level = Level(level_id=3, level_name="Advanced", score_weight=0.75)
    assert level.score_weight == 0.75


def test_user_skill_model_valid():
    us = UserSkill(
        id="US01", user_id="U01", skill_id="SK01",
        level_id=3, years_exp=5, last_used="2025-01-01",
    )
    assert us.years_exp == 5


def test_user_with_skills_model():
    user = User(
        user_id="U01", full_name="Alice", email="alice@test.com",
        role="Consultant", availability=30, timezone="UTC",
        created_at="2025-01-01",
    )
    enriched = UserWithSkills(
        user=user,
        skills=[
            UserSkill(id="US01", user_id="U01", skill_id="SK01",
                      level_id=3, years_exp=5, last_used="2025-01-01"),
        ],
    )
    assert len(enriched.skills) == 1


def test_skill_strength_model():
    ss = SkillStrength(
        skill_id="SK01", skill_name="Python",
        category="Engineering", strength_score=5.25,
    )
    assert ss.strength_score == 5.25


def test_task_recommendation_model():
    assignment = TaskResourceAssignment(
        user_id="U01",
        full_name="Alice",
        role="Engineer",
        fit_score=0.82,
        availability=30,
        matched_skills=["Python"],
        recommendation="Primary",
    )
    task = TaskRecommendation(
        task_id=1,
        task="Build streaming backend",
        required_skills=["Python", "FastAPI"],
        strength_score=4.5,
        resources=[assignment],
        rationale="Strong backend match.",
    )
    assert task.resources[0].recommendation == "Primary"

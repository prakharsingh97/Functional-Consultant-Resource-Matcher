"""Skills and skill-strength endpoints."""
from fastapi import APIRouter
from src.db.excel_db import get_all_skills, get_skill_strength_scores

router = APIRouter(tags=["skills"])


@router.get("/skills")
def list_skills():
    """Return all skills."""
    return get_all_skills()


@router.get("/skills/strength")
def skill_strength():
    """Return all skills ranked by Skill Strength Score (descending)."""
    scores = get_skill_strength_scores()
    return sorted(
        scores, key=lambda x: x["strength_score"], reverse=True
    )

"""User-skills join table endpoints."""
from fastapi import APIRouter
from src.db.excel_db import get_all_user_skills

router = APIRouter(tags=["user_skills"])


@router.get("/user-skills")
def list_user_skills():
    """Return all user-skill join records."""
    return get_all_user_skills()

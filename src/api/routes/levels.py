"""Levels CRUD endpoints."""
from fastapi import APIRouter
from src.db.excel_db import get_all_levels

router = APIRouter(tags=["levels"])


@router.get("/levels")
def list_levels():
    """Return all levels."""
    return get_all_levels()

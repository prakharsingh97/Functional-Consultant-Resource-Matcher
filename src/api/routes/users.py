"""User CRUD endpoints under /v1/users."""
from fastapi import APIRouter, HTTPException
from src.models.schemas import UserCreate
from src.db.excel_db import (
    get_all_users, get_user_by_id, create_user as db_create_user,
    delete_user as db_delete_user, get_user_skills_enriched,
)

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[dict])
def list_users():
    """Return all users."""
    return get_all_users()


@router.get("/users/{user_id}", response_model=dict)
def read_user(user_id: str):
    """Return a single user by ID."""
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users", status_code=201, response_model=dict)
def create_user_endpoint(user: UserCreate):
    """Create a new user."""
    return db_create_user(user.model_dump())


@router.delete("/users/{user_id}")
def delete_user_endpoint(user_id: str):
    """Delete a user by ID."""
    success = db_delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": True}


@router.get("/users/{user_id}/skills", response_model=dict)
def read_user_skills(user_id: str):
    """Return user with enriched skill profiles."""
    result = get_user_skills_enriched(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result

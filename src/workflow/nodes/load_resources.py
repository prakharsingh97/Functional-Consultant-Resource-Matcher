"""Node 1: Load all resources from Excel database."""
from src.db.excel_db import (
    get_all_users, get_all_skills, get_all_levels, get_all_user_skills,
)
from src.workflow.llm.client import get_model_name
from src.workflow.utils import get_writer


def load_resources(state: dict) -> dict:
    """Load all data from Excel into the pipeline state.

    Args:
        state: Pipeline state with problem_statement.

    Returns:
        Updated state with users, skills, levels, user_skills,
        and the active model_name.
    """
    writer = get_writer()
    writer({"status": "Loading consultant database..."})
    users = get_all_users()
    skills = get_all_skills()
    levels = get_all_levels()
    user_skills = get_all_user_skills()
    writer({"status": f"Loaded {len(users)} users, {len(skills)} skills"})
    return {
        **state,
        "model_name": get_model_name(),
        "users": users,
        "skills": skills,
        "levels": levels,
        "user_skills": user_skills,
    }

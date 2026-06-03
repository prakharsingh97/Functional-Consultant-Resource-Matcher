"""Excel data access functions. Sheets = tables, rows = records."""
import os
import uuid
from datetime import datetime, timezone
import pandas as pd

_sheets_cache: dict[str, pd.DataFrame] = {}


def _load_db() -> dict[str, pd.DataFrame]:
    """Load all sheets from Excel file into cache."""
    if _sheets_cache:
        return _sheets_cache
    path = os.getenv("EXCEL_DB_PATH", "data/consultant_database.xlsx")
    xls = pd.ExcelFile(path)
    for name in xls.sheet_names:
        _sheets_cache[name] = pd.read_excel(xls, sheet_name=name)
    return _sheets_cache


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts, handling NaN."""
    return df.where(df.notna(), None).to_dict(orient="records")


def load_sheet(sheet_name: str) -> pd.DataFrame:
    """Load a single sheet as DataFrame."""
    db = _load_db()
    return db.get(sheet_name, pd.DataFrame())


def get_all_users() -> list[dict]:
    """Return all user records."""
    return _df_to_records(load_sheet("users"))


def get_user_by_id(user_id: str) -> dict | None:
    """Return a single user by user_id, or None."""
    df = load_sheet("users")
    matches = df[df["user_id"] == user_id]
    if matches.empty:
        return None
    return matches.iloc[0].where(matches.iloc[0].notna(), None).to_dict()


def get_all_skills() -> list[dict]:
    """Return all skill records."""
    return _df_to_records(load_sheet("skills"))


def get_all_levels() -> list[dict]:
    """Return all level records."""
    return _df_to_records(load_sheet("levels"))


def get_all_user_skills() -> list[dict]:
    """Return all user_skill join records."""
    return _df_to_records(load_sheet("user_skills"))


def get_skill_strength_scores() -> list[dict]:
    """Compute Skill Strength Score per skill.

    SUM of score_weight for all users with that skill.
    """
    user_skills = load_sheet("user_skills")
    levels = load_sheet("levels")
    skills = load_sheet("skills")
    if user_skills.empty:
        return []
    level_weights = dict(zip(levels["level_id"], levels["score_weight"]))
    user_skills = user_skills.copy()
    user_skills["weight"] = user_skills["level_id"].map(level_weights)
    strength = user_skills.groupby("skill_id")["weight"].sum().reset_index()
    strength.columns = ["skill_id", "strength_score"]
    result = strength.merge(skills, on="skill_id", how="left")
    cols = ["skill_id", "skill_name", "category", "strength_score"]
    return result[cols].to_dict(orient="records")


def get_user_skills_enriched(user_id: str) -> dict | None:
    """Return user with their enriched skill profiles."""
    user = get_user_by_id(user_id)
    if user is None:
        return None
    us_df = load_sheet("user_skills")
    user_rows = us_df[us_df["user_id"] == user_id]
    return {"user": user, "skills": _df_to_records(user_rows)}


def create_user(data: dict) -> dict:
    """Create a new user row. Returns the created user dict."""
    new_id = f"U{uuid.uuid4().hex[:6].upper()}"
    row = {
        "user_id": new_id,
        "full_name": data["full_name"],
        "email": data["email"],
        "role": data["role"],
        "availability": data["availability"],
        "timezone": data.get("timezone", "UTC"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    df = load_sheet("users")
    new_df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _sheets_cache["users"] = new_df
    return row


def delete_user(user_id: str) -> bool:
    """Delete a user by user_id. Returns True if deleted."""
    df = load_sheet("users")
    if user_id not in df["user_id"].values:
        return False
    filtered = df[df["user_id"] != user_id].reset_index(drop=True)
    _sheets_cache["users"] = filtered
    return True

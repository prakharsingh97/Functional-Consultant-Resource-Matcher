"""Node 3: Compute Skill Strength Scores using semantic matching.

Strength = SUM(score_weight * semantic_similarity) across all users
who have that skill. Only skills that semantically match required
skills are scored.
"""
import logging
import time

from src.workflow.utils import get_writer
from src.workflow.llm.embeddings import match_skills_semantic

logger = logging.getLogger(__name__)


def compute_strength(state: dict) -> dict:
    """Calculate semantic Skill Strength Score for each DB skill.

    Args:
        state: Pipeline state with skills, levels, user_skills,
                search_results.

    Returns:
        Updated state with skill_strength_scores, sorted desc.
    """
    writer = get_writer()
    writer({"status": "Computing semantic skill matches..."})

    levels = {
        lv["level_id"]: lv["score_weight"]
        for lv in state.get("levels", [])
    }
    user_skills = state.get("user_skills", [])
    skills = state.get("skills", [])
    required = state.get("search_results", {}).get(
        "required_skills", []
    )

    db_names = [s["skill_name"] for s in skills]
    logger.info(
        "compute_strength.semantic_match_start required_skills=%s db_skills=%s",
        len(required), len(db_names),
    )
    writer({"status": "Loading semantic matcher..."})
    start = time.perf_counter()
    semantic_matches = match_skills_semantic(required, db_names)
    elapsed = time.perf_counter() - start
    logger.info(
        "compute_strength.semantic_match_complete matches=%s duration=%.2fs",
        sum(1 for m in semantic_matches if m["matched"]), elapsed,
    )
    sim_map = {
        m["skill_name"]: m["similarity"]
        for m in semantic_matches
    }

    matched_count = sum(1 for m in semantic_matches if m["matched"])
    writer({"status": f"Matched {matched_count} skills semantically"})

    score_map = {}
    for us in user_skills:
        sid = us["skill_id"]
        weight = levels.get(us["level_id"], 0)
        skill_name = _get_skill_name(skills, sid)
        sim = sim_map.get(skill_name, 0.0)
        if sim > 0:
            score_map[sid] = score_map.get(sid, 0) + (
                weight * sim
            )

    skill_lookup = {s["skill_id"]: s for s in skills}
    scores = []
    for sid, total in score_map.items():
        meta = skill_lookup.get(sid, {})
        scores.append({
            "skill_id": sid,
            "skill_name": meta.get("skill_name", sid),
            "category": meta.get("category", ""),
            "strength_score": round(total, 4),
        })

    scores.sort(key=lambda x: x["strength_score"], reverse=True)
    return {**state, "skill_strength_scores": scores}


def _get_skill_name(skills: list[dict], skill_id: str) -> str:
    """Look up skill name by ID."""
    for s in skills:
        if s["skill_id"] == skill_id:
            return s["skill_name"]
    return skill_id

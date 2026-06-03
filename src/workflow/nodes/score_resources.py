"""Node 5: Score resources by semantic skill fit, rank, assign priority."""
import logging
import time

from src.workflow.utils import get_writer
from src.workflow.llm.embeddings import match_skills_semantic

MIN_TASK_FIT = 0.25
MAX_TASK_RESOURCES = 3
logger = logging.getLogger(__name__)


def score_resources(state: dict) -> dict:
    """Score each resource by semantic skill fit, rank, assign priority.

    Fit = SUM(score_weight * semantic_sim for matched skills) /
          (num_required_skills * max_weight)
    Normalized to 0-1.

    Args:
        state: Pipeline state with users, levels, user_skills,
                skills, search_results.

    Returns:
        Updated state with ranked_resources, sorted desc by fit.
    """
    writer = get_writer()
    writer({"status": "Scoring resource fit..."})

    users = state.get("users", [])
    levels = {
        lv["level_id"]: lv["score_weight"]
        for lv in state.get("levels", [])
    }
    user_skills = state.get("user_skills", [])
    skills = {
        s["skill_id"]: s["skill_name"]
        for s in state.get("skills", [])
    }
    required = state.get("search_results", {}).get(
        "required_skills", []
    )

    # Semantic match DB skill names to required skills
    db_names = list(skills.values())
    start = time.perf_counter()
    logger.info(
        "score_resources.project_match_start required_skills=%s db_skills=%s",
        len(required), len(db_names),
    )
    semantic_matches = match_skills_semantic(required, db_names)
    logger.info(
        "score_resources.project_match_complete duration=%.2fs",
        time.perf_counter() - start,
    )
    sim_by_name = {
        m["skill_name"]: m for m in semantic_matches
    }

    # Build per-user skill map
    user_skill_map = {}
    for us in user_skills:
        uid = us["user_id"]
        user_skill_map.setdefault(uid, []).append(us)

    max_possible = max(len(required), 1) * 1.0

    scored = []
    for user in users:
        uid = user["user_id"]
        raw_score, matched = _compute_semantic_fit(
            uid, user_skill_map, levels, skills, sim_by_name,
        )
        fit_score = round(raw_score / max_possible, 2)
        avail = user.get("availability", 0)
        risk_flag = fit_score < 0.5 or avail < 10
        priority = _assign_priority(fit_score, avail)
        scored.append({
            "user_id": uid,
            "full_name": user.get("full_name", ""),
            "fit_score": fit_score,
            "availability": avail,
            "priority": priority,
            "risk_flag": risk_flag,
            "matched_skills": matched,
        })

    scored.sort(key=lambda x: x["fit_score"], reverse=True)
    task_recommendations = _build_task_recommendations(
        state, users, levels, user_skills, skills,
        language=state.get("language", "English"),
    )
    writer({
        "status": (
            f"Ranked {len(scored)} resources across "
            f"{len(task_recommendations)} tasks"
        )
    })
    return {
        **state,
        "ranked_resources": scored,
        "task_recommendations": task_recommendations,
    }


def _compute_semantic_fit(
    user_id: str, user_skill_map: dict,
    levels: dict, skills: dict, sim_by_name: dict,
) -> tuple[float, list[str]]:
    """Compute semantic fit score for a single user.

    Returns:
        Tuple of (raw_score, matched_skill_names).
    """
    score = 0.0
    matched = []
    for us in user_skill_map.get(user_id, []):
        sname = skills.get(us["skill_id"], "")
        match_info = sim_by_name.get(sname)
        if match_info and match_info["matched"]:
            sim = match_info["similarity"]
            weight = levels.get(us["level_id"], 0)
            score += weight * sim
            matched.append(sname)
    return score, matched


def _assign_priority(fit_score: float, availability: int) -> str:
    """Assign P1-P4 priority label per CLAUDE.md spec."""
    if fit_score < 0.25:
        return "P4 - Skip"
    if fit_score >= 0.75 and availability >= 20:
        return "P1 - Assign"
    if 0.5 <= fit_score < 0.75 and availability >= 10:
        return "P2 - Consider"
    if fit_score >= 0.5 and availability >= 10:
        return "P2 - Consider"
    return "P3 - Risky"


def _build_task_recommendations(
    state: dict,
    users: list[dict],
    levels: dict,
    user_skills: list[dict],
    skills: dict,
    language: str = "English",
) -> list[dict]:
    """Build per-task staffing recommendations from solution steps."""
    tasks = state.get("generic_solution", [])
    if not tasks:
        tasks = _fallback_tasks(state)

    user_skill_map = {}
    for us in user_skills:
        uid = us["user_id"]
        user_skill_map.setdefault(uid, []).append(us)

    project_skills = state.get("search_results", {}).get(
        "required_skills", []
    )
    skill_strengths = {
        item.get("skill_name"): item.get("strength_score", 0.0)
        for item in state.get("skill_strength_scores", [])
    }

    recommendations = []
    start = time.perf_counter()
    for idx, task in enumerate(tasks, start=1):
        required = _task_required_skills(task, project_skills)
        candidates = _score_task_candidates(
            required, users, user_skill_map, levels, skills,
        )
        selected = _select_task_resources(candidates)
        strength = _task_strength(required, skill_strengths)
        recommendations.append({
            "task_id": int(task.get("step") or idx),
            "task": task.get("action", f"Task {idx}"),
            "required_skills": required,
            "strength_score": strength,
            "resources": selected,
            "rationale": _task_rationale(required, selected, language),
        })

    logger.info(
        "score_resources.task_recommendations_complete tasks=%s "
        "duration=%.2fs",
        len(recommendations), time.perf_counter() - start,
    )
    return recommendations


def _fallback_tasks(state: dict) -> list[dict]:
    """Create broad project tasks if solution generation returned none."""
    problem = state.get("problem_statement", "Project implementation")
    return [
        {
            "step": 1,
            "action": f"Scope and plan delivery for: {problem[:120]}",
            "technology": "Product Management",
        },
        {
            "step": 2,
            "action": "Implement core engineering and integration work",
            "technology": "Python",
        },
        {
            "step": 3,
            "action": "Validate quality, testing, and release readiness",
            "technology": "QA",
        },
    ]


def _task_required_skills(
    task: dict, project_skills: list[str],
) -> list[str]:
    """Derive task-specific skills from the task and project context."""
    action = task.get("action", "")
    technology = task.get("technology", "")
    text = f"{action} {technology}".lower()
    required = []
    if technology and technology not in {"N/A", "Architecture"}:
        required.append(technology)
    for skill in project_skills:
        skill_lower = skill.lower()
        if (
            skill_lower in text
            or any(part in text for part in skill_lower.split())
        ):
            required.append(skill)
    if len(required) < 2:
        for skill in project_skills:
            required.append(skill)
            if len(required) >= 3:
                break
    return _dedupe(required) or ["Project Delivery"]


def _score_task_candidates(
    required: list[str],
    users: list[dict],
    user_skill_map: dict,
    levels: dict,
    skills: dict,
) -> list[dict]:
    """Score users against one task's required skills."""
    db_names = list(skills.values())
    semantic_matches = match_skills_semantic(required, db_names)
    sim_by_name = {m["skill_name"]: m for m in semantic_matches}
    max_possible = max(len(required), 1) * 1.0

    candidates = []
    for user in users:
        raw_score, matched = _compute_semantic_fit(
            user["user_id"], user_skill_map, levels, skills, sim_by_name,
        )
        skill_fit = min(raw_score / max_possible, 1.0)
        availability = user.get("availability", 0)
        availability_fit = min(availability / 20, 1.0)
        fit_score = round((skill_fit * 0.8) + (availability_fit * 0.2), 2)
        candidates.append({
            "user_id": user["user_id"],
            "full_name": user.get("full_name", ""),
            "role": user.get("role", ""),
            "fit_score": fit_score,
            "availability": availability,
            "matched_skills": matched,
        })

    candidates.sort(key=lambda x: x["fit_score"], reverse=True)
    return candidates


def _select_task_resources(candidates: list[dict]) -> list[dict]:
    """Pick the best viable people for a task without P3/P4 labels."""
    viable = [
        c for c in candidates
        if c["fit_score"] >= MIN_TASK_FIT and c["availability"] >= 5
    ]
    if not viable and candidates:
        viable = candidates[:1]

    selected = []
    for idx, candidate in enumerate(viable[:MAX_TASK_RESOURCES]):
        recommendation = "Primary" if idx == 0 else "Support"
        selected.append({**candidate, "recommendation": recommendation})
    return selected


def _task_strength(
    required: list[str], skill_strengths: dict[str, float],
) -> float:
    """Average known team strength for the task skills."""
    scores = [
        float(skill_strengths.get(skill, 0.0))
        for skill in required
    ]
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


_RATIONALE_TEMPLATES: dict[str, dict[str, str]] = {
    "English":             {"selected": "Selected {names} based on fit for {skills}.",
                            "no_candidate": "No available candidate met the minimum task-fit threshold."},
    "Hindi":               {"selected": "{names} को {skills} के लिए फिट के आधार पर चुना गया।",
                            "no_candidate": "कोई भी उम्मीदवार न्यूनतम कार्य-फिट सीमा को पूरा नहीं करता।"},
    "French":              {"selected": "{names} sélectionné(s) pour leur adéquation avec {skills}.",
                            "no_candidate": "Aucun candidat disponible ne répond au seuil minimum."},
    "German":              {"selected": "{names} aufgrund der Eignung für {skills} ausgewählt.",
                            "no_candidate": "Kein verfügbarer Kandidat erfüllt den Mindest-Eignungsschwellenwert."},
    "Spanish":             {"selected": "{names} seleccionado(s) por adecuación para {skills}.",
                            "no_candidate": "Ningún candidato disponible cumple el umbral mínimo."},
    "Portuguese":          {"selected": "{names} selecionado(s) por adequação para {skills}.",
                            "no_candidate": "Nenhum candidato disponível atende ao limite mínimo."},
    "Arabic":              {"selected": "تم اختيار {names} بناءً على الملاءمة لـ {skills}.",
                            "no_candidate": "لا يوجد مرشح متاح يستوفي الحد الأدنى للملاءمة."},
    "Japanese":            {"selected": "{skills}への適合性に基づき{names}を選出。",
                            "no_candidate": "最低タスク適合基準を満たす候補者がいません。"},
    "Chinese (Simplified)":{"selected": "{names}因与{skills}的匹配度而被选中。",
                            "no_candidate": "没有可用候选人满足最低任务匹配阈值。"},
}


def _task_rationale(
    required: list[str], selected: list[dict], language: str = "English",
) -> str:
    """Explain why resources were selected for the task."""
    t = _RATIONALE_TEMPLATES.get(language, _RATIONALE_TEMPLATES["English"])
    if not selected:
        return t["no_candidate"]
    names = ", ".join(r["full_name"] for r in selected)
    skills = ", ".join(required)
    return t["selected"].format(names=names, skills=skills)


def _dedupe(values: list[str]) -> list[str]:
    """Deduplicate strings while preserving order."""
    seen = set()
    result = []
    for value in values:
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result

"""Node 4: Generate Skill-Biased Generic Solution using LLM."""
import json
import logging
import time
from src.workflow.utils import get_writer
from src.workflow.llm.client import (
    is_testing, get_llm_client, get_model_name,
)
from src.workflow.llm.mock_llm import get_mock_solution
from src.workflow.llm.prompts import (
    SOLUTION_SYSTEM_PROMPT, build_solution_prompt,
)

logger = logging.getLogger(__name__)


def generate_solution(state: dict) -> dict:
    """Generate a step-by-step solution biased to team strengths.

    In TESTING mode: returns mock solution.
    In live mode: calls OpenRouter LLM with tech ranking.

    Args:
        state: Pipeline state with problem_statement and
                skill_strength_scores.

    Returns:
        Updated state with generic_solution populated.
    """
    writer = get_writer()
    writer({"status": "Generating skill-biased solution..."})
    problem = state.get("problem_statement", "")
    tech_ranking = state.get("skill_strength_scores", [])
    override = state.get("override_steps", [])
    if override:
        writer({"status": f"Using {len(override)} edited steps"})
        return {**state, "generic_solution": override}

    language = state.get("language", "English")
    if is_testing():
        solution = get_mock_solution(problem, tech_ranking)
    else:
        try:
            solution = _call_llm_for_solution(problem, tech_ranking, language)
        except Exception:
            logger.exception("generate_solution.live_call_failed")
            solution = _fallback_solution(problem, tech_ranking)

    writer({"status": f"Created {len(solution)} solution steps"})
    return {**state, "generic_solution": solution}


def _call_llm_for_solution(
    problem: str, tech_ranking: list[dict], language: str = "English",
) -> list[dict]:
    """Call OpenRouter LLM to generate the solution.

    Args:
        problem: Problem statement.
        tech_ranking: Ranked tech list with strength scores.

    Returns:
        List of solution step dicts.
    """
    client = get_llm_client()
    prompt = build_solution_prompt(problem, tech_ranking, language)
    logger.info(
        "generate_solution.llm_start model=%s prompt_chars=%s "
        "tech_ranking=%s",
        get_model_name(), len(prompt), len(tech_ranking),
    )
    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": SOLUTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        steps = parsed if isinstance(parsed, list) else parsed.get("steps", [])
        steps = _normalize_solution_steps(steps)
        if steps:
            elapsed = time.perf_counter() - start
            logger.info(
                "generate_solution.llm_complete steps=%s duration=%.2fs",
                len(steps), elapsed,
            )
            return steps
        logger.warning("generate_solution.empty_llm_steps")
    except (json.JSONDecodeError, Exception):
        logger.exception("generate_solution.llm_failed")
    elapsed = time.perf_counter() - start
    logger.info("generate_solution.llm_fallback duration=%.2fs", elapsed)
    return _fallback_solution(problem, tech_ranking)


def _normalize_solution_steps(steps: list) -> list[dict]:
    """Keep only valid solution steps with required output fields."""
    normalized = []
    for idx, step in enumerate(steps or [], start=1):
        if not isinstance(step, dict):
            continue
        normalized.append({
            "step": int(step.get("step") or idx),
            "action": str(step.get("action") or "Define implementation step"),
            "technology": str(step.get("technology") or "Architecture"),
            "skill_strength_score": float(
                step.get("skill_strength_score") or 0.0
            ),
            "effort": str(step.get("effort") or "TBD"),
        })
    return normalized


def _fallback_solution(
    problem: str, tech_ranking: list[dict],
) -> list[dict]:
    """Build a deterministic solution when the live LLM returns nothing."""
    ranked = [
        {
            "name": item.get("skill_name", "Architecture"),
            "score": float(item.get("strength_score", 0.0)),
        }
        for item in tech_ranking[:5]
    ]
    while len(ranked) < 6:
        defaults = [
            ("Python", 0.0),
            ("FastAPI", 0.0),
            ("LangGraph", 0.0),
            ("Streamlit", 0.0),
            ("Guardrails", 0.0),
            ("QA", 0.0),
            ("Release Planning", 0.0),
        ]
        name, score = defaults[len(ranked)]
        ranked.append({"name": name, "score": score})

    return [
        {
            "step": 1,
            "action": (
                "Scope product goals, user journeys, insight workflows, "
                "success metrics, and project delivery boundaries."
            ),
            "technology": ranked[0]["name"],
            "skill_strength_score": ranked[0]["score"],
            "effort": "1-2 days",
        },
        {
            "step": 2,
            "action": (
                "Define the conversational insights architecture, agent "
                "boundaries, tool contracts, and latency budget."
            ),
            "technology": ranked[1]["name"],
            "skill_strength_score": ranked[1]["score"],
            "effort": "2-3 days",
        },
        {
            "step": 3,
            "action": (
                "Add LlamaIndex retrieval and LangGraph agent workflows for "
                "multi-tool reasoning and insight generation."
            ),
            "technology": ranked[2]["name"],
            "skill_strength_score": ranked[2]["score"],
            "effort": "3-5 days",
        },
        {
            "step": 4,
            "action": (
                "Implement streaming orchestration with progress events, "
                "tool-call traces, and recoverable error events."
            ),
            "technology": ranked[3]["name"],
            "skill_strength_score": ranked[3]["score"],
            "effort": "2-3 days",
        },
        {
            "step": 5,
            "action": (
                "Build Streamlit visualizations for intermediate findings, "
                "citations, metrics, and final insight summaries."
            ),
            "technology": ranked[4]["name"],
            "skill_strength_score": ranked[4]["score"],
            "effort": "2-4 days",
        },
        {
            "step": 6,
            "action": (
                "Plan QA, testing, release readiness, observability, and "
                "input/output guardrails validation."
            ),
            "technology": ranked[5]["name"],
            "skill_strength_score": ranked[5]["score"],
            "effort": "2-3 days",
        },
    ]

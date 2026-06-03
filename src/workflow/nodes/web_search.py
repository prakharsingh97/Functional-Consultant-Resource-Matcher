"""Node 2: Tavily web search + LLM skill extraction.

Flow: Tavily searches web → LLM reasons over results → extracts required
skills, tech stack, and difficulty assessment.
"""
import json
import logging
import time
from src.workflow.utils import get_writer
from src.workflow.llm.client import is_testing, get_llm_client, get_model_name
from src.workflow.llm.mock_llm import get_mock_search_results
from src.workflow.llm.tools import tavily_search
from src.workflow.llm.prompts import (
    SKILL_EXTRACTION_PROMPT, build_skill_extraction_prompt,
)

logger = logging.getLogger(__name__)


def web_search(state: dict) -> dict:
    """Search web for problem context and extract required skills.

    In TESTING mode: returns mock results.
    In live mode: Tavily search → LLM extracts skills from results.

    Args:
        state: Pipeline state with problem_statement.

    Returns:
        Updated state with search_results populated.
    """
    writer = get_writer()
    writer({"status": "Searching web for context..."})
    problem = state.get("problem_statement", "")
    cached = state.get("cached_search_results", {})
    if cached and cached.get("required_skills"):
        writer({"status": f"Using cached results ({len(cached['required_skills'])} skills)"})
        return {**state, "search_results": cached}
    if is_testing():
        results = get_mock_search_results(problem)
    else:
        results = _search_and_extract(problem, writer)
    skills_count = len(results.get("required_skills", []))
    writer({"status": f"Extracted {skills_count} required skills"})
    return {**state, "search_results": results}


def _search_and_extract(problem: str, writer) -> dict:
    """Call Tavily, then have LLM extract skills from results.

    Args:
        problem: The problem statement.
        writer: Stream writer for progress messages.

    Returns:
        Dict with required_skills, search_context, difficulty.
    """
    writer({"status": "Running Tavily search..."})
    start = time.perf_counter()
    raw = tavily_search(problem)
    elapsed = time.perf_counter() - start
    logger.info(
        "web_search.tavily_complete results=%s duration=%.2fs",
        len(raw.get("results", [])), elapsed,
    )
    snippets = _format_search_results(raw)
    writer({"status": "LLM extracting skills from results..."})
    return _llm_extract_skills(problem, snippets)


def _format_search_results(raw: dict) -> str:
    """Format Tavily results into a single text block for the LLM."""
    results = raw.get("results", [])
    parts = []
    for r in results:
        title = r.get("title", "")
        content = r.get("content", "")
        parts.append(f"- {title}: {content}")
    return "\n".join(parts) if parts else "No results found."


def _llm_extract_skills(problem: str, snippets: str) -> dict:
    """Use LLM to extract required skills from search snippets.

    Args:
        problem: Problem statement.
        snippets: Formatted search result text.

    Returns:
        Dict with required_skills, search_context, difficulty.
    """
    client = get_llm_client()
    prompt = build_skill_extraction_prompt(problem, snippets)
    logger.info(
        "web_search.llm_extract_start model=%s prompt_chars=%s",
        get_model_name(), len(prompt),
    )
    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": SKILL_EXTRACTION_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        if parsed.get("required_skills"):
            elapsed = time.perf_counter() - start
            logger.info(
                "web_search.llm_extract_complete skills=%s duration=%.2fs",
                len(parsed.get("required_skills", [])), elapsed,
            )
            return parsed
        logger.warning("web_search.empty_llm_skills")
    except (json.JSONDecodeError, Exception):
        logger.exception("web_search.llm_extract_failed")
    elapsed = time.perf_counter() - start
    logger.info("web_search.llm_extract_fallback duration=%.2fs", elapsed)
    return _fallback_extract_skills(problem, snippets)


def _fallback_extract_skills(problem: str, snippets: str) -> dict:
    """Extract a useful baseline skill list from the problem text."""
    text = f"{problem} {snippets}".lower()
    keywords = {
        "Python": ["python"],
        "FastAPI": ["fastapi", "api"],
        "Streamlit": ["streamlit", "ui", "visualization", "dashboard"],
        "LangGraph": ["langgraph", "agent", "agents"],
        "LlamaIndex": ["llamaindex", "llama index", "rag"],
        "LLM Orchestration": ["llm", "language model"],
        "Guardrails": ["guardrail", "safety", "input", "output"],
        "Streaming UX": ["stream", "latency", "real-time", "engaged"],
        "Data Visualization": ["visualization", "charts", "insights"],
        "Tool Integration": ["tools", "tool"],
        "Cloud Deployment": ["deploy", "deployment", "cloud"],
    }
    skills = [
        skill for skill, terms in keywords.items()
        if any(term in text for term in terms)
    ]
    if not skills:
        skills = ["Python", "FastAPI", "Streamlit", "LLM Orchestration"]
    return {
        "required_skills": skills,
        "search_context": (
            "Fallback extraction from the submitted problem statement. "
            f"{problem[:240]}"
        ),
        "difficulty": 0.75,
    }

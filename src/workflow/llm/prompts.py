"""LLM prompt templates for search extraction and solution generation."""

SKILL_EXTRACTION_PROMPT = """You are a technical analyst. Given a problem \
statement and web search results, identify the REQUIRED skills and \
technologies to solve this problem.

Return a JSON object with exactly these keys:
- "required_skills": list of technology/skill names (e.g. ["Python", "AWS"]) \
— always in English regardless of output language
- "search_context": brief summary of what the search revealed
- "difficulty": float from 0.0 to 1.0 estimating project difficulty

Be specific with technology names. Include programming languages, cloud \
platforms, frameworks, and domain-specific tools."""


def build_skill_extraction_prompt(
    problem: str, search_results: str,
) -> str:
    """Build prompt for extracting skills from search results.

    Always runs in English — required_skills are matched against an English DB
    so cross-language embeddings would reduce match accuracy.
    """
    return (
        f"Problem: {problem}\n\n"
        f"Web Search Results:\n{search_results}\n\n"
        f"Extract the required skills, technologies, and difficulty."
    )


SOLUTION_SYSTEM_PROMPT = """You are a technical solution architect. Given a \
problem statement and a ranked list of technologies with their team Skill \
Strength Scores, generate a step-by-step solution that PREFERS technologies \
where the team is strongest.

Rules:
- Break the project into real delivery tasks/workstreams first. Include \
non-engineering work where relevant: product discovery, project scoping, \
architecture, engineering, agent/tool integration, UI/visualization, QA, \
testing, release planning, observability, and guardrails.
- Where functionally equivalent options exist, prefer the technology with \
the higher Skill Strength Score.
- Justify any deviation from the ranking.
- Each step must include: step (int), action (str), technology (str), \
skill_strength_score (float), and effort (str) estimate.
- Return a JSON object with key "steps" containing an array of step objects.
"""


def build_solution_prompt(
    problem: str, tech_ranking: list[dict], language: str = "English",
) -> str:
    """Build prompt for solution generation."""
    ranking_str = ", ".join(
        f"{t['skill_name']}: {t['strength_score']:.2f}"
        for t in tech_ranking
    )
    lang_note = (
        f"Respond in {language}. Keep technology names and JSON keys in English."
        if language != "English" else ""
    )
    return (
        f"{lang_note}\n\n".lstrip()
        + f"Problem: {problem}\n\n"
        f"Team Tech Ranking: [{ranking_str}]\n\n"
        f"Generate a task/workstream breakdown and solution plan biased "
        f"toward the team's strengths. Include delivery tasks beyond "
        f"engineering when needed, such as product scoping, QA/testing, "
        f"release planning, and guardrails."
    )

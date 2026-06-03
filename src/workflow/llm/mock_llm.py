"""Mock LLM responses for testing. Used when env=TESTING."""

MOCK_SEARCH_RESULTS = {
    "required_skills": [
        "Python", "AWS", "FastAPI", "LangChain",
        "Product Management", "QA", "Release Planning",
    ],
    "search_context": (
        "Legal AI platforms require Python backends, "
        "AWS cloud hosting, FastAPI for REST APIs, "
        "and LangChain for LLM orchestration."
    ),
    "difficulty": 0.7,
}

MOCK_SOLUTION = [
    {"step": 1, "action": "Scope product goals and project delivery plan",
     "technology": "Product Management", "skill_strength_score": 0.00,
     "effort": "1 day"},
    {"step": 2, "action": "Design API and agent architecture",
     "technology": "FastAPI", "skill_strength_score": 5.50,
     "effort": "2 days"},
    {"step": 3, "action": "Implement LLM and agent integration layer",
     "technology": "LangChain", "skill_strength_score": 4.75,
     "effort": "3 days"},
    {"step": 4, "action": "Build data processing and streaming pipeline",
     "technology": "Python", "skill_strength_score": 7.25,
     "effort": "2 days"},
    {"step": 5, "action": "Validate QA, testing, and guardrail behavior",
     "technology": "QA", "skill_strength_score": 0.00,
     "effort": "2 days"},
    {"step": 6, "action": "Plan release and deploy backend to cloud",
     "technology": "AWS", "skill_strength_score": 6.50,
     "effort": "1 day"},
]


def get_mock_search_results(problem: str) -> dict:
    """Return mock web search + skill extraction results."""
    return MOCK_SEARCH_RESULTS


def get_mock_solution(problem: str, tech_ranking: list[dict]) -> list[dict]:
    """Return mock generic solution."""
    return MOCK_SOLUTION

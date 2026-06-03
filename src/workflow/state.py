"""Pipeline state for the LangGraph workflow.

This is a TypedDict used as a TYPE HINT only. At runtime, state is a
plain dict. Each node reads keys and returns a dict with updated keys.
"""
from typing import TypedDict


class PipelineState(TypedDict, total=False):
    """State that flows through the LangGraph pipeline nodes."""
    # Input
    problem_statement: str
    language: str
    model_name: str
    cached_search_results: dict
    override_steps: list
    translated_problem: str

    # Node 1: Load Resources
    users: list[dict]
    skills: list[dict]
    levels: list[dict]
    user_skills: list[dict]

    # Node 2: Web Search + LLM Skill Extraction
    search_results: dict

    # Node 3: Compute Strength
    skill_strength_scores: list[dict]

    # Node 4: Generate Solution
    generic_solution: list[dict]

    # Node 5: Score + Rank
    ranked_resources: list[dict]
    task_recommendations: list[dict]

    # Node 6: Report
    report_bytes: bytes

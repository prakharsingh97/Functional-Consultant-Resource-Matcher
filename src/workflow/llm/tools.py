"""Tavily search tool for web search."""
import os
from tavily import TavilyClient


def tavily_search(query: str) -> dict:
    """Search the web using Tavily.

    Args:
        query: Search query string.

    Returns:
        Raw Tavily response dict with "results" key.
    """
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    return client.search(query[:400], search_depth="basic", max_results=5)


def mock_tavily_search(query: str) -> dict:
    """Return mock search results for testing."""
    return {
        "results": [
            {"title": "AI Platform Architecture",
             "content": "Requires Python, FastAPI, AWS for deployment"},
            {"title": "LLM Integration Guide",
             "content": "LangChain recommended for LLM orchestration"},
            {"title": "Legal Tech Stack",
             "content": "Document processing with Python, cloud hosting"},
        ]
    }

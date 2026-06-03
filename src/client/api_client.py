"""Thin client factory. Returns mock or HTTP client."""
import os


def get_client():
    """Return the appropriate client based on env.

    TESTING: MockAPIClient (no server needed).
    Live: HttpClient (calls FastAPI via httpx).
    """
    if os.getenv("env", "TESTING") == "TESTING":
        from src.client.mock_client import MockAPIClient
        return MockAPIClient()
    from src.client.http_client import HttpClient
    return HttpClient()

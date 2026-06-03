"""LLM client factory. Returns mock or real OpenRouter client based on env."""
import os
from openai import OpenAI

FALLBACK_MODEL = "openrouter/free"


def get_model_name() -> str:
    """Return the LLM model name from env, with openrouter/free fallback."""
    return os.getenv("DEFAULT_LLM", FALLBACK_MODEL)


def get_llm_client() -> OpenAI:
    """Return an OpenAI client pointing to OpenRouter."""
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )


def is_testing() -> bool:
    """Check if LLM calls should be mocked."""
    return os.getenv("env", "TESTING") == "TESTING"

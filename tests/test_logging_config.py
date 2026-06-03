"""Tests for shared console logging configuration."""
import logging

from src.logging_config import configure_logging


def test_configure_logging_keeps_src_info_and_quiets_dependencies(
    monkeypatch,
):
    """App logs stay verbose while dependency request logs are quieter."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("THIRD_PARTY_LOG_LEVEL", "WARNING")

    configure_logging()

    assert logging.getLogger("src").level == logging.INFO
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("sentence_transformers").level == logging.WARNING
    assert logging.getLogger("transformers_modules").level == logging.WARNING

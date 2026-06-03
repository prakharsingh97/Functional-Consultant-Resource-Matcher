"""Shared console logging setup for UI and API processes."""
import logging
import os


def configure_logging() -> None:
    """Configure human-readable console logs once per process."""
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    third_party_level_name = os.getenv(
        "THIRD_PARTY_LOG_LEVEL", "WARNING",
    ).upper()
    third_party_level = getattr(
        logging, third_party_level_name, logging.WARNING,
    )
    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s %(levelname)s %(name)s "
            "[%(process)d] %(message)s"
        ),
    )
    logging.getLogger("src").setLevel(level)
    for logger_name in (
        "httpx",
        "httpcore",
        "huggingface_hub",
        "sentence_transformers",
        "transformers",
        "transformers_modules",
        "urllib3",
    ):
        logging.getLogger(logger_name).setLevel(third_party_level)

"""JSON file cache for pipeline results (unlimited entries).

Cache file: .pipeline_cache.json at the project root.
Entries are ordered oldest→newest; duplicates for the same prompt are replaced.
report_bytes is stored base64-encoded so it survives JSON serialization.
"""
import base64
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_FILE = Path(__file__).resolve().parent.parent.parent / ".pipeline_cache.json"


def get_cached_result(prompt: str) -> dict | None:
    """Return the cached pipeline result for this prompt, or None on miss."""
    for entry in _load():
        if entry.get("prompt") == prompt:
            result = entry["result"].copy()
            rb = result.get("report_bytes", "")
            if isinstance(rb, str):
                result["report_bytes"] = base64.b64decode(rb)
            result["_from_cache"] = True
            logger.info("cache.hit prompt_length=%s", len(prompt))
            return result
    logger.info("cache.miss prompt_length=%s", len(prompt))
    return None


def save_to_cache(prompt: str, result: dict) -> None:
    """Add result to cache. Replaces any existing entry for the same prompt."""
    cache = [e for e in _load() if e.get("prompt") != prompt]
    serializable = {
        k: (base64.b64encode(v).decode() if isinstance(v, bytes) else v)
        for k, v in result.items()
        if k != "_from_cache"
    }
    cache.append({"prompt": prompt, "result": serializable})
    _save(cache)
    logger.info("cache.saved entries=%s prompt_length=%s", len(cache), len(prompt))


def get_all_cached() -> list[dict]:
    """Return deduplicated cache entries (latest per prompt), oldest→newest."""
    seen: dict[str, dict] = {}
    for entry in _load():
        seen[entry.get("prompt", "")] = entry   # latest wins
    return list(seen.values())


def delete_from_cache(prompt: str) -> None:
    """Remove a single cache entry by prompt (no-op if not found)."""
    cache = [e for e in _load() if e.get("prompt") != prompt]
    _save(cache)
    logger.info("cache.deleted remaining=%s", len(cache))


def cache_size() -> int:
    """Return the number of entries currently in the cache."""
    return len(_load())


def _load() -> list:
    try:
        if CACHE_FILE.exists():
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                # Deduplicate on load — keeps the last entry for each prompt
                seen: dict[str, dict] = {}
                for entry in data:
                    seen[entry.get("prompt", "")] = entry
                entries = list(seen.values())
                if len(entries) < len(data):
                    _save(entries)   # write back the cleaned file
                return entries
    except Exception:
        logger.warning("cache.load_failed", exc_info=True)
    return []


def _save(cache: list) -> None:
    try:
        CACHE_FILE.write_text(
            json.dumps(cache, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        logger.warning("cache.save_failed", exc_info=True)

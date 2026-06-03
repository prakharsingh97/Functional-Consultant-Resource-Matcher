"""Semantic skill matching via nomic-embed-text-v1.5 embeddings.

Uses sentence-transformers for CPU-optimized embedding computation.
Model is loaded once and cached for subsequent calls.
In TESTING mode, uses fast mock similarity (substring-based).
"""
import logging

import numpy as np
from src.workflow.llm.client import is_testing

SIMILARITY_THRESHOLD = 0.5
FALLBACK_TOP_K = 3

logger = logging.getLogger(__name__)
_model = None
_model_load_error: Exception | None = None


def _get_model():
    """Load and cache the sentence-transformers model."""
    global _model, _model_load_error
    if _model_load_error is not None:
        raise RuntimeError(
            "embedding model unavailable; using lexical fallback"
        ) from _model_load_error
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(
                "nomic-ai/nomic-embed-text-v1.5",
                trust_remote_code=True,
                device="cpu",
            )
            logger.info("embeddings.model_loaded name=nomic-embed-text-v1.5")
        except Exception as exc:
            _model_load_error = exc
            logger.warning(
                "embeddings.model_unavailable fallback=lexical error=%s",
                exc,
            )
            raise
    return _model


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(dot / norm) if norm > 0 else 0.0


def match_skills_semantic(
    required_skills: list[str],
    db_skills: list[str],
) -> list[dict]:
    """Match DB skills to required skills using semantic similarity.

    For each DB skill, computes the max similarity across all
    required skills. Marks as matched if similarity > threshold.
    Falls back to top_k if nothing exceeds threshold.

    Args:
        required_skills: Skills extracted by LLM from web search.
        db_skills: Skill names from the Excel database.

    Returns:
        List of {skill_name, similarity, matched} for each db_skill.
    """
    if is_testing():
        return _mock_match_skills(required_skills, db_skills)

    if not required_skills or not db_skills:
        return [
            {"skill_name": s, "similarity": 0.0, "matched": False}
            for s in db_skills
        ]

    try:
        model = _get_model()
        req_embeddings = model.encode(required_skills)
        db_embeddings = model.encode(db_skills)
    except Exception:
        logger.info(
            "embeddings.fallback_match required_skills=%s db_skills=%s",
            len(required_skills), len(db_skills),
        )
        return _fallback_match_skills(required_skills, db_skills)

    results = []
    for i, db_name in enumerate(db_skills):
        max_sim = 0.0
        for j in range(len(required_skills)):
            sim = _cosine_similarity(
                db_embeddings[i], req_embeddings[j],
            )
            max_sim = max(max_sim, sim)
        results.append({
            "skill_name": db_name,
            "similarity": round(max_sim, 4),
            "matched": max_sim > SIMILARITY_THRESHOLD,
        })

    # Fallback: if nothing matched, pick top_k
    any_matched = any(r["matched"] for r in results)
    if not any_matched and len(results) > 0:
        results.sort(key=lambda x: x["similarity"], reverse=True)
        for i in range(min(FALLBACK_TOP_K, len(results))):
            results[i]["matched"] = True

    return results


def _mock_match_skills(
    required_skills: list[str], db_skills: list[str],
) -> list[dict]:
    """Return mock similarity scores for testing.

    Uses simple substring matching to simulate semantic similarity.
    Exact match → 0.95, substring → 0.75, no match → 0.3.
    """
    results = []
    for db_name in db_skills:
        best_sim = 0.0
        for req in required_skills:
            if db_name.lower() == req.lower():
                best_sim = max(best_sim, 0.95)
            elif (db_name.lower() in req.lower()
                  or req.lower() in db_name.lower()):
                best_sim = max(best_sim, 0.75)
            else:
                best_sim = max(best_sim, 0.3)
        results.append({
            "skill_name": db_name,
            "similarity": round(best_sim, 4),
            "matched": best_sim > SIMILARITY_THRESHOLD,
        })

    any_matched = any(r["matched"] for r in results)
    if not any_matched and len(results) > 0:
        results.sort(key=lambda x: x["similarity"], reverse=True)
        for i in range(min(FALLBACK_TOP_K, len(results))):
            results[i]["matched"] = True

    return results


def _fallback_match_skills(
    required_skills: list[str], db_skills: list[str],
) -> list[dict]:
    """Return lightweight lexical matches if embeddings are unavailable."""
    required_tokens = [
        set(req.lower().replace("-", " ").split())
        for req in required_skills
    ]
    results = []
    for db_name in db_skills:
        db_tokens = set(db_name.lower().replace("-", " ").split())
        best_sim = 0.0
        for req, req_tokens in zip(required_skills, required_tokens):
            req_lower = req.lower()
            db_lower = db_name.lower()
            if db_lower == req_lower:
                best_sim = max(best_sim, 0.95)
            elif db_lower in req_lower or req_lower in db_lower:
                best_sim = max(best_sim, 0.75)
            elif db_tokens and req_tokens:
                overlap = len(db_tokens & req_tokens)
                union = len(db_tokens | req_tokens)
                best_sim = max(best_sim, overlap / union)
        results.append({
            "skill_name": db_name,
            "similarity": round(best_sim, 4),
            "matched": best_sim > SIMILARITY_THRESHOLD,
        })

    any_matched = any(r["matched"] for r in results)
    if not any_matched and len(results) > 0:
        results.sort(key=lambda x: x["similarity"], reverse=True)
        for i in range(min(FALLBACK_TOP_K, len(results))):
            results[i]["matched"] = True

    return results

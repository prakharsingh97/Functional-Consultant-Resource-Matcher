"""Tests for semantic skill matching via embeddings."""
import src.workflow.llm.embeddings as embeddings
from src.workflow.llm.embeddings import match_skills_semantic


def test_match_skills_returns_similarity_scores():
    required = ["Machine Learning", "Cloud Computing"]
    db_skills = ["Python", "AWS", "TensorFlow", "Docker"]
    matches = match_skills_semantic(required, db_skills)
    assert len(matches) == len(db_skills)
    for m in matches:
        assert "skill_name" in m
        assert "similarity" in m
        assert 0.0 <= m["similarity"] <= 1.0


def test_match_skills_above_threshold():
    """Skills above threshold should be marked as matched."""
    required = ["Python"]
    db_skills = ["Python", "Docker", "Java"]
    matches = match_skills_semantic(required, db_skills)
    python_match = next(
        m for m in matches if m["skill_name"] == "Python"
    )
    assert python_match["matched"] is True


def test_match_skills_fallback_topk():
    """If nothing matches threshold, top_k should still return results."""
    required = ["Quantum Computing"]
    db_skills = ["Python", "Excel", "Docker"]
    matches = match_skills_semantic(required, db_skills)
    assert len(matches) > 0


def test_match_skills_falls_back_when_embedding_model_fails(
    monkeypatch,
):
    """Live mode falls back to lexical matching if embeddings fail."""
    monkeypatch.setenv("env", "LOCAL")

    def fail_model():
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(embeddings, "_get_model", fail_model)

    matches = match_skills_semantic(
        ["Python agents"],
        ["Python", "Excel", "Docker"],
    )
    python_match = next(
        m for m in matches if m["skill_name"] == "Python"
    )
    assert python_match["matched"] is True


def test_embedding_model_failure_is_cached(monkeypatch):
    """Repeated live calls should not reload a known-broken model."""
    monkeypatch.setenv("env", "LOCAL")
    monkeypatch.setattr(embeddings, "_model", None)
    monkeypatch.setattr(embeddings, "_model_load_error", None)

    calls = {"count": 0}

    class BrokenSentenceTransformer:
        def __init__(self, *_args, **_kwargs):
            calls["count"] += 1
            raise RuntimeError("missing dependency")

    monkeypatch.setattr(
        "sentence_transformers.SentenceTransformer",
        BrokenSentenceTransformer,
    )

    match_skills_semantic(["Python"], ["Python", "Docker"])
    match_skills_semantic(["FastAPI"], ["FastAPI", "React"])

    assert calls["count"] == 1

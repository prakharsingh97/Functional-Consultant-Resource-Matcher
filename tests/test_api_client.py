"""Tests for API clients."""
import base64
import json

import httpx

from src.client.http_client import HttpClient, PipelineStreamError
from src.client.mock_client import MockAPIClient


def test_mock_client_get_users():
    client = MockAPIClient()
    users = client.get_users()
    assert len(users) > 0
    # Must match User model shape
    assert "user_id" in users[0]
    assert "full_name" in users[0]
    assert "email" in users[0]
    assert "role" in users[0]
    assert "availability" in users[0]
    assert "timezone" in users[0]
    assert "created_at" in users[0]


def test_mock_client_get_skills():
    client = MockAPIClient()
    skills = client.get_skills()
    assert len(skills) > 0
    # Must match Skill model shape
    assert "skill_id" in skills[0]
    assert "skill_name" in skills[0]
    assert "category" in skills[0]


def test_mock_client_get_skill_strength():
    client = MockAPIClient()
    scores = client.get_skill_strength()
    assert len(scores) > 0
    # Must match SkillStrength model shape, sorted desc
    assert "skill_id" in scores[0]
    assert "skill_name" in scores[0]
    assert "category" in scores[0]
    assert "strength_score" in scores[0]
    assert scores[0]["strength_score"] >= scores[1]["strength_score"]


def test_mock_client_get_levels():
    client = MockAPIClient()
    levels = client.get_levels()
    assert len(levels) == 4
    # Must match Level model shape
    assert "level_id" in levels[0]
    assert "level_name" in levels[0]
    assert "score_weight" in levels[0]


def test_mock_client_run_pipeline():
    client = MockAPIClient()
    result = client.run_pipeline("Build a legal AI platform")
    assert "problem" in result
    assert "solution" in result
    assert "resources" in result
    assert "risk_flags" in result
    assert "report_bytes" in result
    assert isinstance(result["report_bytes"], bytes)


def test_mock_client_generate_report():
    client = MockAPIClient()
    report_bytes = client.generate_report({
        "problem": "Test problem",
        "solution": [
            {"step": 1, "action": "Do X", "technology": "Python",
             "skill_strength_score": 5.0},
        ],
        "resources": [
            {"user_id": "U01", "full_name": "Alice", "fit_score": 0.9,
             "priority": "P1", "availability": 30},
        ],
        "risk_flags": [],
    })
    assert isinstance(report_bytes, bytes)
    assert len(report_bytes) > 0


def test_http_client_consumes_pipeline_sse():
    """HttpClient consumes step/progress/complete events from SSE."""
    report_bytes = b"docx bytes"
    events = [
        {"type": "progress", "data": {"status": "Loading database..."}},
        {"type": "step", "node": "load_resources", "step_index": 0},
        {
            "type": "complete",
            "result": {
                "problem": "Build a data pipeline",
                "model_name": "test-model",
                "solution": [],
                "resources": [],
                "risk_flags": [],
                "report_bytes": base64.b64encode(report_bytes).decode(),
            },
        },
    ]
    body = "".join(
        f"data: {json.dumps(event)}\n\n" for event in events
    ) + "data: [DONE]\n\n"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/pipeline/stream"
        return httpx.Response(200, content=body)

    steps = []
    progress = []
    client = HttpClient(
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )

    result = client.run_pipeline(
        "Build a data pipeline",
        on_step=lambda node, idx: steps.append((node, idx)),
        on_progress=progress.append,
    )

    assert steps == [("load_resources", 0)]
    assert progress == [{"status": "Loading database..."}]
    assert result["model_name"] == "test-model"
    assert result["report_bytes"] == report_bytes


def test_http_client_raises_for_pipeline_error_event():
    """HttpClient raises a clear error for backend SSE error events."""
    body = (
        'data: {"type": "error", "error_type": "ValueError", '
        '"message": "bad pipeline state"}\n\n'
        "data: [DONE]\n\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    client = HttpClient(
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )

    try:
        client.run_pipeline("Build a data pipeline")
    except PipelineStreamError as exc:
        assert "ValueError: bad pipeline state" in str(exc)
    else:
        raise AssertionError("Expected PipelineStreamError")


def test_http_client_health_check_returns_true_for_ok():
    """HttpClient health_check returns True for 200 health response."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/pipeline/health"
        return httpx.Response(200, json={"status": "ok"})

    client = HttpClient(
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )

    assert client.health_check() is True


def test_http_client_health_check_returns_false_on_connect_error():
    """HttpClient health_check returns False when backend is unreachable."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("not running", request=request)

    client = HttpClient(
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )

    assert client.health_check() is False

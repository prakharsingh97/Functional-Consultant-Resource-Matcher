"""Smoke tests for the pipeline SSE streaming route.

Uses FastAPI TestClient with env=TESTING so the pipeline
runs with mocked LLM/embedding calls.
"""
import json
import base64
from src.api.app import create_app
from src.api.routes import pipeline
from fastapi.testclient import TestClient


def _stream_events(client: TestClient, problem: str) -> list:
    """Helper: POST to /v1/pipeline/stream and collect SSE events."""
    events = []
    with client.stream(
        "POST",
        "/v1/pipeline/stream",
        json={"problem_statement": problem},
    ) as resp:
        for line in resp.iter_lines():
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                break
            events.append(json.loads(payload))
    return events


def test_pipeline_health_returns_ok():
    """GET /v1/pipeline/health returns 200 with status ok."""
    app = create_app()
    client = TestClient(app)
    resp = client.get("/v1/pipeline/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_pipeline_stream_returns_step_events():
    """POST /v1/pipeline/stream yields step events for each node."""
    app = create_app()
    client = TestClient(app)
    events = _stream_events(client, "Build a data pipeline")
    step_events = [e for e in events if e["type"] == "step"]
    assert len(step_events) > 0
    # First step should be load_resources
    assert step_events[0]["node"] == "load_resources"
    assert step_events[0]["step_index"] == 0


def test_pipeline_stream_returns_complete_event():
    """POST /v1/pipeline/stream ends with a complete event."""
    app = create_app()
    client = TestClient(app)
    events = _stream_events(client, "Build a data pipeline")
    complete = [e for e in events if e["type"] == "complete"]
    assert len(complete) == 1
    result = complete[0]["result"]
    assert "problem" in result
    assert "solution" in result
    assert "resources" in result
    assert "task_recommendations" in result
    assert "report_bytes" in result


def test_pipeline_stream_report_bytes_is_base64():
    """Complete event report_bytes decodes to valid bytes."""
    app = create_app()
    client = TestClient(app)
    events = _stream_events(client, "Build a data pipeline")
    complete = [e for e in events if e["type"] == "complete"][0]
    raw = base64.b64decode(complete["result"]["report_bytes"])
    assert len(raw) > 0
    # .docx files start with PK (zip header)
    assert raw[:2] == b"PK"


def test_pipeline_stream_missing_problem_422():
    """POST with empty body returns 422 validation error."""
    app = create_app()
    client = TestClient(app)
    resp = client.post("/v1/pipeline/stream", json={})
    assert resp.status_code == 422


def test_pipeline_stream_has_model_name():
    """Complete event includes the model_name field."""
    app = create_app()
    client = TestClient(app)
    events = _stream_events(client, "Build a data pipeline")
    complete = [e for e in events if e["type"] == "complete"][0]
    assert "model_name" in complete["result"]


def test_pipeline_stream_returns_error_event_on_exception(monkeypatch):
    """Pipeline stream returns a structured error instead of dropping."""
    class BrokenGraph:
        def stream(self, *_args, **_kwargs):
            yield {
                "type": "custom",
                "data": {"status": "Starting..."},
            }
            raise RuntimeError("semantic matcher failed")

    monkeypatch.setattr(pipeline, "build_pipeline", lambda: BrokenGraph())

    app = create_app()
    client = TestClient(app)
    events = _stream_events(client, "Build a data pipeline")
    error = [e for e in events if e["type"] == "error"]
    assert len(error) == 1
    assert error[0]["error_type"] == "RuntimeError"
    assert "semantic matcher failed" in error[0]["message"]

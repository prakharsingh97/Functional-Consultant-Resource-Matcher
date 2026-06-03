"""Pipeline SSE streaming endpoint.

Streams LangGraph pipeline execution via Server-Sent Events using
combined updates+custom stream mode. Each node completion emits a
step event; get_stream_writer() calls emit progress events.
"""
import json
import base64
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.models.schemas import PipelineRequest
from src.workflow.graph import build_pipeline

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
logger = logging.getLogger(__name__)

# Node name -> workflow step index (mirrors src/ui/components.py)
NODE_STEP_MAP = {
    "load_resources": 0,
    "web_search": 1,
    "compute_strength": 2,
    "generate_solution": 3,
    "score_resources": 3,
    "generate_report": 4,
}


@router.get("/health")
def health():
    """Health check. Returns ok if the API server is running."""
    return {"status": "ok"}


@router.post("/stream")
def stream_pipeline(request: PipelineRequest):
    """Stream pipeline execution as SSE events.

    Yields three event types:
    - step: a pipeline node completed
    - progress: custom progress message from a node
    - complete: final result with base64-encoded report

    Terminal [DONE] event prevents client auto-reconnect.
    """
    logger.info(
        "pipeline.request_start problem_length=%s problem_preview=%r language=%s",
        len(request.problem_statement),
        request.problem_statement[:120],
        request.language,
    )
    return StreamingResponse(
        _event_generator(
            request.problem_statement, request.language,
            request.cached_search_results, request.override_steps,
            request.translated_problem,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _event_generator(
    problem_statement: str,
    language: str = "English",
    cached_search_results: dict | None = None,
    override_steps: list | None = None,
    translated_problem: str = "",
):
    """Generate SSE events from the LangGraph pipeline stream."""
    last_state = {}

    try:
        graph = build_pipeline()
        for chunk in graph.stream(
            {
                "problem_statement": problem_statement,
                "language": language,
                "cached_search_results": cached_search_results or {},
                "override_steps": override_steps or [],
                "translated_problem": translated_problem or problem_statement,
            },
            stream_mode=["updates", "custom"],
            version="v2",
        ):
            chunk_type = chunk.get("type")

            if chunk_type == "updates":
                for node_name, state in chunk.get("data", {}).items():
                    step_idx = NODE_STEP_MAP.get(node_name)
                    if step_idx is not None:
                        event = {
                            "type": "step",
                            "node": node_name,
                            "step_index": step_idx,
                        }
                        logger.info(
                            "pipeline.emit_step node=%s step_index=%s",
                            node_name, step_idx,
                        )
                        yield _sse(event)
                    last_state = state

            elif chunk_type == "custom":
                event = {
                    "type": "progress",
                    "data": chunk.get("data", {}),
                }
                logger.info(
                    "pipeline.emit_progress status=%r",
                    event["data"].get("status"),
                )
                yield _sse(event)

        result = _extract_result(problem_statement, last_state)
        raw_bytes = result.pop("report_bytes", b"")
        result["report_bytes"] = base64.b64encode(raw_bytes).decode()
        logger.info(
            "pipeline.emit_complete solution_steps=%s resources=%s "
            "tasks=%s risk_flags=%s report_bytes=%s model=%s",
            len(result.get("solution", [])),
            len(result.get("resources", [])),
            len(result.get("task_recommendations", [])),
            len(result.get("risk_flags", [])),
            len(raw_bytes),
            result.get("model_name"),
        )
        yield _sse({"type": "complete", "result": result})
    except Exception as exc:
        logger.exception("Pipeline stream failed")
        event = {
            "type": "error",
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        }
        logger.info(
            "pipeline.emit_error error_type=%s message=%r",
            event["error_type"], event["message"],
        )
        yield _sse(event)
    logger.info("pipeline.emit_done")
    yield "data: [DONE]\n\n"


def _sse(data: dict) -> str:
    """Format a dict as an SSE frame."""
    return f"data: {json.dumps(data)}\n\n"


def _extract_result(problem: str, state: dict) -> dict:
    """Extract structured result from pipeline state."""
    risk_flags = [
        {
            "user_id": "",
            "reason": f"No recommended resources for {task.get('task')}",
        }
        for task in state.get("task_recommendations", [])
        if not task.get("resources")
    ]
    return {
        "problem": problem,
        "model_name": state.get("model_name", "unknown"),
        "solution": state.get("generic_solution", []),
        "resources": state.get("ranked_resources", []),
        "task_recommendations": state.get("task_recommendations", []),
        "risk_flags": risk_flags,
        "report_bytes": state.get("report_bytes", b""),
        "search_results": state.get("search_results", {}),
        "skill_strength_scores": state.get("skill_strength_scores", []),
    }

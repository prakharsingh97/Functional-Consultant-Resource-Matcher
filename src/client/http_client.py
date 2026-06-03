"""HTTP client that calls the FastAPI backend via httpx.

Consumes the SSE stream from POST /v1/pipeline/stream,
decodes base64 report_bytes, and provides on_step/on_progress
callbacks for real-time Streamlit UI updates.
"""
import os
import json
import base64
import logging
import httpx

logger = logging.getLogger(__name__)


class PipelineStreamError(RuntimeError):
    """Raised when the backend pipeline stream fails."""


class HttpClient:
    """HTTP client calling the FastAPI backend via httpx."""

    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        self.base_url = base_url or os.getenv(
            "API_BASE_URL", "http://localhost:8000"
        )
        self._client = httpx.Client(timeout=300.0, transport=transport)

    def run_pipeline(
        self,
        problem_statement: str,
        on_step=None,
        on_progress=None,
        language: str = "English",
        cached_search_results: dict | None = None,
        override_steps: list | None = None,
        translated_problem: str = "",
    ) -> dict:
        """POST to /v1/pipeline/stream, consume SSE events.

        Args:
            problem_statement: The user's problem description.
            on_step: Optional callback(node_name, step_index) per
                     node completion.
            on_progress: Optional callback(data) for custom progress
                         messages from get_stream_writer().

        Returns:
            Dict with problem, model_name, solution, resources,
            risk_flags, report_bytes (bytes, decoded from base64).
        """
        result = {}
        logger.info(
            "client.pipeline_start base_url=%s problem_length=%s",
            self.base_url, len(problem_statement),
        )
        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/v1/pipeline/stream",
                json={
                    "problem_statement": problem_statement,
                    "language": language,
                    "cached_search_results": cached_search_results or {},
                    "override_steps": override_steps or [],
                    "translated_problem": translated_problem or "",
                },
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload == "[DONE]":
                        break
                    try:
                        event = json.loads(payload)
                    except json.JSONDecodeError:
                        continue

                    evt_type = event.get("type")
                    if evt_type == "step" and on_step:
                        logger.info(
                            "client.recv_step node=%s step_index=%s",
                            event["node"], event["step_index"],
                        )
                        on_step(event["node"], event["step_index"])
                    elif evt_type == "progress" and on_progress:
                        data = event.get("data", {})
                        logger.info(
                            "client.recv_progress status=%r",
                            data.get("status"),
                        )
                        on_progress(data)
                    elif evt_type == "complete":
                        result = event["result"]
                        if "report_bytes" in result:
                            result["report_bytes"] = base64.b64decode(
                                result["report_bytes"]
                            )
                        logger.info(
                            "client.recv_complete solution_steps=%s "
                            "resources=%s risk_flags=%s report_bytes=%s "
                            "model=%s",
                            len(result.get("solution", [])),
                            len(result.get("resources", [])),
                            len(result.get("risk_flags", [])),
                            len(result.get("report_bytes", b"")),
                            result.get("model_name"),
                        )
                    elif evt_type == "error":
                        message = event.get(
                            "message", "Pipeline stream failed"
                        )
                        error_type = event.get("error_type", "Error")
                        logger.error(
                            "client.recv_error error_type=%s message=%r",
                            error_type, message,
                        )
                        raise PipelineStreamError(
                            f"{error_type}: {message}"
                        )
        except httpx.RemoteProtocolError as exc:
            logger.exception("client.remote_protocol_error")
            raise PipelineStreamError(
                "API stream ended unexpectedly before completion. "
                "Check the FastAPI server logs for the pipeline error."
            ) from exc
        logger.info("client.pipeline_done has_result=%s", bool(result))
        return result

    def health_check(self) -> bool:
        """Check if the API server is reachable.

        Returns:
            True if health endpoint returns 200, False otherwise.
        """
        try:
            resp = self._client.get(
                f"{self.base_url}/v1/pipeline/health",
                timeout=2.0,
            )
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

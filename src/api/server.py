"""Server startup helper for the FastAPI backend.

Starts uvicorn as a background subprocess and checks if the
server is already running via the health endpoint.
"""
import logging
import subprocess
import sys
import httpx

logger = logging.getLogger(__name__)


def start_server(
    host: str = "127.0.0.1", port: int = 8000,
) -> subprocess.Popen:
    """Start FastAPI server as background subprocess via uvicorn.

    Args:
        host: Bind address.
        port: Bind port.

    Returns:
        The subprocess.Popen handle for the uvicorn process.
    """
    logger.info("api.start host=%s port=%s", host, port)
    return subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "src.api.app:create_app", "--factory",
            "--host", host, "--port", str(port),
        ]
    )


def is_server_running(url: str = "http://localhost:8000") -> bool:
    """Check if the API server is reachable via health endpoint.

    Args:
        url: Base URL of the FastAPI server.

    Returns:
        True if /v1/pipeline/health returns 200, False otherwise.
    """
    try:
        resp = httpx.get(
            f"{url}/v1/pipeline/health", timeout=2.0,
        )
        is_running = resp.status_code == 200
        logger.info(
            "api.health_check url=%s status_code=%s running=%s",
            url, resp.status_code, is_running,
        )
        return is_running
    except (httpx.ConnectError, httpx.TimeoutException):
        logger.info("api.health_check url=%s running=false", url)
        return False

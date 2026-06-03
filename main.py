"""Run the FastAPI backend and Streamlit UI together for local demos."""
import signal
import subprocess
import sys
import time

import httpx

API_URL = "http://127.0.0.1:8000"


def _wait_for_api(timeout_seconds: float = 15.0) -> None:
    """Wait until the FastAPI health endpoint responds."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            resp = httpx.get(f"{API_URL}/v1/pipeline/health", timeout=1.0)
            if resp.status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(0.5)
    raise RuntimeError("FastAPI server did not become healthy in time")


def _terminate(processes: list[subprocess.Popen]) -> None:
    """Terminate child processes gracefully."""
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        if process.poll() is None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def main() -> int:
    """Start API and UI with one command."""
    api = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "src.api.app:create_app", "--factory",
        "--host", "127.0.0.1",
        "--port", "8000",
    ])
    processes = [api]

    def _handle_signal(_signum, _frame):
        _terminate(processes)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        _wait_for_api()
        ui = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run",
            "src/ui/app.py",
            "--server.port", "8501",
        ])
        processes.append(ui)
        print("FastAPI:   http://127.0.0.1:8000/docs")
        print("Streamlit: http://localhost:8501")
        return ui.wait()
    finally:
        _terminate(processes)


if __name__ == "__main__":
    raise SystemExit(main())

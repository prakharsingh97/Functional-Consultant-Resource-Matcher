"""Node 6: Generate the final .docx report."""
from src.workflow.utils import get_writer
from src.reports.docx_generator import generate_report_bytes


def generate_report(state: dict) -> dict:
    """Generate a .docx report from pipeline results.

    Args:
        state: Pipeline state with solution, resources, risk data.

    Returns:
        Updated state with report_bytes populated.
    """
    writer = get_writer()
    writer({"status": "Generating .docx report..."})

    risk_flags = [
        {
            "task_id": task.get("task_id"),
            "reason": (
                f"No recommended resources for {task.get('task')}"
            ),
        }
        for task in state.get("task_recommendations", [])
        if not task.get("resources")
    ]
    data = {
        "problem": state.get("translated_problem") or state.get("problem_statement", ""),
        "solution": state.get("generic_solution", []),
        "resources": state.get("ranked_resources", []),
        "task_recommendations": state.get("task_recommendations", []),
        "risk_flags": risk_flags,
    }
    language = state.get("language", "English")
    report_bytes = generate_report_bytes(data, language)
    writer({"status": "Report ready"})
    return {**state, "report_bytes": report_bytes}

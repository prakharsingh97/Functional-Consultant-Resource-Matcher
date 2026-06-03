"""Streamlit chat interface for the Resource Matcher. Single screen."""
import html
import logging
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path for `src.*` imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(override=True)

import streamlit as st
from src.ui.styles import apply_theme
from src.ui.components import (
    get_labels, get_workflow_steps, translate_progress,
    format_solution_step, format_resource_card,
    format_task_recommendation,
)
from src.workflow.llm.client import is_testing
from src.client.mock_client import MockAPIClient
from src.client.api_client import get_client
from src.client.http_client import PipelineStreamError
from src.api.server import is_server_running, start_server
from src.logging_config import configure_logging
from src.workflow.llm.client import get_model_name, get_llm_client
from src.cache.prompt_cache import (
    get_cached_result, save_to_cache, cache_size, get_all_cached, delete_from_cache,
)

configure_logging()
logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HEADER_IMAGE = PROJECT_ROOT / "ey-asset-bot-image.jpeg"

LANGUAGES = [
    "English", "French", "German", "Spanish", "Portuguese",
    "Hindi", "Arabic", "Japanese", "Chinese (Simplified)",
]


def main():
    """Run the Streamlit app."""
    st.set_page_config(
        page_title="Resource Matcher",
        page_icon=str(HEADER_IMAGE) if HEADER_IMAGE.exists() else None,
        layout="wide",
    )
    apply_theme()

    # Resolve language early so lb is available throughout main()
    selected_language = st.session_state.get("language", "English")
    lb = get_labels(selected_language)

    _render_header(lb)
    st.caption(lb.get("app_subtitle", "Describe your project problem and get matched consultant resources."))

    # ── Sidebar: language + cache info + history ────────────────────────────
    with st.sidebar:
        search_query = st.text_input(
            "search",
            placeholder=lb.get("search_placeholder", "🔍 Search history…"),
            label_visibility="collapsed",
            key="history_search",
        )

        if st.button(lb.get("new_chat_btn", "🗨️ New Chat"), use_container_width=True, type="primary"):
            for key in ["messages", "report_bytes", "last_result",
                        "edited_steps", "added_steps", "editing", "processing"]:
                st.session_state.pop(key, None)
            st.rerun()

        cached_entries = get_all_cached()
        if search_query:
            cached_entries = [
                e for e in cached_entries
                if search_query.lower() in e.get("prompt", "").lower()
            ]

        if cached_entries:
            st.markdown("---")
            st.markdown(f"### {lb.get('history_heading', '📋 History')}")
            for i, entry in enumerate(reversed(cached_entries)):
                prompt = entry.get("prompt", "")
                preview = prompt[:33] + "…" if len(prompt) > 33 else prompt
                col_btn, col_eye, col_del = st.columns([5, 0.8, 0.8])
                with col_btn:
                    if st.button(preview, key=f"hist_{i}", use_container_width=True):
                        st.session_state["_pending_history"] = prompt
                        st.rerun()
                with col_eye:
                    if st.button("👁", key=f"hist_eye_{i}",
                                 help=lb.get("preview_help", "Preview"),
                                 use_container_width=True):
                        _history_preview_dialog(prompt, lb)
                with col_del:
                    if st.button("🗑️", key=f"hist_del_{i}",
                                 help=lb.get("delete_help", "Delete from history"),
                                 use_container_width=True):
                        delete_from_cache(prompt)
                        st.rerun()

        st.markdown("---")
        with st.expander(f"⚙️ {lb.get('settings_heading', 'Settings')}", expanded=False):
            selected_language = st.selectbox(
                lb.get("response_language_label", "Response language"),
                LANGUAGES,
                index=LANGUAGES.index(st.session_state.get("language", "English")),
                key="language",
            )
            lb = get_labels(selected_language)  # refresh after selectbox
            st.caption(lb.get("cache_info", "⚡ Cache: {n} prompts stored").format(n=cache_size()))

    # ── Session state init ──────────────────────────────────────────────────
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "report_bytes" not in st.session_state:
        st.session_state.report_bytes = None
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "edited_steps" not in st.session_state:
        st.session_state.edited_steps = {}
    if "editing" not in st.session_state:
        st.session_state.editing = False
    if "added_steps" not in st.session_state:
        st.session_state.added_steps = []
    if "deleted_step_ids" not in st.session_state:
        st.session_state.deleted_step_ids = set()

    # ── Handle deferred actions (history click / force-fresh) ───────────────
    if pending_history := st.session_state.pop("_pending_history", None):
        # Always start a fresh chat when loading from history
        for key in ["messages", "report_bytes", "last_result",
                    "edited_steps", "added_steps", "editing",
                    "processing", "deleted_step_ids"]:
            st.session_state.pop(key, None)
        st.session_state.messages = []  # must re-init before _handle_user_input
        _handle_user_input(pending_history, selected_language)
        return

    # ── Message thread ──────────────────────────────────────────────────────
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            display = msg.get("display", msg["content"])
            original = msg["content"]
            # Show original text as small grey caption when translated
            if display != original:
                lb_cur = get_labels(selected_language)
                st.markdown(
                    f'<p style="text-align:right;color:#888;font-size:0.78rem;'
                    f'margin:0 0 0.2rem 0;font-style:italic;">'
                    f'<span style="color:#aaa;">{html.escape(lb_cur.get("original_label","Original"))}:</span> '
                    f'{html.escape(original)}</p>',
                    unsafe_allow_html=True,
                )
            _render_chat_bubble("user", display)
            # ✏️ Edit + 🔄 Re-run on the same line, right-aligned
            _, col_edit, col_rerun = st.columns([5, 0.55, 0.55])
            with col_edit:
                if st.button("✏️", key=f"edit_q_{i}", help="Edit & re-run",
                             use_container_width=True):
                    _edit_question_dialog(msg["content"])
            with col_rerun:
                if st.button("🔄", key=f"rerun_q_{i}", help="Re-run this question",
                             use_container_width=True):
                    st.session_state["_pending_history"] = msg["content"]
                    st.rerun()
        else:
            raw = msg.get("raw_result")
            if raw:
                content = _format_assistant_result(
                    raw, msg.get("model", ""), selected_language
                )
                _render_chat_bubble("assistant", content)
            else:
                _render_chat_bubble("assistant", msg["content"])

    # ── Edit steps (ABOVE download) ─────────────────────────────────────────
    _render_edit_steps_section(selected_language)

    # ── Download button (disabled while editing) ────────────────────────────
    if st.session_state.report_bytes:
        st.download_button(
            label=lb.get("download_btn", "📥 Download Report (.docx)"),
            data=st.session_state.report_bytes,
            file_name="resource_report.docx",
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.wordprocessingml.document"
            ),
            disabled=st.session_state.editing,
            help=lb.get("finish_editing_hint", "Finish editing before downloading") if st.session_state.editing else "",
        )

    # ── Chat input ──────────────────────────────────────────────────────────
    placeholder_text = (
        lb.get("chat_processing", "⏳ Pipeline running, please wait…")
        if st.session_state.processing
        else lb.get("chat_placeholder", "Describe your project problem…")
    )
    if prompt := st.chat_input(
        placeholder_text,
        disabled=st.session_state.processing,
    ):
        logger.info(
            "ui.prompt_submitted problem_length=%s problem_preview=%r",
            len(prompt), prompt[:120],
        )
        _handle_user_input(prompt, selected_language)


def _translate_for_display(text: str, language: str) -> str:
    """Translate text into the target language for display only.

    Falls back to the original text on any error.
    """
    if language == "English" or is_testing():
        return text
    try:
        llm = get_llm_client()
        response = llm.chat.completions.create(
            model=get_model_name(),
            messages=[{
                "role": "user",
                "content": (
                    f"Translate the following text to {language}. "
                    f"Return only the translated text, nothing else:\n\n{text}"
                ),
            }],
        )
        return response.choices[0].message.content.strip()
    except Exception:
        logger.warning("ui.translate_prompt_failed language=%s", language)
        return text


def _handle_user_input(prompt: str, language: str = "English") -> None:
    """Handle user chat input and run the pipeline."""
    st.session_state.processing = True
    st.session_state.editing = False

    # Show translation status + stop button while translating the prompt
    trans_placeholder = st.empty()
    stop_trans = st.empty()
    if language != "English" and not is_testing():
        lb = get_labels(language)
        trans_placeholder.markdown(f"🔄 {lb.get('translating', f'Translating to {language}…')}")
        _, _col_stop = stop_trans.columns([4, 1])
        with _col_stop:
            if st.button(lb.get("stop_btn", "🛑 Stop"), key="stop_translation", type="primary",
                         use_container_width=True):
                trans_placeholder.empty()
                stop_trans.empty()
                st.session_state.processing = False
                st.rerun()

    display_prompt = _translate_for_display(prompt, language)
    trans_placeholder.empty()
    stop_trans.empty()

    st.session_state.messages.append({
        "role": "user",
        "content": prompt,          # original — used for re-runs, edit dialog
        "display": display_prompt,  # translated — shown in the bubble
    })
    _render_chat_bubble("user", display_prompt)

    cached = get_cached_result(prompt)
    if cached:
        result = cached
        logger.info("ui.cache_hit prompt_length=%s", len(prompt))
    elif is_testing():
        result = _run_mock_pipeline(prompt, language)
    else:
        result = _run_live_pipeline(
            prompt, language,
            translated_problem=display_prompt,  # always pass; backend uses it if non-empty
        )
        if not result.get("error"):
            save_to_cache(prompt, result)

    if result.get("error"):
        logger.error("ui.pipeline_error message=%r", result["error"])
        st.session_state.processing = False
        st.session_state.messages.append({
            "role": "assistant", "content": result["error"],
        })
        _render_chat_bubble("assistant", result["error"])
        return

    model = result.get("model_name", get_model_name())
    assistant_content = _format_assistant_result(result, model, language)
    st.session_state.messages.append({
        "role": "assistant",
        "content": assistant_content,
        "raw_result": result,
        "model": model,
    })
    _render_chat_bubble("assistant", assistant_content)

    st.session_state.report_bytes = result.get("report_bytes")
    st.session_state.last_result = result
    st.session_state.edited_steps = {}
    st.session_state.added_steps = []
    st.session_state.deleted_step_ids = set()

    logger.info(
        "ui.result_rendered solution_steps=%s resources=%s "
        "risk_flags=%s report_bytes=%s model=%s",
        len(result.get("solution", [])),
        len(result.get("resources", [])),
        len(result.get("risk_flags", [])),
        len(result.get("report_bytes", b"")),
        model,
    )
    st.session_state.processing = False
    st.rerun()


@st.dialog("📋 History Preview")
def _history_preview_dialog(prompt: str, lb: dict | None = None) -> None:
    """Show full prompt text with Load and Close options."""
    if lb is None:
        lb = get_labels(st.session_state.get("language", "English"))
    st.markdown(prompt)
    col_load, col_close = st.columns(2)
    with col_load:
        if st.button(lb.get("load_btn", "Load"), type="primary", use_container_width=True):
            st.session_state["_pending_history"] = prompt
            st.rerun()
    with col_close:
        if st.button(lb.get("close_btn", "Close"), use_container_width=True):
            st.rerun()


@st.dialog("✏️ Edit Question")
def _edit_question_dialog(original_prompt: str) -> None:
    """Modal to edit a previous question and re-run the pipeline."""
    lb = get_labels(st.session_state.get("language", "English"))
    st.caption(lb.get("edit_q_caption", "Edit your question below and re-run the pipeline with the updated version."))
    new_prompt = st.text_area(
        "Question",
        value=original_prompt,
        height=200,
        label_visibility="collapsed",
    )
    col_run, col_cancel = st.columns(2)
    with col_run:
        if st.button(lb.get("rerun_btn", "🔄 Re-run"), type="primary", use_container_width=True):
            if new_prompt.strip():
                st.session_state["_pending_history"] = new_prompt.strip()
                st.rerun()
            else:
                st.error("Question cannot be empty.")
    with col_cancel:
        if st.button(lb.get("close_btn", "Close"), use_container_width=True):
            st.rerun()


@st.dialog("➕ Add New Step")
def _add_step_dialog(next_idx: int, language: str) -> None:
    """Modal dialog for adding a new solution step."""
    lb = get_labels(language)
    col_num, col_tech = st.columns([1, 3])
    with col_num:
        step_num = st.number_input(f"{lb['step']} #", value=next_idx, min_value=1, step=1)
    with col_tech:
        technology = st.text_input(lb.get("tech_label", "Technology / Tool"), placeholder="e.g. Python, AWS, Terraform")
    action = st.text_area(lb.get("step_desc_label", "Step description *"), height=100,
                          placeholder=lb.get("step_desc_placeholder", "Describe what this step involves…"))
    effort = st.text_input(lb.get("effort_label", "Estimated effort"),
                           placeholder=lb.get("effort_placeholder", "e.g. 2-3 days"))

    col_add, col_cancel = st.columns(2)
    with col_add:
        if st.button(lb.get("add_step_confirm", "Add Step"), type="primary", use_container_width=True):
            if not action.strip():
                st.error(lb.get("step_desc_required", "Step description is required."))
            else:
                st.session_state.added_steps.append({
                    "step": int(step_num),
                    "action": action.strip(),
                    "technology": technology.strip() or "TBD",
                    "skill_strength_score": 0.0,
                    "effort": effort.strip() or "TBD",
                })
                st.rerun()
    with col_cancel:
        if st.button(lb.get("cancel_btn", "Cancel"), use_container_width=True):
            st.rerun()


def _render_edit_steps_section(language: str) -> None:
    """Toggle-based edit section shown above the download button."""
    last = st.session_state.get("last_result")
    if not last or not last.get("solution"):
        return

    solution = last["solution"]
    lb = get_labels(language)
    editing = st.session_state.get("editing", False)

    if not editing:
        if st.button(lb.get("edit_steps_btn", "✏️ Edit Steps"), use_container_width=False):
            st.session_state.editing = True
            st.rerun()
        return

    # ── Edit mode ───────────────────────────────────────────────────────────
    st.markdown(f"**{lb.get('edit_steps_heading', '✏️ Edit Steps')}**")
    edited: dict[int, dict] = {}
    has_edits = False

    # Existing steps — step number, technology and description all editable
    deleted_ids = st.session_state.deleted_step_ids
    for step in solution:
        idx = step.get("step", 0)
        if idx in deleted_ids:
            has_edits = True
            continue

        saved = st.session_state.edited_steps.get(idx, {})

        # Header labels row
        h_num, h_tech, h_del = st.columns([1, 4, 1])
        with h_num:
            st.caption(f"{lb['step']} #")
        with h_tech:
            st.caption(lb.get("tech_label", "Technology / Tool"))
        with h_del:
            st.caption(lb.get("remove", "Remove"))

        # Inputs row
        col_num, col_tech, col_del = st.columns([1, 4, 1])
        with col_num:
            new_num = st.number_input(
                "num", value=int(saved.get("step", idx)),
                min_value=1, step=1,
                key=f"step_num_{idx}", label_visibility="collapsed",
            )
        with col_tech:
            new_tech = st.text_input(
                "tech",
                value=saved.get("technology", step.get("technology", "")),
                key=f"step_tech_{idx}",
                label_visibility="collapsed",
                placeholder="e.g. Python, AWS, React",
            )
        with col_del:
            if st.button("✖", key=f"del_step_{idx}", help="Delete this step",
                         use_container_width=True):
                st.session_state.deleted_step_ids.add(idx)
                st.rerun()

        st.text_area(
            "desc",
            value=saved.get("action", step.get("action", "")),
            height=80,
            key=f"step_action_{idx}",
            label_visibility="collapsed",
            placeholder="Step description…",
        )
        new_action = st.session_state.get(f"step_action_{idx}",
                                          saved.get("action", step.get("action", "")))
        st.divider()

        edited[idx] = {
            "step": int(new_num),
            "action": new_action,
            "technology": new_tech,
            "skill_strength_score": step.get("skill_strength_score", 0.0),
            "effort": step.get("effort", "TBD"),
        }
        if (
            new_action.strip() != step.get("action", "").strip()
            or new_tech.strip() != step.get("technology", "").strip()
            or int(new_num) != idx
        ):
            has_edits = True

    st.session_state.edited_steps = edited

    # Added steps — all three fields editable + delete button
    surviving_added = []
    for j, step in enumerate(st.session_state.added_steps):
        # Header labels row
        h_num, h_tech, h_del = st.columns([1, 4, 1])
        with h_num:
            st.caption(f"{lb['step']} #")
        with h_tech:
            st.caption(lb.get("tech_label", "Technology / Tool"))
        with h_del:
            st.caption(lb.get("remove", "Remove"))

        # Inputs row
        col_num, col_tech, col_del = st.columns([1, 4, 1])
        with col_num:
            new_num = st.number_input(
                "num", value=int(step.get("step", j + 1)),
                min_value=1, step=1,
                key=f"added_num_{j}", label_visibility="collapsed",
            )
        with col_tech:
            new_tech = st.text_input(
                "tech", value=step.get("technology", "TBD"),
                key=f"added_tech_{j}",
                label_visibility="collapsed",
                placeholder="e.g. Python, AWS, React",
            )
        with col_del:
            delete = st.button("✖", key=f"del_added_{j}", help="Remove this step",
                               use_container_width=True)

        st.text_area(
            "desc", value=step.get("action", ""),
            height=80, key=f"added_action_{j}",
            label_visibility="collapsed", placeholder="Step description…",
        )
        new_action = st.session_state.get(f"added_action_{j}", step.get("action", ""))
        st.divider()

        if not delete:
            surviving_added.append({
                **step,
                "step": int(new_num),
                "action": new_action,
                "technology": new_tech,
            })
            has_edits = True

    st.session_state.added_steps = surviving_added

    # Add Step button
    next_idx = (solution[-1].get("step", len(solution)) if solution else 0) + 1 + len(surviving_added)
    if st.button(lb.get("add_step_btn", "➕ Add Step"), use_container_width=False):
        _add_step_dialog(next_idx, language)

    st.markdown("---")
    col_regen, col_cancel = st.columns(2)
    with col_regen:
        if st.button(
            lb.get("regenerate_btn", "🔄 Regenerate Resources"),
            type="primary",
            use_container_width=True,
            disabled=not has_edits or st.session_state.processing,
            help=lb.get("edit_activate_hint", "Edit or add at least one step to enable") if not has_edits else "",
        ):
            override = [
                {**step, **edited.get(step["step"], {})}
                for step in solution
                if step["step"] not in st.session_state.deleted_step_ids
            ] + st.session_state.added_steps
            _handle_regenerate(override, language)
    with col_cancel:
        if st.button(lb.get("cancel_btn", "✖ Cancel"), use_container_width=True):
            st.session_state.editing = False
            st.session_state.edited_steps = {}
            st.session_state.added_steps = []
            st.session_state.deleted_step_ids = set()
            st.rerun()


def _handle_regenerate(override_steps: list[dict], language: str) -> None:
    """Re-run scoring with edited steps, skipping web search and LLM solution."""
    last = st.session_state.last_result
    st.session_state.processing = True

    result = _run_live_pipeline(
        last.get("problem", ""),
        language,
        cached_search_results=last.get("search_results", {}),
        override_steps=override_steps,
    )

    if result.get("error"):
        logger.error("ui.regenerate_error message=%r", result["error"])
        st.session_state.processing = False
        st.error(result["error"])
        return

    model = result.get("model_name", get_model_name())
    assistant_content = _format_assistant_result(result, model, language)

    messages = st.session_state.messages
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["role"] == "assistant" and messages[i].get("raw_result"):
            messages[i] = {
                "role": "assistant",
                "content": assistant_content,
                "raw_result": result,
                "model": model,
            }
            break

    st.session_state.report_bytes = result.get("report_bytes")
    st.session_state.last_result = result
    st.session_state.edited_steps = {}
    st.session_state.added_steps = []
    st.session_state.deleted_step_ids = set()
    st.session_state.editing = False          # re-enable download
    st.session_state.processing = False
    logger.info(
        "ui.regenerate_complete solution_steps=%s resources=%s model=%s",
        len(result.get("solution", [])),
        len(result.get("resources", [])),
        model,
    )
    st.rerun()


def _render_header(lb: dict | None = None) -> None:
    """Render the app header with the EY asset when available."""
    if lb is None:
        lb = get_labels("English")
    title = lb.get("app_title", "Functional Consultant Resource Matcher")
    if HEADER_IMAGE.exists():
        image_uri = _image_data_uri(HEADER_IMAGE)
        st.markdown(
            f"""
            <div class="app-header">
                <img src="{image_uri}" alt="EY asset bot" />
                <h1>{title}</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    st.title(title)


def _image_data_uri(path: Path) -> str:
    """Return a base64 data URI for a local image."""
    import base64
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _render_chat_bubble(role: str, content: str) -> None:
    """Render a left/right chat bubble."""
    safe_content = _plain_text_to_html(content)
    bubble_role = "user" if role == "user" else "assistant"
    st.markdown(
        f"""
        <div class="chat-row {bubble_role}">
            <div class="chat-bubble {bubble_role}">{safe_content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _plain_text_to_html(content: str) -> str:
    """Escape text and preserve line breaks for HTML bubbles."""
    escaped = html.escape(content or "")
    escaped = escaped.replace("**", "")
    escaped = escaped.replace("`", "")
    return escaped.replace("\n", "<br>")


def _format_assistant_result(
    result: dict, model: str, language: str = "English",
) -> str:
    """Format the assistant response for the chat bubble."""
    lb = get_labels(language)
    cache_badge = " ⚡" if result.get("_from_cache") else ""
    parts = [lb["report_generated"] + cache_badge, f"{lb['model']}: {model}"]

    solution = result.get("solution", [])
    if solution:
        parts.append(f"\n{lb['breakdown_title']}")
        for step in solution:
            parts.append(format_solution_step(step, language))

    task_recs = result.get("task_recommendations", [])
    if task_recs:
        parts.append(f"\n{lb['task_recs_title']}")
        for task in task_recs:
            parts.append(format_task_recommendation(task, language))
    else:
        resources = result.get("resources", [])
        if resources:
            parts.append(f"\n{lb['resources_title']}")
            for resource in resources:
                parts.append(format_resource_card(resource, language))

    if result.get("risk_flags"):
        parts.append(f"\n{lb['risk_title']}")
        for flag in result["risk_flags"]:
            parts.append(f"- {flag.get('reason', 'Unknown risk')}")

    parts.append(f"\n{lb['download_hint']}")
    return "\n\n".join(parts)


def _run_mock_pipeline(prompt: str, language: str = "English") -> dict:
    """Run mock pipeline with animated steps for testing."""
    client = MockAPIClient()
    steps = get_workflow_steps(language)
    placeholder = st.empty()
    for step in steps:
        logger.info("ui.mock_progress label=%r", step["label"])
        placeholder.markdown(f"{step['icon']} {step['label']}")
        time.sleep(0.5)
    placeholder.empty()
    return client.run_pipeline(prompt)


def _run_live_pipeline(
    prompt: str,
    language: str = "English",
    cached_search_results: dict | None = None,
    override_steps: list | None = None,
    translated_problem: str = "",
) -> dict:
    """Stream the backend pipeline, updating UI per SSE event."""
    placeholder = st.empty()
    stop_placeholder = st.empty()

    # Stop button — visible during the pipeline run
    _, col_stop = stop_placeholder.columns([4, 1])
    with col_stop:
        if st.button(get_labels(language).get("stop_btn", "🛑 Stop"), key="stop_pipeline", type="primary",
                     use_container_width=True):
            stop_placeholder.empty()
            placeholder.empty()
            st.session_state.processing = False
            st.session_state.editing = False
            # Remove the orphaned user message that has no response yet
            msgs = st.session_state.messages
            if msgs and msgs[-1]["role"] == "user":
                st.session_state.messages = msgs[:-1]
            st.rerun()

    client = get_client()

    if not is_server_running(client.base_url):
        logger.info("ui.api_not_running base_url=%s", client.base_url)
        start_server()
        for _ in range(10):
            if is_server_running(client.base_url):
                logger.info("ui.api_started base_url=%s", client.base_url)
                break
            time.sleep(0.5)
        else:
            logger.error("ui.api_start_failed base_url=%s", client.base_url)
            st.error("API server did not start. Please try again.")
            return {
                "problem": prompt, "model_name": get_model_name(),
                "solution": [], "resources": [], "risk_flags": [],
                "report_bytes": b"",
            }

    workflow_steps = get_workflow_steps(language)

    def on_step(node_name: str, step_index: int) -> None:
        step = workflow_steps[step_index]
        logger.info(
            "ui.render_step node=%s step_index=%s label=%r",
            node_name, step_index, step["label"],
        )
        placeholder.markdown(f"{step['icon']} {step['label']}")

    def on_progress(data: dict) -> None:
        status = data.get("status")
        if status:
            logger.info("ui.render_progress status=%r", status)
            translated = translate_progress(status, language)
            placeholder.markdown(f"🔄 {translated}")

    try:
        result = client.run_pipeline(
            prompt,
            on_step=on_step,
            on_progress=on_progress,
            language=language,
            cached_search_results=cached_search_results,
            override_steps=override_steps,
            translated_problem=translated_problem,
        )
        placeholder.empty()
        return result
    except PipelineStreamError as exc:
        logger.exception("ui.pipeline_stream_error")
        placeholder.empty()
        return {
            "error": (
                "The backend pipeline stopped before completing. "
                f"{exc}"
            ),
            "problem": prompt, "model_name": get_model_name(),
            "solution": [], "resources": [], "risk_flags": [],
            "report_bytes": b"",
        }


if __name__ == "__main__":
    main()

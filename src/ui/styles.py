"""CSS theme for Streamlit app. Colors: grey, baby pink, dark blue, black."""

THEME_CSS = """
<style>
/* Base */
.stApp {
    background-color: #1a1a2e;
    color: #e0e0e0;
}

/* Chat input */
.stChatInput textarea {
    background-color: #16213e !important;
    color: #e0e0e0 !important;
    border: 1px solid #3a3a5c !important;
}
.stChatInput textarea:focus {
    border-color: #f4a8c4 !important;
    box-shadow: 0 0 0 1px #f4a8c4 !important;
}

/* Chat messages */
.chat-row {
    display: flex;
    width: 100%;
    margin: 0.75rem 0;
}
.chat-row.user {
    justify-content: flex-end;
}
.chat-row.assistant {
    justify-content: flex-start;
}
.chat-bubble {
    max-width: min(760px, 78%);
    padding: 0.85rem 1rem;
    border-radius: 8px;
    line-height: 1.45;
    white-space: pre-wrap;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
}
.chat-bubble.user {
    background-color: #f4a8c4;
    color: #151521;
    border: 1px solid #f7bfd3;
    border-top-right-radius: 2px;
}
.chat-bubble.assistant {
    background-color: #16213e;
    color: #e8edf7;
    border: 1px solid #30466f;
    border-top-left-radius: 2px;
}
.chat-bubble.assistant strong,
.chat-bubble.assistant b {
    color: #f4a8c4;
}
.chat-bubble.user strong,
.chat-bubble.user b {
    color: #0f3460;
}

/* Header */
.app-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.25rem;
}
.app-header img {
    width: 64px;
    height: 64px;
    object-fit: contain;
    border-radius: 8px;
    background: #ffffff;
    padding: 0.25rem;
}
.app-header h1 {
    margin: 0;
    color: #f4a8c4;
}

/* Status spinner */
.stSpinner {
    color: #f4a8c4 !important;
}

/* Buttons — on-hover animation */
.stButton button {
    background-color: #0f3460 !important;
    color: #f4a8c4 !important;
    border: 1px solid #3a3a5c !important;
    transition: all 0.3s ease !important;
}
.stButton button:hover {
    background-color: #f4a8c4 !important;
    color: #1a1a2e !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(244, 168, 196, 0.3) !important;
}

/* Download button override */
.stDownloadButton button {
    background-color: #0f3460 !important;
    color: #f4a8c4 !important;
    border: 1px solid #3a3a5c !important;
    transition: all 0.3s ease !important;
}
.stDownloadButton button:hover {
    background-color: #f4a8c4 !important;
    color: #1a1a2e !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(244, 168, 196, 0.3) !important;
}

/* Markdown headings in chat */
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    color: #f4a8c4 !important;
}

/* Success/complete indicators */
.stSuccess {
    background-color: rgba(15, 52, 96, 0.8) !important;
    color: #f4a8c4 !important;
}

/* Sidebar buttons — consistent blue theme */
section[data-testid="stSidebar"] button {
    background-color: #0f3460 !important;
    color: #f4a8c4 !important;
    border: 1px solid #3a3a5c !important;
}

/* Sidebar history text buttons — left align text only */
section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"] p {
    text-align: left !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"] {
    justify-content: flex-start !important;
    padding-left: 0.6rem !important;
}

/* 👁 and 🗑️ icon buttons — full reset to ghost style */
section[data-testid="stSidebar"] [data-testid="stColumn"]:not(:first-child) button,
section[data-testid="stSidebar"] [data-testid="column"]:not(:first-child) button {
    all: unset !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    color: #f4a8c4 !important;
    padding: 4px 0 !important;
    border-radius: 4px !important;
    font-size: 1.1rem !important;
    transition: background-color 0.2s !important;
}
section[data-testid="stSidebar"] [data-testid="stColumn"]:not(:first-child) button:hover,
section[data-testid="stSidebar"] [data-testid="column"]:not(:first-child) button:hover {
    background-color: rgba(244, 168, 196, 0.15) !important;
}
</style>
"""


def apply_theme():
    """Apply the custom CSS theme to the Streamlit app."""
    import streamlit as st
    st.markdown(THEME_CSS, unsafe_allow_html=True)

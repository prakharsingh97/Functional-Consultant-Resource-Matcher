# Functional Consultant Resource Matcher
### AI-Powered Staffing Intelligence for Consulting Teams

---

## What This Is

Given any project or product problem statement, this tool answers two questions in under five minutes:

1. **How should this project be broken into delivery workstreams?**
2. **Who on the bench has the right skills, and how confident should we be?**

**Primary users: Functional Consultants** — who need to know quickly which of their team members can actually deliver a specific engagement, without spending half a day in spreadsheets.

**Secondary users: Engagement Managers and Partners** — who are accountable for the staffing decision and need a defensible, data-backed shortlist to review and approve, not a gut-feel list assembled over Slack.

Not a quarterly planning tool. Not an HR system. Built for the operational moment when a new engagement lands and the clock is already running.

---

## The Problem It Solves

Staffing a consulting engagement today means opening three spreadsheets, sending four Slack messages, and spending a day building a matrix by hand based on CVs and personal memory. The people best positioned to answer "who fits this project?" are the ones too busy to do the analysis.

This prototype surfaces a ranked, AI-reasoned staffing recommendation — with fit scores, skill coverage, and a downloadable resource report — from a single plain-English problem description.

---

## Live Demo Flow

```
User types problem statement
        ↓
Tavily searches web for current implementation context
        ↓
LLM (OpenRouter) extracts required skills from enriched context
        ↓
Sentence-transformers matches skills semantically against consultant database
        ↓
LLM generates skill-biased workstream breakdown
        ↓
Scoring engine ranks consultants by fit (80% skill match, 20% availability)
        ↓
FastAPI streams progress via SSE → Streamlit renders in real time
        ↓
Downloadable .docx resource report with task matrix and resource recommendations
```

---

## Key Features

| Feature | Description |
|---|---|
| **Chat interface** | Single-screen Streamlit UI — type a problem, get a staffing plan |
| **Live pipeline streaming** | Progress updates appear in real time via Server-Sent Events |
| **Semantic skill matching** | `nomic-embed-text-v1.5` embeddings match "ETL pipeline" to "Data Engineering" — not just keyword search |
| **Task matrix** | Each workstream gets a primary and support resource with fit scores |
| **Multilingual UI** | 9 languages — UI labels, progress messages, and report headings all translate instantly |
| **Editable steps** | Edit, add, or delete workstream steps and regenerate resource matching without re-running the full pipeline |
| **Prompt cache** | Repeated queries return instantly from local JSON cache |
| **History sidebar** | All past queries searchable, previewable, and reloadable |
| **resource report (.docx)** | Downloadable report with original query, executive summary, project breakdown, task recommendations, and risk flags |
| **Stop button** | Cancel a running pipeline at any point |

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| UI | Streamlit | Chat interface, progress rendering, download |
| Backend API | FastAPI | SSE streaming, CRUD endpoints |
| AI Orchestration | LangGraph | Directed 6-node pipeline |
| LLM | OpenRouter (free tier) | Skill extraction + workstream generation |
| Web Search | Tavily | Enriches problem statement with current industry context |
| Embeddings | sentence-transformers (`nomic-embed-text-v1.5`) | Semantic skill matching |
| Data Store | Excel (.xlsx) | 4-sheet normalized schema: users, skills, levels, user_skills |
| Document Gen | python-docx | Generates the PM staffing report |

---

## Architecture

```
Streamlit (UI)
    │  submit problem
    ▼
FastAPI /v1/pipeline/stream   ←── SSE events back to UI
    │
    ▼
LangGraph Pipeline
    ├── load_resources     (Excel → users, skills, levels, user_skills)
    ├── web_search         (Tavily → LLM skill extraction, always English)
    ├── compute_strength   (semantic similarity → skill strength scores)
    ├── generate_solution  (LLM → workstream breakdown, target language)
    ├── score_resources    (fit scoring: 80% skill, 20% availability)
    └── generate_report    (python-docx → .docx bytes)
```

**Important design note on language:** Skill extraction and semantic matching always run in English, regardless of the UI language setting. This preserves embedding accuracy — the consultant database is in English, and cross-language embeddings degrade cosine similarity. The workstream descriptions and UI are translated; the matching pipeline is not.

---

## How Fit Is Calculated

**Skill Strength Score** (per skill, shown in the breakdown):
```
strength = SUM(score_weight × cosine_similarity)
           across all consultants who have that skill
```

**Resource Fit Score** (per consultant, per task):
```
skill_fit        = raw_semantic_score / num_task_skills   (capped at 1.0)
availability_fit = availability_hours / 20                (capped at 1.0)
fit_score        = (skill_fit × 0.80) + (availability_fit × 0.20)
```

Skill level weights: Beginner=0.25 · Intermediate=0.50 · Advanced=0.75 · Expert=1.00
Similarity threshold: >0.5 to count as a match; top-3 fallback if nothing clears threshold.

---

## Project Structure

```
.
├── main.py                   # Launches FastAPI + Streamlit together
├── src/
│   ├── api/                  # FastAPI app, routes, SSE pipeline endpoint
│   ├── cache/                # Local JSON prompt cache
│   ├── client/               # HTTP client consuming SSE stream
│   ├── db/                   # Excel reader (4-sheet schema)
│   ├── models/               # Pydantic schemas
│   ├── reports/              # python-docx report generator (multilingual)
│   ├── ui/                   # Streamlit app, components, styles, translations
│   └── workflow/
│       ├── graph.py          # LangGraph pipeline definition
│       ├── llm/              # OpenRouter client, prompts, embeddings
│       ├── nodes/            # 6 pipeline nodes
│       └── state.py          # Typed pipeline state
├── data/
│   └── consultant_database.xlsx   # 4-sheet consultant database
├── tests/                    # Smoke tests (mock-first)
├── plans/                    # Implementation plan docs
├── .env.example              # Environment variable template
├── pyproject.toml            # Dependencies (managed with uv)
├── TASK_REQUIREMENTS.md      # Product thinking + AI system design doc
└── WHY_THIS_MVP.md           # Product rationale
```

---

## Setup

### Prerequisites

- Python 3.12+
- `uv` package manager

### Install

```bash
# 1. Clone or download the repo
cd product-manager-mvp

# 2. Install uv
python3 -m pip install uv

# 3. Install dependencies
uv sync --all-groups

# 4. Activate the virtual environment
source .venv/bin/activate

# 5. Configure environment
cp .env.example .env
# Edit .env and add your API keys (see below)

# 6. Run
python3 main.py
```

Then open **http://localhost:8501** in your browser.

---

## API Keys

Two keys are required for live mode. The app runs fully in mock mode without any keys (set `env=TESTING` in `.env`).

| Key | Where to get it | Free tier? |
|---|---|---|
| `OPENROUTER_API_KEY` | https://openrouter.ai/settings/keys | Yes |
| `TAVILY_API_KEY` | https://tavily.com/dashboard | Yes (dev tier) |

Copy `.env.example` to `.env` and fill in both keys. Set `env=DEV` (or any non-TESTING value) to activate live calls.

---

## Running in Test Mode (No API Keys)

Set `env=TESTING` in your `.env`. All LLM and Tavily calls are mocked with fixture data. The full UI, streaming, and download flow works — the output just uses pre-built sample data rather than live AI responses.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/v1/pipeline/health` | Health check |
| POST | `/v1/pipeline/stream` | Run pipeline, stream SSE events |
| GET | `/v1/users` | List all consultants |
| GET | `/v1/users/:id` | Single consultant |
| GET | `/v1/users/:id/skills` | Consultant with skills |
| GET | `/v1/skills/strength` | All skills ranked by strength score |
| POST | `/v1/users` | Add consultant |
| PUT | `/v1/users/:id` | Update consultant |
| DELETE | `/v1/users/:id` | Remove consultant |

FastAPI docs available at **http://localhost:8000/docs** when running.

---

## Report Output (.docx)

The downloaded report includes:

| Section | Contents |
|---|---|
| Original Query | Problem statement verbatim (translated if language selected) |
| Executive Summary | Task count, resource count, risk summary |
| How To Read This Report | Definitions of Strength and Fit scores |
| Project Breakdown | Workstream table with skills, strength, effort |
| Task Resource Recommendations | Primary/support resources per task with fit, availability, matched skills |
| Risk Flags | Tasks with no available resource coverage |

All section headings and labels translate to the selected language (9 languages supported).

---

## Product Scope

### In Scope

- Plain-English problem statement → workstream breakdown → staffing shortlist
- Semantic skill matching (not keyword matching)
- Task-level primary/support resource recommendations
- Availability-weighted fit scoring
- Multilingual output (9 languages) with English-only matching pipeline
- Editable workstream steps with targeted re-scoring
- Downloadable resource report (.docx)
- Local prompt cache for instant repeat queries
- TESTING mode (full UI, no API keys required)
- **Human-in-the-loop feedback** — users can edit, add, or delete workstream steps and regenerate resource matching without re-running the full pipeline

### Intentionally Out of Scope

- **No staffing decisions** — the tool surfaces a shortlist; humans approve
- **No ERP/HR integration** — reads from Excel, writes nowhere
- **No utilization forecasting** — tactical staffing only, not strategic planning
- **No skill validation** — takes profile data at face value
- **No authentication** — single-user local tool

### Planned Next

- ReAct agent loop for per-feature web research and skill extraction
- Editable checkpoint flow after each pipeline step
- Google Sheets integration for live availability data
- Feedback collection to calibrate fit scores over time

---

## What Breaks at Scale (Known Limits)

| Limit | Current state | Fix path |
|---|---|---|
| Data store | Excel (35 consultants) | Replace with PostgreSQL — schema is already normalized |
| Concurrency | Single-threaded SSE | Async LangGraph + horizontal FastAPI scaling |
| Embedding speed | Re-embeds every run | Cache DB skill embeddings (they are static) |
| LLM cost | 2 calls/run, free tier | Prompt caching + smaller model for extraction at volume |
| Stale availability | Snapshot in Excel | Live pull from People/HR system |

---

## Multilingual Support

The UI, all labels, progress messages, and the .docx report support:

English · French · German · Spanish · Portuguese · Hindi · Arabic · Japanese · Chinese (Simplified)

Change the language in the **Settings** panel in the sidebar. All elements update immediately — no re-run required.

**Architecture note:** Skill extraction and semantic matching always run in English to preserve embedding accuracy. Workstream descriptions and the report body are generated in the selected language.

---

*MVP 1.1 · Built with Streamlit, FastAPI, LangGraph, OpenRouter, Tavily, sentence-transformers*

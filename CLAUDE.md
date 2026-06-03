# Functional Consultant Resource Matcher — Project Guide

## Project Overview

AI-assisted Streamlit app that matches consultant resources to product/project problem statements. User types a problem in a chat interface. The current MVP performs query-level web/search enrichment, generates a task/workstream breakdown, maps resources to each task, calls out coverage risks, and presents a downloadable PM-ready report for human review.

**Current Core Loop:** Chat Input > Query-Level Web Research > Skill-Biased Work Breakdown > Task-Based Resource Matrix > Execution Risks > Human Review > Download Report

**Next Planned Loop:** Chat Input > Feature/Deliverable Breakdown > Per-Feature Web Research > Per-Feature Skill Extraction > Resource x Feature Matrix > Execution Risks > Human Review > Download Report

**Goal:** From problem statement to a downloadable resource report in under 5 minutes.

---

## Development Rules (MUST follow)

- project uses uv. install uv using pip first : `python3 -m pip install uv`
- once uv is installed, ensure you either create or sync with the pyproject toml, ie `uv init` (if you dont have a pyproject.toml file)or `uv sync --all-groups` (if there are packages already and we are syncing for the requirements)
- activate the virtual environment : `source .venv/bin/activate`
- use `python3` always, not `python`
- use `uv` and not `pip` for all additions to the project
- commit pyproject.toml and uv.lock both if you update the package list

### Package Management

- **UV only.** No pip. Use `uv add <package>` for all additions.
- All code is Python.

### Code Style

- Simple Python functions. Each function `<=100 lines` with clear docstrings.
- No over-abstraction, no inheritance, no interfaces — unless there is a genuine need for classes/OOP.
- **YAGNI over DRY.** If you must choose, prefer simple readable code over deduplication.
- Clear documentation on every function. Code is broken down by large features scoped to ui, backend, logic. they have relevant plans in ./plans/ subdir

### Git Hygiene

- Commit prefixes ONLY: `addition --`, `deletion --`, `update --`, `refactor --`
- Single-line commit messages only.
- No attribution info (no `Co-authored-by` lines).
- Commit in bunches the files relevant to the commit prefixes
- Commit often, keep commit messages succinct
- branches to know :
  - "dev" : dev work (langgraph work)
  - "fastapi-backend" : backend work with api contracts that interface with the frontend (endpoints, fastapi work)
  - "streamlit-ui" : simple streamlit app which uses the endpoints as per the decided api models and data contracts

### Testing & Mocking

- **Mock-first, outside-in implementation.** Data contracts, API models, integration points, function definitions, and args are all decided first → mocked → written for smoke tests — for ALL functionality.
- LLM calls are **always mocked** in tests unless `.env` var `env` is NOT `"TESTING"`. Default is `"TESTING"`.

### LLM Configuration

- **All LLM calls go through OpenRouter** using the `openai-python` library.
- Default model: `openrouter/free` (auto-selects from available free models).
- Client setup:
  ```python
  from openai import OpenAI
  client = OpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key=os.environ["OPENROUTER_API_KEY"],
  )
  response = client.chat.completions.create(
      model="openrouter/free",
      messages=[...],
  )
  ```
- Available free models include: `google/gemma-3-27b:free`, `qwen/qwen3-235b-a22b-thinking:free`, etc. See `https://openrouter.ai/collections/free-models`

### Scope Boundaries for MVP

- **NO rerun loop.** No auto-rerun on override.
- **NO editable checkpoint flow.** Human review happens after report generation.
- Output is a downloadable `.docx` report only.

## Plan Index

Use the tracked plan files for deeper implementation context and parity notes:

- `plans/01-backend-api.md` - Excel data layer, Pydantic schemas, and FastAPI CRUD endpoints.
- `plans/02-frontend-ui.md` - Streamlit chat UI, progress indicators, report display, and download-only final action.
- `plans/03-logic-workflow.md` - LangGraph nodes, search enrichment, skill strength, scoring, and task recommendations.
- `plans/04-integration-polish.md` - FastAPI/SSE integration, console logging, report polish, and final hardening.

---

## Tech Stack

| Layer            | Technology            | Purpose                                              |
| ---------------- | --------------------- | ---------------------------------------------------- |
| UI               | Streamlit             | Single-screen chat interface with workflow status    |
| AI Orchestration | LangGraph (Python)    | Directed pipeline for workflow steps                 |
| LLM              | OpenRouter (free)     | All LLM calls via openai-python + OpenRouter API     |
| Search Tool      | Tavily                | Web search tool given to LLM                         |
| Embeddings       | sentence-transformers | Semantic skill matching via nomic-embed-text-v1.5    |
| Data Store       | Excel (.xlsx)         | Sheets = tables (users, skills, levels, user_skills) |
| Backend API      | FastAPI               | Endpoints under `v1/` prefix                       |
| Document Gen     | python-docx           | Generates downloadable .docx report                  |

---

## Architecture

### Core Application: Current Pipeline + ReAct Roadmap

The current implementation is a LangGraph pipeline with query-level search enrichment and task-based staffing recommendations. The next planned evolution is a ReAct-style planning agent that reasons over each feature/deliverable, calls web search per feature, extracts feature-specific skills, then maps people to those feature needs.

```
LLM (OpenRouter/free)
  └── Tool: internet_search (Tavily)
```

Current implemented loop:

1. Read the original user query.
2. Run query-level Tavily/search enrichment and skill extraction.
3. Compute team skill strength from the Excel database.
4. Generate a skill-biased task/workstream breakdown.
5. Build task-level primary/support resource recommendations.
6. Generate a downloadable PM-ready `.docx` report.

Target ReAct reasoning loop:

1. Read the original user query.
2. Break it into product features/deliverables as a checklist.
3. For each feature/deliverable, call `internet_search` to gather current implementation context, best practices, risks, and likely skills.
4. Extract required skills per feature, not just globally.
5. Build a Resource x Feature matrix with primary/support recommendations.
6. Call out execution risks, dependencies, assumptions, and open PM questions.
7. Generate a report that a Product Manager can use for scoping, staffing, and planning.

### LangGraph Workflow (Streamlit Chat)

The Streamlit UI is a simple chat interface. LangGraph emits standard workflow step messages as the pipeline progresses:

1. **Gathering project information...**
2. **Searching web to clarify feature deliverables...**
3. **Finding resources with relevant skills from our database...**
4. **Finding best match resources...**
5. **Finalizing resource report** → downloadable `.docx`

Each step appears as a status message in the chat. The final output is a downloadable report.

### Current LLM Workflow and Prompts

Prompt templates live in `src/workflow/llm/prompts.py`. The current workflow is not a fully autonomous ReAct loop yet; it is a deterministic LangGraph pipeline with two bounded LLM calls and code-owned scoring/reporting around them.

**Prompt 1: Skill Extraction**

- System prompt: `SKILL_EXTRACTION_PROMPT`
- Builder: `build_skill_extraction_prompt(problem, search_results)`
- Node: `src/workflow/nodes/web_search.py`
- Flow:
  1. Take the original user problem statement.
  2. Run Tavily search for query-level implementation context.
  3. Format the search snippets into one text block.
  4. Ask the LLM to return JSON with exactly:
     - `required_skills`: specific skills/technologies needed for the project.
     - `search_context`: short summary of what search revealed.
     - `difficulty`: `0.0` to `1.0` difficulty estimate.
  5. If Tavily or the LLM fails, use deterministic keyword/query extraction fallback so the pipeline still completes.

**Prompt 2: Solution / Workstream Generation**

- System prompt: `SOLUTION_SYSTEM_PROMPT`
- Builder: `build_solution_prompt(problem, tech_ranking)`
- Node: `src/workflow/nodes/generate_solution.py`
- Flow:
  1. Read the original problem statement.
  2. Read the computed team Skill Strength Scores.
  3. Ask the LLM to break the project into delivery tasks/workstreams, not only engineering steps.
  4. Instruct the LLM to include product discovery/scoping, architecture, engineering, agent/tool integration, UI/visualization, QA/testing, release planning, observability, and guardrails where relevant.
  5. Ask for JSON with `steps`, where each step has:
     - `step`
     - `action`
     - `technology`
     - `skill_strength_score`
     - `effort`
  6. If the LLM response is empty, malformed, or unavailable, use a deterministic fallback plan.

**Code-Owned Work After LLM Calls**

The LLM does interpretation and planning only. The code owns the non-trivial deterministic parts:

1. `load_resources` loads users, skills, levels, and user-skill mappings from Excel.
2. `web_search` enriches the problem and extracts required skills.
3. `compute_strength` maps required skills to DB skills using semantic similarity, with lexical fallback if embeddings are unavailable.
4. `generate_solution` produces the skill-biased task/workstream breakdown.
5. `score_resources` computes resource fit, availability-aware rankings, and per-task primary/support assignments.
6. `generate_report` creates the PM-ready `.docx`.

This separation is intentional: prompts produce structured context, while scoring, matching, report assembly, and failure handling stay in testable Python code.

**Streaming / Observability**

- LangGraph runs with `stream_mode=["updates", "custom"]`.
- Node updates become `step` SSE events from FastAPI.
- `get_stream_writer()` messages become `progress` SSE events.
- The Streamlit UI and console logger receive updates at the same time, so UI progress and terminal logs should tell the same story.

### Data Model (Excel — 4 sheets)

- **users** — user_id (PK), full_name, email (UNIQUE), role, availability (0-40 hrs/wk), timezone, created_at
- **skills** — skill_id (PK), skill_name (UNIQUE), category, description
- **levels** — level_id (PK: 1=Beginner, 2=Intermediate, 3=Advanced, 4=Expert), level_name, score_weight (0.25/0.50/0.75/1.00)
- **user_skills** (JOIN) — id (PK), user_id (FK→users), skill_id (FK→skills), level_id (FK→levels), years_exp, last_used

### Key Derived Value: Skill Strength Score

Computed at runtime (not stored). Skills from the LLM/web search (required skills) are matched to skills in the DB using **semantic similarity** (not string matching).

**Embedding model:** `nomic-ai/nomic-embed-text-v1.5` via `sentence-transformers` (CPU-optimized, ~274MB).

**Matching flow:**

1. Embed required skills (from LLM + web search) and DB skill names.
2. Compute cosine similarity between each required skill and each DB skill.
3. For each DB skill, take `max(semantic_sim)` across all required skills.
4. Score = `SUM(score_weight * semantic_sim)` across all users with that skill.
5. Normalize and rank descending.

**Threshold:** `semantic_sim > 0.5` to count as a match. If no candidates satisfy the 0.5 threshold, fall back to `top_k=3` (highest semantic similarity regardless of threshold).

Example: LLM says "Machine Learning" → DB has "Python", "TensorFlow", "scikit-learn" → semantic match picks these with scores > 0.5.

### Resource Fit Score

Per-user fit score uses the same semantic matching:

1. For each user, find their skills that semantically match required skills (threshold > 0.5, fallback top_k=3).
2. Raw fit = `SUM(score_weight * semantic_sim)` for matched skills.
3. Normalized fit = `raw_fit / (num_required_skills * max_weight)` → clamped to 0–1.
4. This normalized fit feeds the priority queue.

### Priority Queue (P1–P4)

| Priority      | Condition           | Fit Score         | Availability |
| ------------- | ------------------- | ----------------- | ------------ |
| P1 - Assign   | High fit, available | >= 0.75           | >= 20 hrs/wk |
| P2 - Consider | Good fit, semi-busy | 0.5 - 0.74        | 10-19 hrs/wk |
| P3 - Risky    | Low fit or busy     | < 0.5 OR < 10 hrs | < 10 hrs/wk  |
| P4 - Skip     | No match            | < 0.25            | Any          |

---

## UI — Streamlit Single Screen

**Colors:** grey, baby pink, dark blue, black (any combination). On-hover animations on buttons, but nothing else.

**Layout:** Single chat interface.

- User types problem statement in chat input.
- LangGraph pipeline runs, emitting step-by-step status messages:
  - 🔄 Gathering project information...
  - 🔄 Searching web to clarify task lists...
  - 🔄 Finding resources with relevant skills from our database...
  - 🔄 Finding best match resources...
  - ✅ Finalizing resource report
- Final output: downloadable `.docx` resource report displayed in chat.
- Button: Download Report only.

---

## API Endpoints (FastAPI — `v1/` prefix)

| Op              | Endpoint                | Description                            |
| --------------- | ----------------------- | -------------------------------------- |
| CREATE          | POST v1/users           | New row; returns user_id               |
| READ            | GET v1/users/:id        | Single user JSON                       |
| UPDATE          | PUT v1/users/:id        | Updated row in sheet                   |
| DELETE          | DELETE v1/users/:id     | Row removed from sheet                 |
| READ ALL        | GET v1/users            | Array of all user objects              |
| JOIN READ       | GET v1/users/:id/skills | User + skills + levels enriched        |
| STRENGTH        | GET v1/skills/strength  | All skills ranked by Strength Score    |
| PIPELINE HEALTH | GET v1/pipeline/health  | Streaming backend health check         |
| PIPELINE STREAM | POST v1/pipeline/stream | SSE pipeline progress and final report |

---

## Report Output (.docx)

The downloadable report should be useful to a Product Manager, not just a technical staffing list. It must preserve traceability from the original query to the final staffing recommendation.

| Section                       | Contents                                                                                |
| ----------------------------- | --------------------------------------------------------------------------------------- |
| Original Query                | User input verbatim for traceability                                                    |
| Executive Summary             | Task-based staffing summary and coverage risks                                          |
| Project Breakdown             | Query broken into tasks/workstreams                                                     |
| Task Resource Recommendations | Primary/support resource recommendations per task with fit, availability, and rationale |
| Definitions                   | Define Strength and Fit in plain language                                               |
| Risk Flags                    | Unstaffed task coverage gaps                                                            |

Planned PM report improvements:

- Feature/Deliverable Checklist
- Per-feature web research notes
- Assumptions & open questions
- Dependencies
- Execution risks & mitigations
- Milestones / release plan
- Success metrics
- Acceptance criteria

Do not frame the report as picking one best person for the whole project. A project can require engineering, product management, scoping, QA/testing, release planning, observability, visualization, and guardrail work. Recommendations should be per feature/deliverable and may include combinations of people.

Avoid P3/P4 classifications in the primary report for people who are not enlisted for the project. Keep skipped candidates out of the recommendation table unless the user asks for a full bench analysis.

---

## Scope

### In Scope (MVP)

Excel CRUD, Streamlit chat UI, Tavily web search tool, semantic skill matching with lexical fallback, Skill Strength Score calculation, skill-biased task/workstream breakdown, task-based resource recommendations, downloadable .docx report, LangGraph orchestration, FastAPI SSE streaming, OpenRouter LLM integration, console progress logging

### Future Work

- After each workflow step, show the user a markdown-formatted **checklist** with tick boxes and an option to edit.
- Use a diff mechanism to compare what the user has entered vs. AI output, update the checklist, and proceed.
- Build current version with this future in mind so the code is not brittle — keep step outputs structured (not raw strings) to allow future editing/diffing.

### Out of Scope (for now)

Risk-Aware Auto-Rerun loop, React, Google Sheets API, authentication/SSO, ZIP/multi-file packaging, native mobile app, billing/invoicing, email/Slack notifications, ML model fine-tuning

---

## Environment Variables (or follow .env.example)

```
OPENROUTER_API_KEY=    # OpenRouter API key
TAVILY_API_KEY=        # Tavily search API key. sign up for one for free using email
env=DEV                # "TESTING" = mock all LLM calls; anything else = live calls
API_BASE_URL=http://localhost:8000
DEFAULT_LLM=openrouter/free
LOG_LEVEL=INFO
```

---

## Implementation Approach: Mock-First Outside-In

For every feature, follow this order:

1. **Define data contracts** — Pydantic models for inputs/outputs of every function.
2. **Define function signatures** — name, args, return type, docstring.
3. **Write mocks** — return fixture data matching the contracts.
4. **Write smoke tests** — call the mocked functions, assert contract shape.
5. **Implement** — replace mocks with real logic, tests still pass.

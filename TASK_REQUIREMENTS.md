# Task Requirements & Product Thinking Document
## EY Functional Consultant Resource Matcher — MVP 1.1

---

## Part 1 — Product Thinking Note

### The Problem Moment

The pain does not happen in a meeting room or on a slide deck. It happens at 7:43 PM on a Tuesday when a partner emails a team saying a new financial services engagement just closed and the SOW needs a staffing plan by Thursday morning.

The engagement manager opens three spreadsheets — one for bench availability, one for skill certifications, one tracking who is wrapping up which project and when. None of them talk to each other. She Slack-messages four senior managers asking who might be good for ETL pipeline work. Two do not respond until morning. One recommends someone who is already 90% allocated. She spends Wednesday building a matrix by hand, guessing at skill fit based on CVs and personal memory.

By the time the staffing plan lands in front of the partner, two things are almost certainly true: it is not optimal, and it took twelve hours of senior attention to produce.

This is the exact moment the prototype addresses. Not the strategic workforce planning that happens quarterly, not the HR performance cycle that happens annually — the operational moment when a specific project needs specific people and the clock is running.

**Why this moment is underserved:** Every large consulting firm has systems for billing, utilization, and HR. None of them answer "given this project, who should I put on it, in what roles, and how confident should I be?" in under ten minutes. The people who could answer that question are the ones too busy to do the analysis.

---

### Why Generative AI?

Three capabilities make Generative AI specifically the right fit here, not just "better software."

**1. The problem statement is always novel.**

No two client engagements are identical. A traditional rules-based system would require someone to pre-tag every project type, skill requirement, and workstream template. That is the same manual work we are trying to eliminate. A language model can read "a mid-sized financial services firm needs to reconcile 340 pages of contractual obligations across four jurisdictions" and understand — without any pre-configuration — that this involves data integration, compliance expertise, legal language processing, and change management. That semantic understanding is the core unlock.

**2. Skill-to-task matching is ambiguous by design.**

A consultant who lists "Python" on their profile may or may not be relevant for an ETL pipeline engagement. The match depends on context: what kind of Python, at what seniority level, in combination with what other skills? Sentence-transformer embeddings capture this contextual similarity in a way that exact keyword matching cannot. "Data engineering" and "ETL pipeline" score high similarity. "Python" and "ERP integration" score low. This is the kind of nuanced, semantic reasoning that makes the resource fit score meaningful rather than arbitrary.

**3. Web-enriched context improves output quality.**

When Tavily searches for "reconciliation automation financial services 2024," it retrieves current implementation patterns, common failure modes, and relevant technology choices. The LLM uses this to generate a more accurate workstream breakdown — not generic consulting phases, but task structures that reflect how this type of problem is actually being solved in the market right now. A static rule engine cannot do this.

The combination — LLM for understanding and planning, embeddings for semantic matching, web search for grounding — is why this is a generative AI solution and not a better spreadsheet.

---

### Product Boundaries — What This Product Intentionally Does Not Do

Being clear about what the product refuses to do is as important as what it does.

**It does not make the staffing decision.** The output is a recommendation with a confidence score (fit), not an assignment. Every recommendation requires a human to review, override, and approve. The product surfaces the shortlist; the partner or engagement manager makes the call. This is not a limitation to fix later — it is a deliberate boundary. AI-made staffing decisions create accountability gaps that no consulting firm can accept.

**It does not integrate with HR, ERP, or billing systems.** The MVP reads from an Excel file. At scale, it would read from a People system. But it does not write back. It does not create resource bookings, update availability flags, or trigger Workday workflows. Integration is a future phase with significant change management implications. The MVP proves the value of the intelligence layer first.

**It does not handle utilization forecasting or capacity planning.** Those are quarterly planning problems with different stakeholders, different data, and different decision cadences. The prototype solves the tactical, project-level question. Strategic workforce planning is a separate product.

**It does not learn from outcomes.** If a recommended consultant turns out to be a poor fit for a project, that signal does not feed back into the model. The MVP does not close the feedback loop. This is the biggest gap between what exists now and what a production system would need.

**It does not verify or validate skill claims.** If a consultant's profile says they have Advanced Tableau skills, the system takes that at face value. It does not cross-check with completed project work, peer reviews, or certifications. The quality of the output is bounded by the quality of the skills database.

---

### Success Metrics — How You Know It Is Working

Three layers of measurement, from immediate to lagging.

**Layer 1 — Adoption (weeks 1–4)**
- Time from project description to downloaded report: target under 5 minutes, measured end-to-end.
- Report download rate per session: if a user runs the pipeline but never downloads the report, the output is not trusted or used. Target: >70% download rate.
- Return usage: does the same engagement manager use it again? A one-time demo is not adoption.

**Layer 2 — Output quality (months 1–3)**
- Human override rate: what percentage of primary resource recommendations get replaced before the staffing plan is submitted? High override means low fit accuracy. Target: <40% primary override rate.
- Skill coverage: does the recommended team cover the required skills identified by the pipeline? Measure the delta between recommended skills and approved staffing.
- Bench utilisation delta: are consultants identified as high-fit actually available, or does the system recommend people already allocated? The availability score should reduce this mismatch.

**Layer 3 — Business outcome (months 3–12, requires retrospective tracking)**
- Project delivery risk correlation: do engagements staffed using the tool have lower early-warning risk flags than those staffed manually? This is the hardest metric to isolate but the most meaningful.
- Engagement manager time saved: self-reported via quarterly survey. If the answer is not "at least two hours per engagement," the tool has not changed the workflow.

---

## Part 2 — AI System Design Explanation

### Prompting Approach

The system uses two distinct LLM calls, each with a different role.

**Call 1 — Skill Extraction (web_search node)**

System prompt role: *technical analyst.* The model is instructed to read a problem statement plus web search results and return a structured JSON object with three fields: `required_skills` (always in English, regardless of output language, because these feed the embedding matcher), `search_context` (a brief summary of what the search revealed), and `difficulty` (a 0–1 float).

The system prompt is intentionally narrow. It does not ask the model to plan, recommend, or reason about staffing. It only asks it to identify skills and technology. Keeping this prompt single-purpose reduces hallucination surface and makes the JSON output more reliable.

Example: for a problem about cross-border payment reconciliation, the model returns skills like "SAP Finance," "SWIFT messaging," "data governance," and "regulatory compliance" — not generic terms like "banking" or "finance." The web search context from Tavily grounds the extraction in current industry practice rather than training data alone.

**Call 2 — Solution Generation (generate_solution node)**

System prompt role: *solution architect.* The model receives the problem statement plus a ranked list of technologies with their team skill-strength scores. It is instructed to generate a task/workstream breakdown that is biased toward the technologies where the team is strongest.

The key prompt instruction: "Include non-engineering work where relevant — product discovery, project scoping, architecture, QA, testing, release planning, observability, and guardrails." This prevents the model from returning a generic engineering-only plan. For the reconciliation problem, it should include a "Regulatory Mapping and Sign-Off" workstream alongside the ETL engineering steps, because that is how this type of project actually runs.

Language handling: Call 1 (skill extraction) always runs in English. The required_skills list feeds the embedding pipeline, which operates in English-only vector space. Adding a language instruction to Call 1 would cause the model to return "सांख्यिकीय विश्लेषण" instead of "Statistical Analysis," breaking the semantic match against the English skills database. Call 2 (solution generation) does accept a language parameter, because the action descriptions in the output are for human reading, not for embedding.

---

### Tools, Agents, and Workflows

**Tavily (web search tool)**

Used in Call 1 to enrich the problem statement before skill extraction. The query is the first 400 characters of the problem statement (Tavily's API limit). Returns five search results that are concatenated into the LLM prompt as context.

The decision to use Tavily rather than relying solely on the LLM's training data: consulting problem types evolve. A problem about "AI governance frameworks" in 2024 involves different skills and frameworks than it would have in 2022. Tavily grounds the extraction in current practice.

**LangGraph (workflow orchestration)**

The pipeline is a directed acyclic graph with six nodes: load_resources → web_search → compute_strength → generate_solution → score_resources → generate_report.

LangGraph streams node updates via Server-Sent Events. Each node completion emits a `step` event; each `get_stream_writer()` call emits a `progress` event. The Streamlit UI renders both in real time. This is not a ReAct-style autonomous agent — it is a deterministic pipeline with two bounded LLM calls. The choice of deterministic over autonomous was deliberate: consulting staffing decisions require traceability and predictability. An agent that decides to call tools in an unpredictable order is not appropriate here.

**Sentence-Transformers (semantic matching)**

Model: `nomic-ai/nomic-embed-text-v1.5`. Runs locally on CPU. Computes cosine similarity between required skills (from Call 1) and the 38 skills in the Excel database.

Threshold: similarity > 0.5 counts as a match. If no skill clears 0.5, the top-3 by similarity are used as a fallback. This prevents the system from returning zero results when the skill vocabulary in the problem statement does not exactly match the database labels.

---

### Key Failure Modes and Guardrails

**Failure mode 1: LLM returns malformed JSON**

Both LLM calls request `response_format: json_object`. Despite this, models occasionally return JSON wrapped in markdown code fences, or omit required keys. Guard: both nodes parse the response and check for the presence of required keys before accepting the output. If validation fails, a deterministic fallback runs — for skill extraction, keyword matching against the problem text; for solution generation, a pre-built six-step plan drawn from the top-scoring skills.

**Failure mode 2: Tavily is unavailable or rate-limited**

The web_search node catches all exceptions from the Tavily client. If the search fails, the pipeline continues with only the problem statement — no web enrichment. The fallback skill extraction still runs. The output is slightly less grounded in current industry context but remains usable.

**Failure mode 3: Required skill vocabulary mismatch**

If a project description uses terminology that does not exist in the skill database (e.g., "Databricks" when the database only has "Spark"), the cosine similarity may not clear the 0.5 threshold. Guard: top-k fallback ensures at least three skills are always matched. The fit score for those matches will be lower, which is the correct signal — it means the team's coverage of that problem type is weak.

**Failure mode 4: Cross-language embedding degradation**

If the skill extraction LLM call accidentally returns skills in a non-English language, the embedding space degrades. "डेटा विश्लेषण" and "Data Analysis" will not score high cosine similarity even though they are the same concept. Guard: the skill extraction prompt explicitly instructs the model to keep `required_skills` in English regardless of the output language setting. The solution generation prompt, which produces human-readable text, accepts the language parameter freely.

**Failure mode 5: Stale availability data**

The Excel database reflects availability at the moment it was last updated. If a consultant's availability changes after the database was exported, the fit score reflects outdated information. Guard: none currently — this is a known gap. The report includes availability hours per consultant, surfacing the assumption for human review.

---

### What Breaks at Scale and How to Address It

**Excel → proper database**

At 35 consultants, Excel is fine. At 350, reading the whole file on every pipeline run becomes slow and error-prone. At 3,500, it breaks entirely. Migration path: replace the Excel reader with a PostgreSQL or Cosmos DB read. The data model (users, skills, levels, user_skills) is already normalized to four tables — migration is a swap of the data layer, not a redesign.

**Single-threaded SSE pipeline**

Currently, one pipeline run occupies one FastAPI worker. Two simultaneous users compete for the same thread. At scale, the solution is async node execution (LangGraph supports async) plus horizontal scaling of the FastAPI service behind a load balancer. The LLM calls (which take 5–40 seconds each) are the primary bottleneck; async handling would allow other requests to proceed while waiting for OpenRouter responses.

**No embedding cache**

Every pipeline run re-embeds the required skills against the full skill database. With 38 skills, this takes under one second. With 3,800 skills, it becomes meaningful latency. Solution: cache embeddings for known skill strings. The database skill names are static; they can be embedded once and stored. Required skills from each pipeline run are dynamic but can be cached per unique problem statement hash.

**No feedback loop**

The system cannot improve its recommendations over time. A consultant recommended at fit 0.72 who delivered an excellent project and one who delivered a poor project look identical to the system a month later. Production solution: capture outcome signals (partner rating, project risk flags, consultant self-assessment) and use them to calibrate the fit score formula — either as a fine-tuning signal or as a re-weighting of the availability vs. skill components.

**LLM cost at volume**

Two LLM calls per pipeline run. At 100 runs per day, this is manageable with free-tier OpenRouter models. At 1,000 runs per day, cost and latency become real constraints. Solutions: prompt caching for repeated problem types (Anthropic-style cache headers), model downgrading for skill extraction (a smaller model handles JSON extraction reliably), and response caching for identical problem statements.

---

*Document version: MVP 1.1 | Prepared June 2026*

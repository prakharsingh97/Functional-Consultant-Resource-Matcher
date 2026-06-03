# Why I Chose To Build It This Way

## Product Thesis

The Resource Matcher MVP is not meant to be a heavyweight workforce planning platform. It is a fast proof of value for a very specific consulting-firm problem: teams often know they have talent somewhere in the organization, but they do not have a quick, structured way to translate a client problem into workstreams, required capabilities, and a credible staffing recommendation.

The product bet is simple: if a Product Manager, Engagement Manager, or delivery lead can go from a rough problem statement to a defensible resource recommendation in under five minutes, the tool creates immediate value. It reduces blank-page effort, makes assumptions visible, and gives stakeholders something concrete to review. That matters more for an MVP than building every downstream scheduling, utilization, or approval feature.

This is why the MVP focuses on the core loop:

```text
Problem statement -> task breakdown -> skill matching -> resource matrix -> PM-ready report
```

The intent is not to replace human staffing judgment. The intent is to compress the first pass of analysis so the human conversation starts from a structured recommendation instead of a vague Slack thread or spreadsheet search.

## Why This Scope

I chose a narrow but meaningful workflow: resource matching for consultant profiles stored in some sort of database. In many organizations, especially large consulting environments, performance review data, contributions and work notes/streams are the practical source of truth for development and progress related operations. A perfect enterprise system might use Workday, SAP, internal staffing tools, project history, utilization forecasts, certifications, and HR permissions - and they can be ingested with the right set of MCP tools or data layers. But for the purpose of the MVP, I scoped it to a simple imitation of an RDBMS system: an Excel file with different sheets acting as tables. I added realistic sample skills, employees, levels, and availability so the product could demonstrate ground-level staffing decisions without requiring enterprise system access.

The MVP uses what a team could reasonably have available:

- a consultant list
- a skill catalog
- skill levels
- availability
- a project/problem statement
- access to free or low-cost AI/search tools

That lets the product demonstrate the main transformation: unstructured demand becomes structured delivery thinking. The report does not just rank people globally. It decomposes the work into tasks, maps skills to those tasks, and recommends primary/support resources. That is closer to how a Product Manager or consulting lead thinks: scope, workstreams, capability gaps, risks, and next decisions.

## Product Manager Lens

From a PM lens, the valuable artifact is not the model response. The valuable artifact is a decision package.

A useful report should help answer:

- What did the user actually ask for?
- What did we break that into?
- What features or deliverables are implied?
- What skills are required per workstream?
- Who can lead or support each piece of work?
- Where are the execution risks?
- What assumptions need validation before committing?
- What would success look like?

This is why the current report is moving toward a PM-ready structure: original query, executive summary, definitions, project breakdown, task resource recommendations, risks, and a downloadable `.docx`. A PM at a consulting firm needs a document that can enter a stakeholder conversation, not just a technical log.

## System Design Choices

The architecture deliberately keeps deterministic logic outside the LLM where possible.

The LLM is useful for interpreting the problem, generating a work breakdown, and enriching the request with broader context. But the matching math should be explainable. Skill strength and fit are computed outside the LLM using structured data:

- skill levels are weighted
- semantic similarity maps required skills to known skills
- availability contributes to task fit
- recommendations are tied to task-level resource assignments

This separation keeps the system interpretable, testable, and easier to debug. If the LLM returns bad JSON or a weak answer, the app can fall back to deterministic logic and still produce a useful report. That is an important MVP design choice: the demo should complete, even when live free-model infrastructure is imperfect.

The stack reflects the same product-first thinking:

- **Streamlit** for a fast interactive UI without a frontend build.
- **FastAPI** for clear API contracts and a real backend boundary.
- **LangGraph** for visible workflow orchestration.
- **Excel** because it is believable as a starting data layer and a good stand-in for RDBMS operations.
- **Tavily** for lightweight web context.
- **OpenRouter free models** to reduce cost and make experimentation accessible.
- **python-docx** because a PM-friendly report is the actual handoff artifact.

## AI-Native Development Approach

The build process was intentionally AI-native. The goal was not to let the LLM invent everything, but to use AI tools to move faster while keeping the problem bounded.

The development approach used:

- documentation lookup and MCP-style tool use for current library patterns
- planning plugins and iterative plans to keep work chunked
- mock-first contracts before implementation
- tests around each node, API route, and report artifact
- small commits that reflect how the system evolved
- prompts that crafted the LLM behaviour rather than specified what the LLM should do (Reasoning-and-Action style reasoning and workflow)

The important design choice was to reduce the LLM's scope. The LLM enhances the original request and helps produce structured planning output, but calculation, ranking, report assembly, API contracts, and test validation are handled by code. That keeps the system from becoming a black box.

This is also why the pipeline has fallback behavior. Free tools and free models are excellent for MVP velocity, but they are not always reliable. Building fallbacks keeps the product demo grounded. The LLM can fail and the user still gets a report.

## Why Testing Mattered

Following a test-driven loop made the AI-assisted build much safer. Each major part of the system has focused tests:

- Pydantic model contracts
- Excel data access
- FastAPI routes
- LangGraph node behavior
- semantic matching
- SSE streaming
- HTTP client parsing
- report generation

This created a self-correcting loop. When the implementation changed from global resource ranking to task-based recommendations, the tests forced the contracts and report output to change intentionally. When SSE streams failed mid-response, tests helped convert a raw protocol crash into structured error events. When reports looked empty, tests began inspecting `.docx` contents directly.

For an MVP, this is not engineering ceremony. It is product risk management. The faster AI helps you move, the more important it is to have guardrails that confirm the product still works.

## What Experience Informed The Build

The build reflects lessons from leading engineering teams through feature delivery:

- Version control matters because product direction changes quickly.
- A sanitized local environment matters because demos need to be reproducible.
- Data layers should start with what exists, not what the ideal enterprise architecture would be.
- Human-readable outputs matter because stakeholders need to review, question, and override recommendations.
- Scope must be defended constantly, especially when AI makes ambitious features feel easy.

The MVP is intentionally pragmatic. It shows how a consulting organization could begin to operationalize AI-assisted staffing without immediately needing deep integrations into every enterprise system.

Core insight my previous work has informed : you dont always need a frontier level model to do tasks when a more viable alternative exists and can be used

## Tradeoffs And Challenges

As a PM, visual artefacts are essential in planning. I started with several ideas and quickly had to trade them off or note down their deliberate deferral:

- A Gantt chart overlay for resources and delivery phases.
- Editable human-in-the-loop checkpoints after each workflow step.
- Rerun/diff workflows after a PM edits the task breakdown.
- Better utilization balancing to avoid overusing one star resource.
- Richer resource histories, including prior project outcomes and domain experience.
- Upsert/ingest pipelines for keeping consultant skills current.
- More nuanced treatment of new resources who have skills but little recorded delivery history.

Those are valuable ideas for a polish product, but they would expand the MVP from a proof of value into a platform. The current version focuses on the shortest path to impact: make the initial staffing recommendation faster, more structured, and easier to review.

The biggest practical challenges were around live AI reliability and report usefulness. Free models can return malformed JSON. Embedding models can fail to load. Streaming endpoints can close early if an exception occurs. Early reports looked too thin and too much like generic technical output. Each of those failures shaped the product: add fallback logic, add console logs, harden SSE errors, and make the report more PM-oriented. To keep the MVP scoped to a reasonable budget I moved the LLM API overhead to openrouter and enlisted a cheaper LLM (gemma4-31B/stepfun-3.7-flash) which are marginally cheaper than even the cheapest gemini model available. 

## The Product Value

The final MVP is valuable because it turns ambiguity into a reviewable plan. It does not claim to solve staffing perfectly. It gives a consulting lead a first pass that is fast, structured, explainable, and tied to the organization's actual skills.

That is the right MVP shape: small enough to build, real enough to demo, and useful enough to start a better conversation.

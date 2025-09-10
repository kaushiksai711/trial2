# Project Athena — Team To‑Do Plan (Phase 1 & Phase 2)

This is the authoritative team task board for building Athena (domain‑specific FAQ chatbot) as defined in `docs/architecture.md` and `README.md`.

Legend
- Owners: @A (Data/Ingestion), @B (Symbolic/MeTTa), @C (Backend/API), @D (QA/DevOps/UI)
- Status: [ ] Not started, [~] In progress, [x] Done
- Dependencies are listed explicitly under each task where relevant

Team Roles & Responsibilities
- @A Data & Ingestion Engineer
  - Document/Web ingestion, chunking, LLM extraction to JSON, entity standardization
- @B Symbolic Knowledge/MeTTa Engineer
  - Domain schema, MeTTa atom modeling, Atomspace persistence, query design (Graph RAG)
- @C Backend/API Orchestrator
  - Python orchestration, MeTTa Motto integration, endpoints, runtime configuration
- @D QA/DevOps & UX
  - Test plans, CI, observability, provenance & explainability, minimal chat UI

---

## Phase 0 — Foundations (applies to all)

- [ ] Create and share environment & secrets
  - Output: `.env.example` with `GEMINI_API_KEY`, `OPENAI_API_KEY`, others as needed
  - Acceptance: `README.md` instructions updated; teammates can run local scripts without ambiguity
  - Owner: @C; Reviewer: @D

- [ ] Pin dependencies and create `requirements.txt`
  - Include: `hyperon` (or `hyperon-experimental`), `metta-motto`, `pdfplumber`, `pypdf2`, `beautifulsoup4`, `trafilatura`, `requests`, `fastapi`, `uvicorn`, `python-dotenv`
  - Acceptance: Clean install in a fresh venv on Windows; app imports succeed
  - Owner: @C; Reviewer: @D

- [ ] Project skeleton under `backend/`
  - Directories: `ingestion/`, `nsai/`, `metta/`, `query/`, `api/`, `ui/`
  - Acceptance: All modules import; placeholder `__init__.py` present
  - Owner: @C; Reviewer: @B

---

## Phase 1 — Offline Knowledge Ingestion & Atomspace Population

### 1. Ingestion & Chunking (@A)

- [ ] Implement PDF ingestion
  - Path: `backend/ingestion/ingest.py`
  - Details: Use `pdfplumber` to extract text; chunk with overlap; write JSONL to `data/processed/chunks.jsonl`
  - Acceptance: For 2 sample PDFs in `data/raw/`, outputs >= 20 chunks with overlap preserved
  - Owner: @A; Reviewer: @D

- [ ] Implement web page ingestion (basic)
  - Path: `backend/ingestion/fetch_web.py`
  - Details: `requests` + `trafilatura` to extract main text; normalize (strip boilerplate)
  - Acceptance: Given a URL list, produce chunked text in the same format as PDFs
  - Owner: @A; Reviewer: @C

- [ ] Add CLI wrappers
  - Paths: `backend/ingestion/__main__.py` (e.g., `python -m backend.ingestion --pdf data/raw/`)
  - Acceptance: Single command runs ingestion and writes outputs deterministically
  - Owner: @A; Reviewer: @D

### 2. NSAI Extraction to Structured JSON (@A)

- [ ] Define JSON schema for extracted knowledge
  - Path: `backend/nsai/schema.py`
  - Fields: `concept`, `sub_concept`, `explanation`, `source?`, `media?[]`
  - Acceptance: `pydantic` model validates payloads; schema doc added to `README.md`
  - Owner: @A; Reviewer: @B

- [ ] Design few-shot prompts for extraction
  - Path: `backend/nsai/prompts/extract_prompt.txt`
  - Acceptance: Prompts capture Domain→Concept→Sub-concept→Explanation + provenance
  - Owner: @A; Reviewer: @D

- [ ] Implement LLM extraction (provider-agnostic)
  - Path: `backend/nsai/extract.py`
  - Details: Call Gemini or OpenAI via Motto or Python SDK; parse to schema; batch process chunks
  - Acceptance: From 50 chunks, produce valid JSON objects (>=90% schema‑valid) stored at `data/processed/extracted.jsonl`
  - Owner: @A; Reviewer: @C

- [ ] Entity standardization & dedup
  - Path: `backend/nsai/normalize.py`
  - Details: Canonical form mapping (e.g., `copay` vs `co‑payment`), basic similarity heuristics
  - Acceptance: Duplicates merged; emits mapping table at `data/processed/canonical_map.json`
  - Owner: @A; Reviewer: @B

### 3. Translate JSON → MeTTa atoms (@B)

- [ ] Domain schema & symbol conventions
  - Path: `docs/domain_schema.md`
  - Details: Types, relations (`has-concept`, `has-subconcept`, `has-explanation`, `has-content`, `has-source`, `has-media`), naming rules
  - Acceptance: Reviewed and approved; used consistently by translator and queries
  - Owner: @B; Reviewer: @D

- [ ] Implement translator
  - Path: `backend/metta/translate.py`
  - Details: Convert normalized JSON objects to S‑expressions; escape strings; create reusable IDs for explanations/media
  - Acceptance: For sample input, generates `.metta` text and/or direct API calls compatible with Hyperon
  - Owner: @B; Reviewer: @C

### 4. Atomspace creation & persistence (@B)

- [ ] Build/manage Atomspace
  - Path: `backend/metta/store.py`
  - Details: Initialize `&athena_kb`, add atoms (`add-atom`) via Hyperon; optional snapshot/restore hooks
  - Acceptance: After running store, `match` queries return expected entities; snapshot can be reloaded
  - Owner: @B; Reviewer: @D

- [ ] Seed dataset & smoke tests
  - Path: `backend/metta/seed_and_test.py`
  - Details: Ingest 10–20 extracted items; run basic `match` queries; print results
  - Acceptance: Pass/fail summary printed; zero exceptions on clean environment
  - Owner: @B; Reviewer: @C

### 5. Documentation & handoff (@A, @B)

- [ ] Update `README.md` with Phase 1 runbook
  - Steps: ingest → extract → normalize → translate → store → smoke test
  - Acceptance: A new contributor can complete Phase 1 in under 30 minutes
  - Owner: @A & @B; Reviewer: @D

Milestone M1 (end of Phase 1)
- Seeded Atomspace `&athena_kb` populated from sample documents
- Verified queries return expected facts
- All scripts runnable via documented commands

---

## Phase 2 — Online Conversational (Graph RAG) Pipeline

### 1. Query generation (NL → MeTTa) (@C, @B)

- [ ] NL‑to‑Query prompt design
  - Path: `backend/query/prompts/nl2match.txt`
  - Acceptance: Covers common patterns (single hop, multi‑hop, filters)
  - Owner: @C; Reviewer: @B

- [ ] Implement NL‑to‑Query service
  - Path: `backend/query/nl2match.py`
  - Details: LLM or rules generate `match` expressions; validate against schema
  - Acceptance: 20 test questions converted to valid `match` queries with >= 90% validity
  - Owner: @C; Reviewer: @D

### 2. Query execution & traversal (@B)

- [ ] Query engine wrapper
  - Path: `backend/query/execute.py`
  - Details: Run `match`/composite traversals; limit/score results; sanitize outputs
  - Acceptance: Deterministic outputs on seeded Atomspace; timeouts handled
  - Owner: @B; Reviewer: @C

### 3. Answer synthesis (LLM) (@C)

- [ ] Response generator with MeTTa Motto or SDK
  - Path: `backend/query/synthesize.py`
  - Details: Feed only retrieved facts; enforce grounding; include sources
  - Acceptance: Example questions return fluent answers with explicit provenance
  - Owner: @C; Reviewer: @D

### 4. Explainability & provenance (@D)

- [ ] Trace & source packaging
  - Path: `backend/query/trace.py`
  - Details: Return matched atoms, traversal path, and source links alongside answer
  - Acceptance: UI/API shows expandable trace block; links resolve
  - Owner: @D; Reviewer: @B

### 5. API & minimal UI (@C, @D)

- [ ] FastAPI endpoints
  - Path: `backend/api/main.py`
  - Endpoints: `POST /ingest`, `POST /query`, `GET /healthz`
  - Acceptance: `uvicorn backend.api.main:app --reload` serves endpoints locally
  - Owner: @C; Reviewer: @D

- [ ] Minimal chat UI (optional prototype)
  - Path: `backend/ui/app.py` (Streamlit) or `frontend/` (React)
  - Acceptance: Ask a question, view answer, sources, and trace
  - Owner: @D; Reviewer: @C

### 6. Testing, Observability, and Ops (@D)

- [ ] Unit & integration tests
  - Path: `tests/`
  - Details: Ingestion, schema validation, translator, query, synthesize
  - Acceptance: CI green on PR; coverage > 70% of core modules
  - Owner: @D; Reviewer: @C

- [ ] Logging/metrics & cost tracking
  - Path: integrated into services; config in `.env`
  - Acceptance: Per‑stage logs; token/cost metrics captured for LLM calls
  - Owner: @D; Reviewer: @C

Milestone M2 (end of Phase 2)
- End‑to‑end question → answer works locally via API/UI
- Answers show sources and trace; NL‑to‑Query reliability ≥ 90% on test set
- Basic tests and logging in place

---

## Cross‑Cutting Tasks & Nice‑to‑Haves

- [ ] Persistence/snapshot strategy for Atomspace (@B)
- [ ] Domain ontology & typing refinements (@B)
- [ ] Rate limiting & retries for LLM calls (@C)
- [ ] Cost guardrails & caching (@C, @D)
- [ ] Subgraph visualization (stretch) (@D)

---

## Daily Standup Template

- Yesterday: …
- Today: …
- Blockers: …

---

## Acceptance Criteria (Global)

- Phase 1 can be executed by a new dev in < 30 minutes using the runbook in `README.md`
- Phase 2 can answer 10 representative domain questions with sources and traces
- No hardcoded secrets; reproducible installs on Windows

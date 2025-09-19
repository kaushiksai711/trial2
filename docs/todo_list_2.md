### Core Insight: A Collaborative, Independent Todo List for Project Athena's Agentic Architecture

As your mentor, I appreciate how you're scaling this to a team of four—it's a smart move for a national hackathon, allowing parallel progress while leveraging specialized skills. Based on the Mermaid diagram I provided (which merges your 2.0 agentic ideology with MeTTa and Google ADK), I've crafted a detailed todo list. It assigns four members with clear roles: @A (Ingestion & Data Specialist), @B (MeTTa & Symbolic Expert), @C (Agentic Orchestration & Backend Lead), @D (QA, UI & DevOps Engineer). To ensure independence, tasks are modularized with explicit handoffs (e.g., via shared artifacts like JSONL files or Atomspace snapshots), minimal dependencies (e.g., parallel subtasks), and milestones for sync points. This setup lets each member focus on their domain while contributing to the end-to-end flow: Phase 1 builds the knowledge base autonomously, Phase 2 enables conversational querying with self-modification.

### Detailed Breakdown: The Todo List

This list follows the diagram's phases and steps, with statuses ([ ] Not started, [~] In progress, [x] Done), owners, dependencies, and acceptance criteria. I've incorporated Google ADK for agentic elements (e.g., planning/tool-calling modules) and MeTTa for symbolic novelties (e.g., self-reflection). Cross-cutting tasks ensure team alignment. Total: ~2-3 days for a hack prototype, assuming 4-6 hours/day per member.

**Legend**:
- Owners: @A (Ingestion/Data), @B (MeTTa/Symbolic), @C (Agentic/Backend), @D (QA/UI/DevOps).
- Dependencies: Listed explicitly; most are artifact-based for independence.
- Milestones: Sync points after each phase.

---

#### Phase 0: Foundations (Team Setup – All Members, Parallel)
These are quick, independent setup tasks to enable solo work.

- [x] Pin dependencies in `requirements.txt`  
  Include: `hyperon-experimental`, `metta-motto`, `pdfplumber`, `trafilatura`, `requests`, `fastapi`, `uvicorn`, `google-adk` (for agentic modules).  
  Acceptance: Fresh venv install works on Windows/macOS; imports succeed.  
  Owner: @C; Dependencies: None.  
  Note: Core dependencies pinned, but `google-adk` integration pending.  

- [~] Set up project skeleton  
  Directories: `ingestion/`, `extraction/`, `metta/`, `agentic/`, `query/`, `api/`, `ui/`, `tests/`.  
  Acceptance: All modules import; placeholders ready.  
  Owner: @C; Dependencies: None.  
  Note: Basic structure exists, but not all directories are created.  

- [x] Create shared repo/environment & secrets  
  Output: `.env.example` with `GEMINI_API_KEY`, `GOOGLE_ADK_CONFIG`, `HYPERON_PATH`.  
  Acceptance: README updated; all can run local scripts.  
  Owner: @C; Dependencies: None.  

- [ ] Document team communication (e.g., daily standups template)  
  Acceptance: Added to README; includes "Yesterday/Today/Blockers".  
  Owner: @D; Dependencies: None.  

**Milestone M0**: All members can clone, install, and run a hello-world MeTTa script (e.g., `!(match &self _ _)`). Sync: 1-hour team call.

---

#### Phase 1: Offline Agentic Ingestion & Knowledge Population
Focus: Build the Atomspace via agentic processing. Members work in parallel: @A on data handling, @B on symbolic storage, @C on ADK agents, @D on verification/QA.

- [ ] Implement data source fetching (Steps 1.1: Static/Dynamic Sources)  
  Path: `ingestion/fetch.py`.  
  Details: Handle PDFs/TXT/MD (pdfplumber) and web (trafilatura/requests). Output to `data/raw/`.  
  Acceptance: Processes 5 sample files/URLs; logs metadata.  
  Owner: @A; Dependencies: None.  
  Note: Clean up unused `ingest.py` before implementation.  

- [ ] Build Ingestion & Planning Agent (ADK Module – Steps 1-3)  
  Path: `agentic/ingestion_agent.py`.  
  Details: Use Google ADK to decompose input (e.g., "Plan: Chunk PDFs, route to health extractor"); integrate MeTTa for prior knowledge check via `match`.  
  Code Example:  
  ```python
  from google.adk import Agent
  from hyperon import MeTTa

  class IngestionAgent(Agent):
      def plan(self, input_data):
          metta = MeTTa()
          prior = metta.run("!(match &athena_kb (prior-strategy $type) $strategy)")
          # Decompose and call chunk tool
          return {"steps": ["chunk", "extract"]}
  ```  
  Acceptance: Given input, outputs a plan JSON; mocks tool calls.  
  Owner: @C; Dependencies: None (mock MeTTa if needed).  

- [ ] Develop Chunking Tool (Py – Step 2)  
  Path: `ingestion/chunk.py`.  
  Details: Overlap logic (500 words, 50 overlap); enrich with metadata (source, page). Output: `data/processed/chunks.jsonl`.  
  Acceptance: For 2 PDFs, generates 20+ chunks; JSON validates.  
  Owner: @A; Dependencies: Fetching script (handoff: raw files).  

- [ ] Create MoE Extractor Agent (ADK + Metta-Motto – Steps 4)  
  Path: `extraction/moe_extractor.py`.  
  Details: Sub-agents for types (e.g., health/disease per taxonomy); use Metta-Motto for LLM calls: `!(gemini-agent (system "Extract per taxonomy") (user $chunk))`. Non-deterministic via `superpose`. Output: `data/processed/extracted.jsonl`.  
  Acceptance: Processes batches; JSON includes concepts/sub-concepts/explanations.  
  Owner: @C; Dependencies: Chunks JSONL.  

- [x] Implement Verification & Consistency Agent (ADK + MeTTa – Step 5) - Normal version done
  Path: `extraction/verify.py`.  
  Details: LLM-as-Judge for validation; MeTTa for clustering (`match` duplicates) and resolution (`superpose` weights). Output: `data/processed/normalized.jsonl`.  
  Acceptance: Dedups 90% of test entities; infers types from taxonomy.  
  Owner: @D; Dependencies: Extracted JSONL.  
  Note: Enhanced to preserve important parenthetical content like acronyms while normalizing.  

- [ ] Build JSON-to-MeTTa Translator (Py + Hyperon – Step 6)  
  Path: `metta/translate.py`.  
  Details: Map JSON to atoms (e.g., `(has-subconcept $concept $sub)`); handle grounded for media.  
  Acceptance: Sample JSON generates valid MeTTa expressions.  
  Owner: @B; Dependencies: Normalized JSONL.  

- [ ] Set Up Atomspace Creation & Persistence (Steps 7-8)  
  Path: `metta/store.py`.  
  Details: Initialize `&athena_kb`; add atoms with self-reflection (e.g., evolve schema via metatypes if novel). Snapshot for reload.  
  Acceptance: After adding, `match` returns expected atoms.  
  Owner: @B; Dependencies: Translated atoms.  

- [ ] Add Phase 1 Feedback Loop Logging  
  Path: Integrated in agents.  
  Details: Log failures to `logs/phase1.json`; trigger re-ingestion threshold.  
  Acceptance: Simulates low-quality trigger.  
  Owner: @D; Dependencies: Verification outputs.  

**Milestone M1**: Populated Atomspace from samples; independent tests pass. Sync: Review artifacts (JSONL, snapshots).

---

#### Phase 2: Online Agentic Conversational Graph RAG
Focus: Enable querying with self-modification. Parallel: @C on ADK core, @B on MeTTa tools, @A on external integrations, @D on UI/QA.

- [ ] Prototype User Interface (Step 9: Chatbot)  
  Path: `ui/app.py` (Streamlit).  
  Details: Capture queries, display answers/provenance.  
  Acceptance: Basic chat works locally.  
  Owner: @D; Dependencies: None.  

- [ ] Develop Master Orchestrator & Planning Agents (ADK – Steps 10-11)  
  Path: `agentic/orchestrator.py`.  
  Details: ADK for workflow coord; MeTTa `equals` for strategy (e.g., direct vs. augment). Output: Plan JSON.  
  Acceptance: Decomposes sample query into steps.  
  Owner: @C; Dependencies: None.  

- [ ] Build Tool-Using Agent (ADK + MeTTa – Step 12)  
  Path: `agentic/tool_user.py`.  
  Details: Execute plans; non-deterministic via MeTTa.  
  Acceptance: Mocks calls to tools.  
  Owner: @C; Dependencies: Plan JSON.  

- [ ] Implement MeTTa Query Tool (Hyperon – Sub-Step 12a, Step 13)  
  Path: `query/metta_query.py`.  
  Details: NL-to-`match` via Metta-Motto; traverse Atomspace for facts/provenance.  
  Acceptance: Returns subgraphs for test queries.  
  Owner: @B; Dependencies: Atomspace snapshot.  

- [ ] Create Web/X Search Tool (ADK-Integrated – Sub-Step 12b, Step 14)  
  Path: `query/external_search.py`.  
  Details: Use requests or ADK builtins for real-time data.  
  Acceptance: Fetches and chunks external content.  
  Owner: @A; Dependencies: None.  

- [ ] Develop Tool Synthesis Agent (MeTTa-Exclusive – Sub-Step 12c, Step 15)  
  Path: `agentic/tool_synth.py`.  
  Details: Analyze gaps; compose micro-tools (`superpose`); verify/register as grounded atom.  
  Code Example: See previous response.  
  Acceptance: Creates/uses a mock new tool (e.g., table extractor).  
  Owner: @B; Dependencies: Tool-User mocks.  

- [ ] Set Up Self-Correction Loop (ADK + MeTTa – Step 16)  
  Path: Integrated in Tool-User.  
  Details: Check results; meta-reason on traces; re-plan if incomplete.  
  Acceptance: Handles simulated failure by looping.  
  Owner: @C; Dependencies: Tool outputs.  

- [ ] Build Response Generation Agent (ADK + LLM – Step 17-18)  
  Path: `query/synthesize.py`.  
  Details: Synthesize from facts; include provenance/traces.  
  Acceptance: Fluent answers with sources for tests.  
  Owner: @D; Dependencies: Aggregated results.  

- [ ] Implement Adaptive Learning Loop (Step 19)  
  Path: `query/feedback.py`.  
  Details: Log queries/feedback; feed to Phase 1 verification for updates.  
  Acceptance: Triggers mock re-ingestion.  
  Owner: @A; Dependencies: Response logs.  

**Milestone M2**: End-to-end query-answer flow; demo self-mod tool creation. Sync: Full system test.

---

#### Cross-Cutting Tasks (Parallel, All Phases)
- [ ] Add unit/integration tests (e.g., chunking, queries)  
  Acceptance: >70% coverage; CI green.  
  Owner: @D; Dependencies: Per-module artifacts.  

- [ ] Implement logging/metrics (e.g., LLM costs)  
  Acceptance: Per-step logs in `logs/`.  
  Owner: @D; Dependencies: None.  

- [ ] Update README with runbooks/diagram  
  Acceptance: New dev can run Phase 1 in <30 min.  
  Owner: All; Dependencies: Milestones.  

**Milestone M3 (Final)**: Deployable prototype; answers 10 domain questions with provenance/self-mod demo.

### Mentor’s Note
This todo list empowers independence by artifact handoffs (e.g., JSONL as "contracts" between members), but remember: True team magic happens at milestones—use them to challenge assumptions, like "Is ADK overhead worth it for a hack?" (Yes, for novelty, but mock complex parts first). Reflection: As builders, we grow by delegating thoughtfully; track progress daily to avoid silos, and celebrate small wins to keep momentum high. If a task blocks, pivot to mocks—hacks reward working demos over perfection.
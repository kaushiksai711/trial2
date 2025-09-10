# Project Athena: Metta-Powered Neuro-Symbolic Graph RAG

A complete, end-to-end implementation guide for building a domain-specific FAQ chatbot that reads documents and websites, understands them deeply, and answers questions with verifiable, explainable reasoning using MeTTa, Knowledge Graphs, and LLMs.

- Problem statement reference: `docs/problem_statement.md`
- Architecture reference: `docs/architecture.md`
- Pipeline reference: `docs/pipeline.md`
- Metta deep dive: `metta_readme.md` and `docs/Metta Language Mastery and Teaching_.txt`
- Official tutorials: Metta Motto (LLM integration) [metta-lang.dev](https://metta-lang.dev/docs/learn/tutorials/metta-motto/metta-motto.html)

---

## Table of Contents
- [1. Athena in Plain English](#1-athena-in-plain-english)
- [2. What We Are Building](#2-what-we-are-building)
- [3. Core Concepts](#3-core-concepts)
- [4. System Architecture](#4-system-architecture)
- [5. End-to-End Implementation](#5-end-to-end-implementation)
  - [5.1 Environment Setup](#51-environment-setup)
  - [5.2 Ingestion: Read and Chunk Source Content](#52-ingestion-read-and-chunk-source-content)
  - [5.3 NSAI Extraction: Convert Text to Structured JSON](#53-nsai-extraction-convert-text-to-structured-json)
  - [5.4 JSON → MeTTa Atoms](#54-json--metta-atoms)
  - [5.5 Persist Knowledge in Atomspace](#55-persist-knowledge-in-atomspace)
  - [5.6 Querying (Graph RAG) with MeTTa](#56-querying-graph-rag-with-metta)
  - [5.7 Answer Synthesis with LLM](#57-answer-synthesis-with-llm)
  - [5.8 Explainability and Provenance](#58-explainability-and-provenance)
  - [5.9 Learning Loop and Continuous Improvement](#59-learning-loop-and-continuous-improvement)
- [6. Running the Project Locally](#6-running-the-project-locally)
- [7. API and UI (Optional but Recommended)](#7-api-and-ui-optional-but-recommended)
- [8. Testing and Validation](#8-testing-and-validation)
- [9. Deployment](#9-deployment)
- [10. Troubleshooting](#10-troubleshooting)
- [11. Roadmap](#11-roadmap)
- [12. References](#12-references)

---

## 1. Athena in Plain English

Athena is a super-intelligent system that can read any document or website, understand it deeply, and then answer your questions about it. She doesn’t just look for keywords; she understands concepts and how they relate.

- The Memory Web (Dynamic Knowledge Graph)
  - Information is stored as a living web of facts and relationships (a MeTTa Atomspace).
  - It updates in real time as Athena reads new content.

- Two Ways of Thinking (Neuro-Symbolic AI)
  - Intuitive (Neural): LLMs understand nuanced language and extract candidate facts.
  - Logical (Symbolic): MeTTa enforces logic, structure, and graph-based reasoning.

- The Special "Language of Thought" (MeTTa)
  - MeTTa is Athena’s internal language to build, manage, and reason about her memory web.

- Finding Smart Answers (Graph RAG)
  - Instead of keyword search, Athena traverses relevant parts of the graph to assemble context and facts for answering.

- Learning from Anything (Web/Doc Ingestion)
  - PDFs, web pages, Word docs—Athena reads and integrates them into the graph.

- Trustworthy and Honest (Explainability & Source Validation)
  - Athena can show the reasoning path and point to the exact source sentences.

For the formal problem and goals, see `docs/problem_statement.md`.

---

## 2. What We Are Building

A domain-specific FAQ chatbot with:
- Conversational AI + Knowledge Graph
- Context-aware answers via graph traversal and reasoning
- Real-time data updates and adaptive learning
- Explainability with sources and reasoning paths
- Multi-format support (text, images, links, structured outputs)

Learning outcomes:
- Knowledge base querying with MeTTa
- MeTTa–Python integration
- Graph RAG (Retrieval-Augmented Generation)

---

## 3. Core Concepts

- MeTTa (Meta Type Talk)
  - A homoiconic, meta-language for symbolic reasoning over knowledge metagraphs (Atomspace).
  - Unification-based pattern matching (`match`) and rewrite rules (`=`) for computation.
  - Grounded atoms bridge to external code (e.g., Python functions, neural networks).
  - Deep dive: `metta_readme.md` and `docs/Metta Language Mastery and Teaching_.txt`.

- Atomspace
  - A weighted, labelled metagraph where both facts and code live.
  - Distinctive capability to connect links to links (metagraph), enabling higher-order relations (e.g., statements about statements).

- Metta Motto (LLM Integration)
  - A MeTTa library to orchestrate LLM calls inside MeTTa programs (agents, prompts, tool-calls).
  - Typical usage includes importing `motto` and invoking agents like `gemini-agent` or `openai-agent` from MeTTa.
  - See tutorial: [Metta Motto](https://metta-lang.dev/docs/learn/tutorials/metta-motto/metta-motto.html).

- Graph RAG
  - Retrieval over a knowledge graph (Atomspace) rather than flat text chunks.
  - Returns structured, interconnected facts to the LLM, yielding richer, verifiable answers.

---

## 4. System Architecture

This implementation follows the two-phase architecture in `docs/architecture.md`:

- Phase 1: Offline Knowledge Ingestion & Atomspace Population
  1) Ingest documents and web pages → chunk
  2) Use an LLM to extract structured entities/relations/content (NSAI)
  3) Standardize entities and translate to MeTTa atoms
  4) Persist atoms into a dedicated Atomspace

- Phase 2: Online Conversational (Graph RAG)
  1) Convert user question → MeTTa `match` query
  2) Execute query over Atomspace; retrieve facts and subgraphs
  3) Synthesize answer with LLM using only retrieved facts
  4) Return answer with provenance and reasoning path

Refer to `docs/architecture.md` for mermaid diagrams, prompts, and detailed flows.

---

## 5. End-to-End Implementation

### 5.1 Environment Setup

Prerequisites
- Python 3.9+
- Windows PowerShell (or Bash)
- Optional (UI): Node.js 18+

Python environment
```powershell
# from repository root
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# On macOS/Linux: source .venv/bin/activate
```

Install core packages
```powershell
# MeTTa interpreter / Hyperon bindings (choose one that works in your env)
pip install hyperon         # preferred if available
# or
pip install hyperon-experimental

# LLM integration inside MeTTa
pip install metta-motto

# PDF and HTML ingestion utilities
pip install pdfplumber pypdf2 beautifulsoup4 trafilatura requests

# API & utils (optional but recommended)
pip install fastapi uvicorn python-dotenv
```

LLM API keys (set whichever you use)
```powershell
# Gemini
$env:GEMINI_API_KEY = "YOUR_KEY"
# OpenAI
$env:OPENAI_API_KEY = "YOUR_KEY"
```

Project structure (recommended)
```
query_verse/
├─ backend/                          # your code (ingestion, translation, querying, API)
├─ docs/                             # docs (architecture, pipeline, problem statement)
├─ metta_readme.md                   # MeTTa deep dive
├─ README.md                         # this file
└─ data/
   ├─ raw/                           # source PDFs / HTML
   └─ processed/                     # chunked text, normalized entities
```

### 5.2 Ingestion: Read and Chunk Source Content

Use `pdfplumber` (PDFs) or `trafilatura`/`requests` (web).
```python
# backend/ingestion/ingest.py
import os, pdfplumber

def load_and_chunk_pdfs(pdf_dir, chunk_size=500, overlap=50):
    chunks, buf = [], []
    def flush():
        if buf:
            text = " ".join(buf).strip()
            if text:
                chunks.append(text)
            buf.clear()
    for name in os.listdir(pdf_dir):
        if not name.lower().endswith('.pdf'):  
            continue
        with pdfplumber.open(os.path.join(pdf_dir, name)) as pdf:
            for page in pdf.pages:
                t = (page.extract_text() or '').strip()
                if not t:
                    continue
                words = t.split()
                i = 0
                while i < len(words):
                    segment = words[i:i+chunk_size]
                    buf.append(" ".join(segment))
                    flush()
                    i += (chunk_size - overlap)
    return chunks
```
Persist chunks (e.g., JSONL in `data/processed/`).

### 5.3 NSAI Extraction: Convert Text to Structured JSON

Prompt an LLM (Gemini/OpenAI) to extract a canonical structure, e.g.:
```json
{
  "concept": "Billing",
  "sub_concept": "Insurance-Coverage",
  "explanation": "Insurance coverage determines which services are paid for...",
  "source": "https://example.com/faq/insurance",
  "media": [
    {"type": "image", "url": "https://example.com/img.png"}
  ]
}
```
Prompt template (from `docs/architecture.md`/`docs/pipeline.md`)
- Identify Domain → Concept → Sub-concept → Explanation
- Include validated sources and media if present
- Return as array of JSON objects

You may do this either:
- From Python (call LLM SDK, then parse JSON), or
- Inside MeTTa via Motto agents (see 5.7, 5.8 for integration patterns).

### 5.4 JSON → MeTTa Atoms

Construct MeTTa S-expressions for concepts, relations, and content.
```lisp
; Hierarchy
(has-concept Hospital-FAQ Billing)
(has-subconcept Billing Insurance-Coverage)

; Explanation entity + content
(: explanation-1 Explanation)
(has-content explanation-1 "Insurance coverage determines which services are paid...")
(has-explanation Insurance-Coverage explanation-1)

; Provenance
(has-source explanation-1 "https://example.com/faq/insurance")
```

### 5.5 Persist Knowledge in Atomspace

Using Python + Hyperon (
`from hyperon import MeTTa, E, S`
):
```python
# backend/metta/store.py
from hyperon import MeTTa, E, S

def build_space(name='&athena_kb'):
    metta = MeTTa()
    metta.run(f"!(bind! {name} (new-space))")
    return metta, name

def add_has_subconcept(metta, space, concept, subconcept):
    expr = E(S('has-subconcept'), S(concept), S(subconcept))
    metta.space().add_atom(expr)

# Example usage
# metta, space = build_space()
# add_has_subconcept(metta, space, 'Billing', 'Insurance-Coverage')
```
You can also `metta.run` MeTTa code strings directly to add atoms.

### 5.6 Querying (Graph RAG) with MeTTa

Turn user questions into MeTTa `match` queries (via LLM prompt or rules).

Examples (from `docs/architecture.md`):
```lisp
; Retrieve explanations tied to a sub-concept
!(match &athena_kb (has-explanation Insurance-Coverage $exp) $exp)

; Composite traversal: list all sub-concepts under Billing with their content
!(match &athena_kb
  (, (has-subconcept Billing $sub)
     (has-explanation $sub $exp_atom)
     (has-content $exp_atom $content))
  (Result $sub $content)
)
```

### 5.7 Answer Synthesis with LLM

Feed retrieved structured facts to an LLM to produce a fluent answer. Example prompt:
```
You are a helpful assistant. A user asked a question. Using only the provided facts, synthesize a clear, accurate answer. Include sources when relevant.

Facts:
---
Sub-concept: Insurance Coverage
Content: Insurance coverage determines which services are paid...
Source: https://example.com/faq/insurance
---
```

Using Metta Motto inside MeTTa (typical pattern):
```lisp
!(import! &self motto)

; Bind the LLM response to &llm_out (agent name depends on your setup)
!(bind! &llm_out
  ((gemini-agent)
   (system "You are a helpful assistant. Use only provided facts.")
   (user   "Facts: ...\nQuestion: ...\nAnswer:")))
```
Configure API keys as environment variables before running.

### 5.8 Explainability and Provenance

Model provenance explicitly in the Atomspace and return it to users:
```lisp
(has-source explanation-1 "https://example.com/faq/insurance")
(has-media  explanation-2 (Image "https://example.com/img/payment_diagram.png"))
```
When answering, include:
- Sources used
- Traversal path (which atoms matched)
- Confidence scores (if modeled)

### 5.9 Learning Loop and Continuous Improvement

- Log failed or low-confidence queries and user feedback
- Periodically re-run ingestion/extraction to update or correct facts
- Standardize entities to avoid duplicates (e.g., “copay”, “co-payment”)
- Human-in-the-loop for critical updates

---

## 6. Running the Project Locally

Minimal end-to-end smoke test
```powershell
# 1) Activate env and ensure packages installed
.\.venv\Scripts\activate

# 2) Place a couple of PDFs into data/raw/

# 3) Run ingestion to produce chunks (pseudo-command)
python -m backend.ingestion.ingest

# 4) Run extraction (LLM) to JSON (pseudo-command)
python -m backend.nsai.extract

# 5) Translate JSON → MeTTa and store atoms
python -m backend.metta.translate_and_store

# 6) Run a sample query via a small runner
python -m backend.query.run_sample
```
Adapt these module names to your actual code. See `docs/architecture.md` and `docs/pipeline.md` for detailed prompts and query patterns.

---

## 7. API and UI (Optional but Recommended)

- API: Build a `FastAPI` service with endpoints:
  - `POST /ingest` → enqueue new documents
  - `POST /query` → body: user question; returns answer + sources + trace
  - `GET /healthz` → health check

- UI: A simple chat interface (Streamlit or React) that:
  - Captures user questions
  - Displays final answers
  - Shows expandable sections for sources and reasoning path

---

## 8. Testing and Validation

- Unit tests for:
  - Chunking logic (boundary conditions on overlap, empty pages)
  - JSON schema validation from LLM extraction
  - Translation functions (JSON → MeTTa atoms)
  - Query functions (expected matches on a toy Atomspace)

- Integration tests:
  - Seed a small Atomspace with known atoms
  - Run representative queries and verify outputs and provenance

- Evaluation:
  - Accuracy against a labeled set of Q/A
  - Latency and throughput under load
  - Cost tracking (LLM tokens per pipeline stage)

---

## 9. Deployment

- Containerization:
  - Python backend + MeTTa runtime in one image
  - Optional separate worker for ingestion/extraction

- Configuration:
  - Environment variables for API keys and feature flags
  - Persistent storage/snapshots for Atomspace if needed

- Observability:
  - Structured logs for each stage (ingest, extract, translate, query, synthesize)
  - Tracing IDs to correlate an answer with its query and provenance

- Security & Compliance:
  - PII handling and redaction policies
  - Key management via secret stores (not checked into repo)

---

## 10. Troubleshooting

- No atoms returned by `match`:
  - Verify ingestion produced atoms in the intended space (e.g., `&athena_kb`)
  - Check for typos in symbols (`Insurance-Coverage` vs `InsuranceCoverage`)

- LLM extraction is noisy/inconsistent:
  - Strengthen few-shot examples
  - Add entity standardization and deduplication

- "Module motto not found" in MeTTa:
  - Ensure `pip install metta-motto` and restart the interpreter
  - Check API keys are present in environment

- Package name conflicts (`hyperon` vs `hyperon-experimental`):
  - Try the alternative package
  - If needed, build from source: https://github.com/trueagi-io/hyperon-experimental

---

## 11. Roadmap

- Distributed Atomspace for large-scale graphs
- Domain ontologies and type systems to enforce constraints
- Advanced Graph RAG policies (scoring, multi-hop selection)
- Active learning loop for continuous refinement
- Rich UI: subgraph visualization and interactive provenance trails

---

## 12. References

- `docs/problem_statement.md`
- `docs/architecture.md`
- `docs/pipeline.md`
- `metta_readme.md`
- `docs/Metta Language Mastery and Teaching_.txt`
- MeTTa Motto tutorial (LLM integration): https://metta-lang.dev/docs/learn/tutorials/metta-motto/metta-motto.html
- Hyperon / MeTTa (implementation): https://github.com/trueagi-io/hyperon-experimental

---

Notes
- Treat code snippets as templates. Adapt module paths and names to your codebase.
- Keep symbols consistent (case and hyphenation) to ensure `match` queries succeed.
- Store provenance with every explanation/content atom to enable explainability.

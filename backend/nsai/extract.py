import json
import os ,time
from pathlib import Path
from typing import List, Dict, Any

from pydantic import ValidationError
from .schema import DocumentExtraction, ExtractionBatchRecord
from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BATCHES_PATH = PROJECT_ROOT / "data" / "processed" / "doc_batches.jsonl"
EXTRACTED_PATH = PROJECT_ROOT / "data" / "processed" / "extracted.jsonl"
PROMPT_TEMPLATE_PATH = PROJECT_ROOT / "backend" / "nsai" / "prompts" / "extract_prompt.txt"

# Choose provider via env var, default to Gemini
PROVIDER = os.getenv("NSAI_PROVIDER", "gemini").lower()


def _load_prompt_template() -> str:
    with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _call_llm(prompt: str) -> str:
    """Provider-agnostic shim. Returns raw text (expected to be JSON)."""
    if PROVIDER == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set. Configure environment before running extractor.")
        # Lazy import to avoid hard dependency when not used
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content(prompt)
        # Prefer resp.text, fallback to candidates content aggregation
        if hasattr(resp, "text") and resp.text:
            return resp.text
        # Fallback extraction
        parts = []
        for cand in getattr(resp, "candidates", []) or []:
            content = getattr(cand, "content", None)
            if not content:
                continue
            for p in getattr(content, "parts", []) or []:
                t = getattr(p, "text", None)
                if t:
                    parts.append(t)
        return "\n".join(parts)
    elif PROVIDER == "openai":
        # TODO: implement OpenAI provider integration (gpt-4o or similar)
        raise NotImplementedError("OpenAI call not implemented. Provide SDK integration.")
    else:
        raise RuntimeError(f"Unsupported provider: {PROVIDER}")


def _coerce_list(obj: Any) -> List[Dict[str, Any]]:
    """Ensure response is a list of JSON objects."""
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        return [obj]
    raise ValueError("LLM did not return a JSON object/array")


def _merge_backcompat_into_evidence(sc: Dict[str, Any]) -> None:
    """Map back-compat fields (sources/links/media/tables) into evidence if present."""
    # Ensure evidence block exists
    ev = sc.get("evidence") or {}
    # Back-compat lists
    for key in ("sources", "links", "tables"):
        vals = sc.get(key)
        if vals:
            arr = list(dict.fromkeys(vals))  # dedupe
            ev[key] = sorted(set(ev.get(key, []) + arr)) if ev.get(key) else arr
    # Media requires mapping into list of objects if provided in back-compat
    if sc.get("media") and not ev.get("media"):
        ev["media"] = sc["media"]
    sc["evidence"] = ev


def _populate_sources_links_if_empty(sc: Dict[str, Any], links_found: List[str]) -> None:
    ev = sc.get("evidence") or {}
    # If both sources and links empty, populate with links_found
    if not ev.get("sources") and not ev.get("links") and links_found:
        # Prefer to treat as sources (provenance) first
        ev["sources"] = links_found[:5]
    elif not ev.get("sources") and links_found:
        ev["sources"] = links_found[:5]
    elif not ev.get("links") and links_found:
        ev["links"] = links_found[:5]
    sc["evidence"] = ev


def _postprocess_payload(payload: Dict[str, Any], doc_id: str, links_found: List[str]) -> Dict[str, Any]:
    # Ensure top-level metadata carries doc_id
    metadata = payload.get("metadata") or {}
    metadata.setdefault("doc_id", doc_id)
    payload["metadata"] = metadata

    for concept in payload.get("concepts", []) or []:
        # Concept metadata
        cm = concept.get("metadata") or {}
        cm.setdefault("doc_id", doc_id)
        concept["metadata"] = cm
        # Sub-concepts
        for sc in concept.get("sub_concepts", []) or []:
            # Subconcept metadata
            sm = sc.get("metadata") or {}
            sm.setdefault("doc_id", doc_id)
            sc["metadata"] = sm
            # Back-compat merge
            _merge_backcompat_into_evidence(sc)
            # Populate evidence if empty using context links
            _populate_sources_links_if_empty(sc, links_found)
    return payload


def run() -> None:
    if not BATCHES_PATH.exists():
        raise FileNotFoundError(f"Batches not found at {BATCHES_PATH}. Run aggregate_docs first.")

    template = _load_prompt_template()

    EXTRACTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BATCHES_PATH, "r", encoding="utf-8") as f_in, open(EXTRACTED_PATH, "w", encoding="utf-8") as f_out:
        for line in f_in:
            rec = json.loads(line)
            doc_id = rec["doc_id"]
            base_prompt = rec["nsai_extraction_prompt_doc"]
            examples = rec.get("metta_examples_doc", "")
            prompt = base_prompt
            if examples:
                prompt = f"{base_prompt}\n\nEXAMPLES (Heuristic, optional):\n{examples}"

            # Call LLM
            raw = _call_llm(prompt)
            print(raw)
            if raw.startswith("```json"):
                raw = raw.replace("```json", "", 1)
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
            # Parse
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as e:
                print(f"[NSAI] JSON parse failed for doc {doc_id}: {e}")
                continue

            # Validate & write
            try:
                objs = _coerce_list(parsed)
                links_found = rec.get("links_found", []) or []
                for obj in objs:
                    post = _postprocess_payload(obj, doc_id, links_found)
                    model = DocumentExtraction(**post)
                    out_rec = ExtractionBatchRecord(doc_id=doc_id, payload=model)
                    f_out.write(out_rec.model_dump_json() + "\n")
            except ValidationError as ve:
                print(f"[NSAI] Validation error for doc {doc_id}: {ve}")
                continue

    print(f"Wrote extractions to {EXTRACTED_PATH}")


if __name__ == "__main__":
    run()

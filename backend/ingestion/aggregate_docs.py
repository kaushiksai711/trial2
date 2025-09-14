import json
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "metta_chunks.jsonl"
BATCHES_PATH = PROJECT_ROOT / "data" / "processed" / "doc_batches.jsonl"
PROMPT_TEMPLATE_PATH = PROJECT_ROOT / "backend" / "nsai" / "prompts" / "extract_prompt.txt"

# Limits to keep doc-level batches within token budgets
MAX_CHUNKS_PER_DOC = 80       # use bigger batches to reduce request count
MAX_CHARS_PER_CHUNK = 1600    # ~400 tokens per chunk
MAX_CANDIDATES = 40           # still manageable
MAX_RULES = 25
MAX_DEFINITIONS = 20


def _load_prompt_template() -> str:
    try:
        with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback minimal template if file not present
        return (
            "You are an expert extractor. From the following document text, extract JSON objects with fields: "
            "concept, sub_concept, explanation, source (optional), media (optional list).\n"
            "Return ONLY JSON array.\n\nDOC: {DOC_ID}\nTEXT:\n{TEXT_BLOCK}\n"
        )


def _truncate(s: str, max_chars: int) -> str:
    return s if len(s) <= max_chars else (s[: max_chars - 3] + "...")


def _collate_doc_examples(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Aggregate heuristic hints for doc-level few-shot
    candidate_atoms: List[str] = []
    candidate_rules: List[str] = []
    definitions: List[Dict[str, str]] = []

    for ch in chunks:
        hints = ch.get("metta_hints", {})
        candidate_atoms.extend(hints.get("candidate_atoms", []))
        candidate_rules.extend(hints.get("candidate_rules", []))
        definitions.extend(hints.get("definitions", []))

    # Deduplicate while preserving order
    def dedup(seq):
        seen = set()
        out = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    candidate_atoms = dedup(candidate_atoms)[:MAX_CANDIDATES]
    candidate_rules = dedup(candidate_rules)[:MAX_RULES]
    definitions = definitions[:MAX_DEFINITIONS]

    examples_lines = ["; Candidate facts:"] + [f"  {a}" for a in candidate_atoms]
    if candidate_rules:
        examples_lines += ["; Candidate rules:"] + [f"  {r}" for r in candidate_rules]
    if definitions:
        examples_lines += ["; Definitions:"] + [
            f"  (: {d.get('term','Term')} Concept) ; {d.get('definition','...')}" for d in definitions
        ]
    return {
        "candidate_atoms": candidate_atoms,
        "candidate_rules": candidate_rules,
        "definitions": definitions,
        "examples_text": "\n".join(examples_lines),
    }


def build_batches() -> None:
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"Chunks not found at {CHUNKS_PATH}. Run metta_chunker first.")

    template = _load_prompt_template()

    # Group chunks by doc_id
    by_doc: Dict[str, List[Dict[str, Any]]] = {}
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            meta = obj.get("metadata", {})
            doc_id = meta.get("doc_id") or (meta.get("source") or "unknown").split(".")[0]
            by_doc.setdefault(doc_id, []).append(obj)

    with open(BATCHES_PATH, "w", encoding="utf-8") as out:
        for doc_id, chunks in by_doc.items():
            # Sort chunks by page then chunk_index for stable ordering
            chunks.sort(key=lambda c: ((c.get("metadata", {}).get("page") or 0), c.get("metadata", {}).get("chunk_index", 0)))

            total = len(chunks)
            if total == 0:
                continue

            total_batches = (total + MAX_CHUNKS_PER_DOC - 1) // MAX_CHUNKS_PER_DOC
            for b_idx, start in enumerate(range(0, total, MAX_CHUNKS_PER_DOC), start=1):
                batch = chunks[start : start + MAX_CHUNKS_PER_DOC]
                text_block_parts: List[str] = []
                included_indices: List[int] = []
                for ch in batch:
                    txt = ch.get("text", "")
                    text_block_parts.append(_truncate(txt, MAX_CHARS_PER_CHUNK))
                    included_indices.append(ch.get("metadata", {}).get("chunk_index", -1))
                text_block = "\n\n".join(text_block_parts)

                # Build examples per-batch
                examples = _collate_doc_examples(batch)

                # Collect deduped links from this batch
                links_found_set = []
                seen = set()
                for ch in batch:
                    for u in ch.get("metadata", {}).get("links", []) or []:
                        if u not in seen:
                            seen.add(u)
                            links_found_set.append(u)

                # Fill template and append context sections
                prompt_text = template.replace("{DOC_ID}", doc_id).replace("{TEXT_BLOCK}", text_block)
                prompt_text += f"\n\nBatch info: This is batch {b_idx} of {total_batches} for document {doc_id}.\n"
                prompt_text += (
                    "Include numeric page/chunk references only under evidence.citations. "
                    "Evidence.sources must be valid URLs when present.\n"
                )
                prompt_text += f"Chunks included in this batch: {included_indices}\n"
                if links_found_set:
                    prompt_text += "\nContext: Links found in document (use as sources/links when applicable):\n" + "\n".join(
                        f"- {u}" for u in links_found_set
                    )

                record = {
                    "doc_id": doc_id,
                    "batch_index": b_idx,
                    "total_batches": total_batches,
                    "nsai_extraction_prompt_doc": prompt_text,
                    "metta_examples_doc": examples.get("examples_text", ""),
                    "chunks_included": included_indices,
                    "source_files": list({c.get("metadata", {}).get("source") for c in chunks if c.get("metadata", {}).get("source")} ),
                    "links_found": links_found_set,
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote document batches to {BATCHES_PATH}")


if __name__ == "__main__":
    build_batches()

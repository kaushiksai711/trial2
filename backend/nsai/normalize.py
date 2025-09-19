import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "extracted.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "extracted_normalized.jsonl"
CANON_MAP_PATH = PROJECT_ROOT / "data" / "processed" / "canonical_map.json"

TYPE_KEYWORDS = {
    "definition": "Definition",
    "terminology": "Definition",
    "framework": "Framework",
    "dataset": "Dataset",
    "metric": "Metric",
    "phase": "Phase",
}


def strip_parentheticals(name: str) -> Tuple[str, List[str]]:
    """Process parenthetical segments, return cleaned name + list of tags found."""
    tags: List[str] = []
    
    def process_match(m):
        inner = m.group(1).strip()
        if not inner:
            return ""
            
        # Check if this looks like an acronym (all caps or camel case with dots)
        is_acronym = (inner.isupper() or 
                     (len(inner) <= 5 and any(c.isupper() for c in inner)) or
                     bool(re.match(r'^[A-Z0-9]+(?:\.[A-Z0-9]+)*$', inner)))
        
        if is_acronym:
            # For acronyms, keep them in the name but clean them up
            clean_acronym = inner.strip('.')
            tags.append(clean_acronym)
            return f" ({clean_acronym})"
        else:
            # For other content, extract as tag but keep in the name
            tags.append(inner)
            return f" ({inner})"
    
    # Process all parentheticals
    processed_name = re.sub(r"\s*\(([^)]+)\)", process_match, name).strip()
    
    # Clean up any extra spaces
    processed_name = re.sub(r'\s+', ' ', processed_name).strip()
    
    return processed_name, tags


def detect_type_from_tags(tags: List[str]) -> str | None:
    """Detect concept type from tags, with special handling for acronyms."""
    if not tags:
        return None
        
    # First pass: look for explicit type indicators
    for t in tags:
        low = t.lower()
        for kw, type_name in TYPE_KEYWORDS.items():
            if kw in low:
                return type_name
    
    # Second pass: check if any tag looks like a type
    type_like = next((t for t in tags if t.lower() in [v.lower() for v in TYPE_KEYWORDS.values()]), None)
    if type_like:
        return type_like
        
    return None


def to_canonical(name: str) -> Tuple[str, str]:
    """Return (canonical_name, symbol_name) where canonical_name is Title Case and symbol uses hyphens.
    Example: 'insurance coverage' -> ('Insurance Coverage', 'Insurance-Coverage')
    """
    # Normalize unicode/apostrophes/spaces
    s = re.sub(r"[_\-/]+", " ", name)
    s = re.sub(r"\s+", " ", s).strip()
    # Title Case words, keep short words lowercase unless first
    words = s.split(" ")
    out_words: List[str] = []
    for i, w in enumerate(words):
        w_clean = re.sub(r"[^A-Za-z0-9]+", "", w)
        if not w_clean:
            continue
        if i == 0 or len(w_clean) > 3:
            out_words.append(w_clean.capitalize())
        else:
            out_words.append(w_clean.lower())
    canonical = " ".join(out_words).strip() or name.strip()
    symbol = "-".join(out_words)
    return canonical, symbol


def normalize_record(rec: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, str]], List[Dict[str, str]]]:
    """Normalize one ExtractionBatchRecord payload.
    Returns: (normalized_rec, concept_mappings, subconcept_mappings)
    """
    doc_id = rec.get("doc_id") or rec.get("payload", {}).get("metadata", {}).get("doc_id")
    payload = rec.get("payload", {})
    if not payload:
        return rec, [], []

    concept_maps: List[Dict[str, str]] = []
    subconcept_maps: List[Dict[str, str]] = []

    # Ensure top-level metadata emits doc_id
    payload.setdefault("metadata", {})
    payload["metadata"].setdefault("doc_id", doc_id)

    for concept in payload.get("concepts", []) or []:
        orig_name = concept.get("name", "")
        stripped, tags = strip_parentheticals(orig_name)
        ctype = concept.get("concept_type") or detect_type_from_tags(tags)
        canon, symbol = to_canonical(stripped)

        concept.setdefault("metadata", {})
        concept["metadata"].setdefault("doc_id", doc_id)
        concept["metadata"]["original_name"] = orig_name
        concept["name"] = canon
        if ctype:
            concept["concept_type"] = ctype

        concept_maps.append({
            "doc_id": str(doc_id),
            "original": orig_name,
            "canonical": canon,
            "symbol": symbol,
            "type": ctype or "",
        })

        for sc in concept.get("sub_concepts", []) or []:
            sc_orig = sc.get("name", "")
            sc_stripped, sc_tags = strip_parentheticals(sc_orig)
            sc_type = sc.get("sub_type") or detect_type_from_tags(sc_tags)
            sc_canon, sc_symbol = to_canonical(sc_stripped)

            sc.setdefault("metadata", {})
            sc["metadata"].setdefault("doc_id", doc_id)
            sc["metadata"]["original_name"] = sc_orig
            sc["name"] = sc_canon
            if sc_type:
                sc["sub_type"] = sc_type

            subconcept_maps.append({
                "doc_id": str(doc_id),
                "original": sc_orig,
                "canonical": sc_canon,
                "symbol": sc_symbol,
                "type": sc_type or "",
                "parent_concept": canon,
            })

    rec["payload"] = payload
    return rec, concept_maps, subconcept_maps


def run() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input not found: {INPUT_PATH}. Run nsai.extract first.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_c_maps: List[Dict[str, str]] = []
    all_sc_maps: List[Dict[str, str]] = []

    with open(INPUT_PATH, "r", encoding="utf-8") as f_in, \
         open(OUTPUT_PATH, "w", encoding="utf-8") as f_out:
        for line in f_in:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            norm, c_map, sc_map = normalize_record(rec)
            f_out.write(json.dumps(norm, ensure_ascii=False) + "\n")
            all_c_maps.extend(c_map)
            all_sc_maps.extend(sc_map)

    # Emit canonical map
    with open(CANON_MAP_PATH, "w", encoding="utf-8") as f_map:
        out = {
            "concepts": all_c_maps,
            "sub_concepts": all_sc_maps,
        }
        json.dump(out, f_map, ensure_ascii=False, indent=2)

    print(f"Wrote normalized JSONL to {OUTPUT_PATH}")
    print(f"Wrote canonical map to {CANON_MAP_PATH}")


if __name__ == "__main__":
    run()

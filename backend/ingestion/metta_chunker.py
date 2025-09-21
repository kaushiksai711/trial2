import os
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# LangChain imports (align with existing style in ingest.py)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    TextLoader,
)


# Optional semantic chunker (created lazily, fallback to structural if not available)
try:
    from langchain_experimental.text_splitter import SemanticChunker  # type: ignore
    from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore
except Exception:  # pragma: no cover
    SemanticChunker = None  # type: ignore
    HuggingFaceEmbeddings = None  # type: ignore

# NLP
import spacy


def _load_spacy() -> "spacy.language.Language":
    """Load spaCy English model, fallback to blank pipeline with sentencizer."""
    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        nlp = spacy.blank("en")
        if "sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("sentencizer")
        return nlp


def _to_symbol(text: str) -> str:
    """Convert arbitrary text to a MeTTa-friendly symbol (no spaces/punct)."""
    # Keep alphanum and underscores, replace spaces with '_', strip quotes
    cleaned = re.sub(r"[^A-Za-z0-9_\- ]+", "", text).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    # Avoid starting with digits in symbols by prefixing 'S_'
    if cleaned and cleaned[0].isdigit():
        cleaned = f"S_{cleaned}"
    return cleaned or "Unknown"


class MeTTaOptimizedChunker:
    """
    MeTTa-aware hybrid chunker that aligns text boundaries with concept units
    suitable for Atomspace extraction (facts, definitions, rules).

    - Semantic-first (if OpenAI embeddings available), fallback to structural
    - Preserves definitional and rule-like statements
    - Adds MeTTa-oriented prompts and lightweight extraction hints
    """

    def __init__(
        self,
        input_dir: Path,
        output_file: Path,
        concept_chunk_size: int = 1200,
        concept_overlap: int = 100,
        semantic_threshold_percentile: int = 95,
        enable_semantic: bool = True,
    ) -> None:
        self.input_dir = Path(input_dir)
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        self.concept_chunk_size = concept_chunk_size
        self.concept_overlap = concept_overlap
        self.semantic_threshold_percentile = semantic_threshold_percentile
        self.enable_semantic = enable_semantic

        self.nlp = _load_spacy()
        self.semantic_chunker = self._init_semantic_chunker()

        # Structural splitter tuned for conceptual coherence
        self.structural_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.concept_chunk_size,
            chunk_overlap=self.concept_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
            add_start_index=False,
        )

    def _init_semantic_chunker(self):
        if not self.enable_semantic:
            print("[MeTTaChunker] Semantic chunking disabled; using structural splitting only.")
            return None
        if SemanticChunker is None or HuggingFaceEmbeddings is None:
            print("[MeTTaChunker] SemanticChunker not available; install langchain-experimental and langchain-community.")
            return None
        try:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            return SemanticChunker(
                embeddings,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=self.semantic_threshold_percentile,
            )
        except Exception as e:  # pragma: no cover
            print(f"[MeTTaChunker] Failed to initialize SemanticChunker: {e}")
            return None

    # ---------- Public API ----------

    def process_all(self) -> None:
        files = []
        for pattern in ["*.pdf", "*.md", "*.markdown", "*.txt"]:
            files.extend(self.input_dir.glob(pattern))
        if not files:
            print(f"[MeTTaChunker] No supported files found in {self.input_dir}")
            return

        print(f"[MeTTaChunker] Found {len(files)} files to process...")
        total_chunks = 0
        with open(self.output_file, "w", encoding="utf-8") as f_out:
            for file_path in files:
                chunks = self._process_file(file_path)
                for rec in chunks:
                    f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                total_chunks += len(chunks)
                print(f"  - {file_path.name}: {len(chunks)} chunks")

        print(f"[MeTTaChunker] Done. Wrote {total_chunks} chunks to {self.output_file}")

    # ---------- File routing ----------

    def _process_file(self, file_path: Path) -> List[Dict]:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return self._process_pdf(file_path)
        if ext in [".md", ".markdown"]:
            return self._process_markdown(file_path)
        if ext == ".txt":
            return self._process_text(file_path)
        print(f"[MeTTaChunker] Skipping unsupported file: {file_path}")
        return []

    # ---------- Processors ----------

    def _normalize_text(self, text: str) -> str:
        """Normalize whitespace and clean up text."""
        if not text:
            return ""
        # Replace all whitespace sequences with single space
        text = re.sub(r'\s+', ' ', text)
        # Clean up spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([(])\s+', r'\1', text)  # Remove space after opening parenthesis
        text = re.sub(r'\s+([)])', r'\1', text)  # Remove space before closing parenthesis
        text = re.sub(r'\s+', ' ', text)  # Final pass for any remaining multiple spaces
        return text.strip()

    def _process_pdf(self, file_path: Path) -> List[Dict]:
        try:
            loader = PyPDFLoader(str(file_path))
            pages = loader.load()
        except Exception as e:
            print(f"[MeTTaChunker] Error loading PDF {file_path.name}: {e}")
            return []

        out: List[Dict] = []
        for i, page in enumerate(pages):
            page_text = self._normalize_text(page.page_content or "")
            chunks = self._split_coherent(page_text)
            for j, text in enumerate(chunks):
                record = self._enrich_record(
                    text=text,
                    source=file_path.name,
                    page=i + 1,
                    section_path=None,
                    chunk_index=j,
                    total_chunks=len(chunks),
                )
                out.append(record)
        return out

    def _process_markdown(self, file_path: Path) -> List[Dict]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                markdown_text = self._normalize_text(f.read())
        except Exception as e:
            print(f"[MeTTaChunker] Error reading MD {file_path.name}: {e}")
            return []

        # Header-aware pass to retain section hierarchy
        header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
        )
        docs = header_splitter.split_text(markdown_text)

        out: List[Dict] = []
        for d in docs:
            # Build a section path like H1 > H2 > H3
            h1 = d.metadata.get("Header 1")
            h2 = d.metadata.get("Header 2")
            h3 = d.metadata.get("Header 3")
            section_path = " > ".join([h for h in [h1, h2, h3] if h]) or None
            # Now split the body coherently
            for idx, text in enumerate(self._split_coherent(d.page_content or "")):
                record = self._enrich_record(
                    text=text,
                    source=file_path.name,
                    page=None,
                    section_path=section_path,
                    chunk_index=idx,
                    total_chunks=0,
                )
                out.append(record)
        return out

    def _process_text(self, file_path: Path) -> List[Dict]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = self._normalize_text(f.read())
        except Exception as e:
            print(f"[MeTTaChunker] Error reading TXT {file_path.name}: {e}")
            return []

        out: List[Dict] = []
        chunks = self._split_coherent(text)
        for j, ch in enumerate(chunks):
            record = self._enrich_record(
                text=ch,
                source=file_path.name,
                page=None,
                section_path=None,
                chunk_index=j,
                total_chunks=len(chunks),
            )
            out.append(record)
        return out

    # ---------- Chunking logic ----------

    def _split_coherent(self, text: str) -> List[str]:
        text = text.strip()
        if not text:
            return []

        # Pre-pass: keep definition and rule cues together by expanding window around sentences with triggers
        sentences = self._sentences(text)
        if not sentences:
            return self._split_fallback(text)

        merged_blocks: List[str] = []
        buf: List[str] = []
        for sent in sentences:
            buf.append(sent)
            # Trigger cues to force boundary on next step
            if self._has_rule_or_def_cue(sent):
                # Keep current buffer but allow size control later
                pass
            # Size-based flush to avoid overgrowth
            if sum(len(s) for s in buf) >= self.concept_chunk_size * 1.2:
                merged_blocks.append(" ".join(buf).strip())
                buf = []
        if buf:
            merged_blocks.append(" ".join(buf).strip())

        # Second pass: semantic-first splitting within each block
        final_chunks: List[str] = []
        for block in merged_blocks:
            block = block.strip()
            if not block:
                continue
            parts = self._split_semantic_first(block)
            # Enforce max size by structural splitter as needed
            for p in parts:
                if len(p) > self.concept_chunk_size * 1.5:
                    final_chunks.extend(self.structural_splitter.split_text(p))
                else:
                    final_chunks.append(p)

        return [c.strip() for c in final_chunks if len(c.strip()) >= 100]  # drop tiny fragments

    def _split_semantic_first(self, text: str) -> List[str]:
        if self.semantic_chunker is not None:
            try:
                return self.semantic_chunker.split_text(text)
            except Exception as e:
                print(f"[MeTTaChunker] Semantic split failed; fallback to structural: {e}")
        return self._split_fallback(text)

    def _split_fallback(self, text: str) -> List[str]:
        return self.structural_splitter.split_text(text)

    def _sentences(self, text: str) -> List[str]:
        doc = self.nlp(text)
        if hasattr(doc, "sents"):
            return [s.text.strip() for s in doc.sents if s.text and s.text.strip()]
        # naive fallback
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

    def _has_rule_or_def_cue(self, sentence: str) -> bool:
        s = sentence.lower()
        return any(
            cue in s
            for cue in [" if ", " then ", " implies ", " therefore ", " defined as ", " refers to ", " means ", " is "]
        )

    # ---------- Enrichment ----------

    def _enrich_record(
        self,
        text: str,
        source: str,
        page: Optional[int],
        section_path: Optional[str],
        chunk_index: int,
        total_chunks: int,
    ) -> Dict:
        doc = self.nlp(text)
        definitions = self._extract_definitions(text)
        rules = self._extract_rules(text)
        triples = self._extract_triples(doc)
        is_a_facts = self._extract_is_a(text)
        links = self._extract_links(text)
        media_links = self._extract_media_links(links)
        has_media_mentions = self._has_media_mentions(text)
        has_table_hints = self._has_table_hints(text)
        # Derive a stable document id from source filename
        doc_id = Path(source).stem

        candidate_atoms: List[str] = []
        # Convert triples to s-expr facts: (predicate Subject Object)
        for subj, pred, obj in triples:
            subj_sym = _to_symbol(subj)
            pred_sym = _to_symbol(pred.lower())
            obj_sym = _to_symbol(obj)
            if pred_sym and subj_sym and obj_sym:
                candidate_atoms.append(f"({pred_sym} {subj_sym} {obj_sym})")

        # is-a patterns to either (: X Y) or (Y X)
        for subj, obj in is_a_facts:
            subj_sym, obj_sym = _to_symbol(subj), _to_symbol(obj)
            candidate_atoms.append(f"(: {subj_sym} {obj_sym})")
            candidate_atoms.append(f"({obj_sym} {subj_sym})")

        # Rule placeholders (let LLM refine patterns)
        candidate_rules: List[str] = []
        for cond, cons in rules:
            candidate_rules.append(f"(implies ;; condition: {cond!r} ;; consequence: {cons!r})")

        metta_prompt = self._metta_prompt(text, candidate_atoms, definitions, rules)

        record = {
            "text": text,
            "metadata": {
                "doc_id": doc_id,
                "source": source,
                "page": page,
                "section_path": section_path,
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "word_count": len(text.split()),
                "links": links,
                "media_links": media_links,
                "has_media_mentions": has_media_mentions,
                "has_table_hints": has_table_hints,
                "me_tt_a": {
                    "definitions": definitions,
                    "rules_text": rules,
                    "candidate_atoms": candidate_atoms,
                    "candidate_rules": candidate_rules,
                },
            },
            # Backward-compatible field (kept), but prefer using 'metta_hints' at doc-level batching
            "metta_extraction_prompt": metta_prompt,
            # New non-breaking field for doc-level batching consumption
            "metta_hints": {
                "candidate_atoms": candidate_atoms,
                "candidate_rules": candidate_rules,
                "definitions": definitions,
                "triples": triples,
                "is_a_pairs": is_a_facts,
            },
        }
        return record

    def _extract_definitions(self, text: str) -> List[Dict]:
        patterns = [
            r"(\b[A-Z][\w\- ]{0,60}?)\s+(?:is|means|refers to|defined as)\s+([^\.\n]+\.)",
            r"(\b[A-Z][\w\- ]{0,60}?):\s+([^\.\n]+)",
        ]
        defs: List[Dict] = []
        for pat in patterns:
            for m in re.finditer(pat, text, flags=re.IGNORECASE):
                term = m.group(1).strip()
                definition = m.group(2).strip()
                if term and definition:
                    defs.append({"term": term, "definition": definition, "confidence": 0.75})
        return defs

    def _extract_rules(self, text: str) -> List[Tuple[str, str]]:
        rules: List[Tuple[str, str]] = []
        # if X then Y
        for m in re.finditer(r"\bif\s+([^\.;\n]+?)\s+then\s+([^\.;\n]+)", text, flags=re.IGNORECASE):
            rules.append((m.group(1).strip(), m.group(2).strip()))
        # X implies Y
        for m in re.finditer(r"([^\.;\n]+?)\s+implies\s+([^\.;\n]+)", text, flags=re.IGNORECASE):
            rules.append((m.group(1).strip(), m.group(2).strip()))
        return rules

    def _extract_is_a(self, text: str) -> List[Tuple[str, str]]:
        pairs: List[Tuple[str, str]] = []
        for m in re.finditer(r"\b([A-Z][A-Za-z0-9_\- ]{1,60})\s+is\s+(?:an?\s+|the\s+)?([A-Z][A-Za-z0-9_\- ]{1,60})\b", text):
            pairs.append((m.group(1).strip(), m.group(2).strip()))
        return pairs

    def _extract_triples(self, doc) -> List[Tuple[str, str, str]]:
        triples: List[Tuple[str, str, str]] = []
        try:
            for token in doc:
                if token.pos_ in ("VERB",) or token.dep_ == "ROOT":
                    subs = [c for c in token.children if c.dep_ in ("nsubj", "nsubjpass")]
                    objs = [c for c in token.children if c.dep_ in ("dobj", "attr", "oprd")]
                    for s in subs:
                        for o in objs:
                            triples.append((s.text, token.lemma_.lower(), o.text))
        except Exception:
            pass
        return triples

    def _extract_links(self, text: str) -> List[str]:
        pattern = r"https?://[^\s)\"]+"
        links = re.findall(pattern, text)
        # Deduplicate while preserving order
        seen = set()
        out: List[str] = []
        for u in links:
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out

    def _extract_media_links(self, links: List[str]) -> List[str]:
        media_ext = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp4", ".mov", ".avi")
        return [u for u in links if any(u.lower().endswith(ext) for ext in media_ext)]

    def _has_media_mentions(self, text: str) -> bool:
        return bool(re.search(r"\b(figure|image|diagram|video|media)\b", text, flags=re.IGNORECASE))

    def _has_table_hints(self, text: str) -> bool:
        # Markdown tables or textual mentions of tables
        if re.search(r"^\s*\|.*\|\s*$", text, flags=re.MULTILINE):
            return True
        if re.search(r"\btable\s+\d+\b", text, flags=re.IGNORECASE):
            return True
        # Heuristic: lines with multiple 2+ spaces may indicate columns
        lines = text.splitlines()
        dense_cols = sum(1 for ln in lines if re.search(r"\S+\s{2,}\S+\s{2,}\S+", ln))
        return dense_cols >= 2

    def _metta_prompt(
        self,
        chunk_text: str,
        candidate_atoms: List[str],
        definitions: List[Dict],
        rules_text: List[Tuple[str, str]],
    ) -> str:
        sample_atoms = "\n".join(f"  - {a}" for a in candidate_atoms[:6]) or "  - (relation Subject Object)"
        sample_defs = "\n".join(
            f"  - (: {_to_symbol(d['term'])} Concept) ; Definition: {d['definition']}" for d in definitions[:4]
        ) or "  - (: Term Concept) ; Definition: ..."
        sample_rules = (
            "\n".join(f"  - (implies ;; if: {c} ;; then: {e})" for c, e in rules_text[:4])
            or "  - (implies (P $x) (Q $x))"
        )

        return (
            "Convert the following TEXT into canonical MeTTa atoms for Atomspace.\n\n"
            "Guidelines:\n"
            "- Facts as S-expressions: (relation arg1 arg2 ...)\n"
            "- Type membership as: (: Symbol Type) and/or (Type Symbol)\n"
            "- Rules as: (implies (pattern) (consequence)) using variables like $x where appropriate\n"
            "- Definitions may be captured as: (defined-as Symbol \"text\")\n"
            "- Prefer lower-case relations and CamelCase/underscored symbols. Avoid spaces in symbols.\n\n"
            f"TEXT (first 700 chars):\n{chunk_text[:700]}\n\n"
            "Helpful candidates (heuristic):\n"
            f"Facts:\n{sample_atoms}\n"
            f"Type/Definition hints:\n{sample_defs}\n"
            f"Rule hints:\n{sample_rules}\n"
        )


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    input_dir = project_root / "data" / "raw"
    output_file = project_root / "data" / "processed" / "metta_chunks.jsonl"

    chunker = MeTTaOptimizedChunker(
        input_dir=input_dir,
        output_file=output_file,
        concept_chunk_size=1200,
        concept_overlap=100,
        semantic_threshold_percentile=95,
        enable_semantic=True,
    )
    chunker.process_all()


if __name__ == "__main__":
    main()

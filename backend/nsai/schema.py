from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class MediaItem(BaseModel):
    type: str = Field(..., description="media type, e.g., image, video")
    url: HttpUrl


class Evidence(BaseModel):
    sources: Optional[List[HttpUrl]] = None  # provenance / citations
    media: Optional[List[MediaItem]] = None  # non-text evidence
    links: Optional[List[HttpUrl]] = None    # related web references
    tables: Optional[List[str]] = None       # serialized table text
    citations: Optional[List[str | int]] = None  # numeric page/chunk refs or textual notes


class Relation(BaseModel):
    type: str                                 # e.g., causes | mitigates | leads-to | part-of | related-to
    target: str                               # target node name
    note: Optional[str] = None
    confidence: Optional[float] = None


class CrossReference(BaseModel):
    target: str                               # other node name
    target_type: Optional[str] = None         # Concept | SubConcept
    note: Optional[str] = None


class Metadata(BaseModel):
    doc_id: Optional[str] = None
    author: Optional[str] = None
    provenance: Optional[str] = None          # free-form provenance string
    original_name: Optional[str] = None       # populated by normalizer


class Assertion(BaseModel):
    text: str
    evidence: Optional[Evidence] = None
    cross_references: Optional[List[CrossReference]] = None


class SubConcept(BaseModel):
    name: str
    explanation: Optional[str] = None
    # Backward-compatible fields (may be populated by extractor or post-pass)
    sources: Optional[List[HttpUrl]] = None
    media: Optional[List[MediaItem]] = None
    links: Optional[List[HttpUrl]] = None
    tables: Optional[List[str]] = None  # optional serialized table text
    # New structured fields
    sub_type: Optional[str] = None
    assertions: Optional[List[Assertion]] = None
    evidence: Optional[Evidence] = None
    cross_references: Optional[List[CrossReference]] = None
    related_concepts: Optional[List[str]] = None
    relations: Optional[List[Relation]] = None
    metadata: Optional[Metadata] = None


class Concept(BaseModel):
    name: str
    concept_type: Optional[str] = None        # optional typing (Definition | Framework | Dataset | Metric | Phase | ...)
    related_concepts: Optional[List[str]] = None
    relations: Optional[List[Relation]] = None
    metadata: Optional[Metadata] = None
    sub_concepts: List[SubConcept] = Field(default_factory=list)


class DocumentExtraction(BaseModel):
    domain: Optional[str] = None
    concepts: List[Concept] = Field(default_factory=list)
    metadata: Optional[Metadata] = None


class ExtractionBatchRecord(BaseModel):
    doc_id: str
    payload: DocumentExtraction
    batch_index: Optional[int] = None
    total_batches: Optional[int] = None

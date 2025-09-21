# QueryVerse Pipeline Documentation

## Overview
This document explains the current state of the QueryVerse document processing pipeline, which transforms raw documents into structured knowledge using a multi-stage process.

## Pipeline Stages

### 1. Document Ingestion & Chunking
**Entry Point**: `backend/ingestion/__main__.py`  
**Main Components**:
- `MeTTaOptimizedChunker` (`metta_chunker.py`)
- `DocumentIngestor` (`ingest.py`)

**Process**:
1. Accepts various document formats (PDF, text, markdown)
2. Splits content into coherent chunks with overlap
3. Enriches chunks with metadata and structural information
4. Outputs to `data/processed/metta_chunks.jsonl`

### 2. Batch Creation
**File**: `backend/ingestion/aggregate_docs.py`  
**Purpose**:
- Groups related chunks into batches for LLM processing
- Ensures batches stay within token limits
- Adds context and prompts for extraction
- Outputs to `data/processed/doc_batches.jsonl`

### 3. LLM Extraction
**File**: `backend/nsai/extract.py`  
**Process**:
1. Loads batched chunks
2. Sends to LLM (Gemini/OpenAI) for structured extraction
3. Parses responses into JSON format
4. Outputs raw extractions to `data/processed/extracted.jsonl`

### 4. Normalization & Canonicalization
**File**: `backend/nsai/normalize.py`  
**Key Functions**:
- `strip_parentheticals()`: Preserves important content in parentheses (acronyms, keywords) while cleaning
- `detect_type_from_tags()`: Infers concept types from tags and parenthetical content
- `to_canonical()`: Converts names to standardized Title Case format
- `normalize_record()`: Main function that processes each record

**Features**:
- Preserves acronyms and important keywords in parentheses
- Handles various formats of acronyms (uppercase, camelCase, dot-separated)
- Maintains original context while standardizing names
- Creates a mapping between original and canonical forms

**Outputs**:
- `data/processed/extracted_normalized.jsonl`: Normalized concepts with preserved context
- `data/processed/canonical_map.json`: Mapping between original and canonical forms

## Key Data Structures

### Chunk Format (metta_chunks.jsonl)
```json
{
  "text": "...chunk content...",
  "metadata": {
    "source": "filename.pdf",
    "page": 1,
    "section_path": "#section/subsection",
    "chunk_index": 0,
    "total_chunks": 5
  },
  "extras": {
    "candidate_atoms": [...],
    "definitions": [...],
    "rules": [...],
    "media_hints": [...]
  }
}
```

### Extraction Format (extracted.jsonl)
```json
{
  "domain": "healthcare",
  "metadata": {
    "doc_id": "document_123",
    "author": "Author Name",
    "provenance": "source.pdf"
  },
  "concepts": [
    {
      "name": "Diabetes",
      "concept_type": "Disease",
      "sub_concepts": [
        {
          "name": "Type 2 Diabetes",
          "explanation": "...detailed explanation...",
          "sub_type": "Variant",
          "evidence": {
            "sources": ["document_123#page=5"],
            "citations": ["1", "2"],
            "media": [{"type": "image", "url": "..."}]
          }
        }
      ]
    }
  ]
}
```

## How to Run

### Prerequisites
```bash
pip install -r requirements.txt
```

### Running the Pipeline
```bash
# Basic usage
python -m backend.ingestion --input-dir data/raw

# With custom options
python -m backend.ingestion \
  --input-dir data/raw \
  --output-dir data/processed \
  --batch-size 15 \
  --chunk-size 1000 \
  --chunk-overlap 150
```

## Current Limitations
1. Web page ingestion not yet implemented
2. No incremental processing (reprocesses all documents)
3. Limited error recovery in the pipeline
4. No parallel processing of batches

## Next Steps
1. Implement web page ingestion
2. Add incremental processing
3. Improve error handling and retries
4. Add parallel batch processing
5. Implement monitoring and metrics collection

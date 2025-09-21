I'll help you create clear documentation for your ingestion pipeline. Here's a comprehensive documentation structure:

# Document Ingestion Pipeline

## Overview
The pipeline processes raw documents into structured knowledge through a series of well-defined stages. It transforms unstructured text into a normalized knowledge graph with relationships between concepts.

## Pipeline Stages

### 1. Raw Data Ingestion
- **Location**: `data/raw/`
- **Input**: Raw documents (PDFs, text files, etc.)
- **Process**: 
  - Documents are loaded from the source directory
  - File metadata is extracted
  - Documents are prepared for chunking

### 2. Document Chunking
- **Script**: `metta_chunker.py`
- **Process**:
  - Documents are split into manageable chunks
  - Each chunk receives metadata including:
    - Source document ID
    - Chunk position
    - Character offsets
    - Document-specific metadata
- **Output**: Chunked documents in JSONL format

### 3. Batch Aggregation
- **Script**: `aggregate_docs.py`
- **Process**:
  - Groups related chunks into logical batches
  - Applies NSAI prompt templates
  - Adds context and examples to each batch
- **Output**: 
  - Batched documents in `data/processed/doc_batches.jsonl`
  - Each batch contains:
    - Document ID
    - Batch index and total batches
    - Chunks with context
    - NSAI extraction prompt
    - Metadata examples

### 4. Parallel LLM Processing
- **Module**: `nsai.extract`
- **Process**:
  - Loads batched documents
  - Makes parallel API calls to the LLM (Gemini)
  - Handles rate limiting and retries
  - Processes responses
- **Configuration**:
  - Environment variables:
    - `GEMINI_API_KEY`: Required for LLM access
    - `GEMINI_MODEL`: Model to use (default: "gemini-2.5-flash")
    - `NSAI_PROVIDER`: LLM provider (default: "gemini")
- **Output**: Raw extractions in [data/processed/extracted.jsonl](cci:7://file:///d:/query_verse/data/processed/extracted.jsonl:0:0-0:0)

### 5. Normalization
- **Script**: `normalize.py`
- **Process**:
  - Loads raw extractions
  - Normalizes structure and fields
  - Validates against schema
  - Handles edge cases
- **Output**: 
  - Normalized data in [data/processed/extracted_normalized.jsonl](cci:7://file:///d:/query_verse/data/processed/extracted_normalized.jsonl:0:0-0:0)
  - Canonical mappings in [data/processed/canonical_map.json](cci:7://file:///d:/query_verse/data/processed/canonical_map.json:0:0-0:0)

## Directory Structure
```
data/
├── raw/                  # Raw input documents
├── processed/
│   ├── doc_batches.jsonl     # Aggregated document batches
│   ├── extracted.jsonl       # Raw LLM extractions
│   ├── extracted_normalized.jsonl  # Normalized extractions
│   └── canonical_map.json    # Mappings between original and canonical terms
└── trial/                # Test outputs and experiments
```

## Running the Pipeline

1. **Prerequisites**:
   ```bash
   pip install -r requirements.txt
   export GEMINI_API_KEY='your-api-key'
   ```

2. **Run the full pipeline**:
   ```bash
   # 1. Chunk documents
   python -m metta_chunker --input-dir data/raw --output data/processed/chunks.jsonl
   
   # 2. Aggregate into batches
   python -m aggregate_docs --input data/processed/chunks.jsonl --output data/processed/doc_batches.jsonl
   
   # 3. Run LLM extraction
   python -m nsai.extract
   
   # 4. Normalize outputs
   python -m nsai.normalize
   ```

## Configuration

### Environment Variables
- `GEMINI_API_KEY`: Required for LLM access
- `GEMINI_MODEL`: Override default model
- `NSAI_PROVIDER`: LLM provider (default: "gemini")
- `LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)

### Rate Limiting
- Default: 60 requests per minute
- Configure in [nsai/extract.py](cci:7://file:///d:/query_verse/backend/nsai/extract.py:0:0-0:0) if needed

## Error Handling
- Failed batches are logged and skipped
- Automatic retries for API failures
- Detailed error logging in console and log files

## Monitoring
- Progress is logged to console
- Performance metrics are printed at completion
- Error counts and success rates are reported

## Output Schema

### Extracted Document
```json
{
  "doc_id": "document_identifier",
  "payload": {
    "domain": "Domain name",
    "concepts": [],
    "domain_specific_patterns": {},
    "extraction_completeness": {},
    "metadata": {}
  },
  "batch_index": 1,
  "total_batches": 3
}
```

## Troubleshooting

### Common Issues
1. **API Key Errors**
   - Verify `GEMINI_API_KEY` is set
   - Check for API quota limits

2. **JSON Parsing Errors**
   - Check for malformed responses
   - Review prompt templates

3. **Rate Limiting**
   - Reduce batch size
   - Add delays between requests

4. **Memory Issues**
   - Process fewer documents at once
   - Increase system memory if needed

## Performance Considerations
- Processing time scales with document count and complexity
- Larger batches improve throughput but increase memory usage
- Network latency affects overall performance

## Maintenance
- Monitor API usage and costs
- Update prompt templates as needed
- Review and update schema validations periodically

Would you like me to elaborate on any specific part of the documentation or make any adjustments to better suit your needs?
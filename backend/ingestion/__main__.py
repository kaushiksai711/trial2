"""
CLI for the QueryVerse document processing pipeline.

Usage:
    python -m backend.ingestion --input-dir data/raw [--output-dir data/processed] [--batch-size 10]
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

def run_pipeline(
    input_dir: Path,
    output_dir: Optional[Path] = None,
    batch_size: int = 10,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> None:
    """Run the complete document processing pipeline.
    
    Args:
        input_dir: Directory containing input documents
        output_dir: Directory for output files (default: data/processed)
        batch_size: Number of chunks per batch for LLM processing
        chunk_size: Target size for text chunks
        chunk_overlap: Overlap between chunks
    """
    import json
    from backend.ingestion.metta_chunker import MeTTaOptimizedChunker
    from backend.ingestion.aggregate_docs import build_batches
    from backend.nsai.extract import process_batches
    from backend.nsai.normalize import normalize_extractions
    
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Chunk documents
    print("🚀 Starting document chunking...")
    chunks_file = output_dir / "metta_chunks.jsonl"
    chunker = MeTTaOptimizedChunker(
        input_dir=input_dir,
        output_file=chunks_file,
        concept_chunk_size=chunk_size,
        concept_overlap=chunk_overlap
    )
    chunker.process_all()
    
    # 2. Build batches for LLM processing
    print("\n📦 Building document batches...")
    batches_file = output_dir / "doc_batches.jsonl"
    build_batches()  # Uses the chunks_file by default
    
    # 3. Process batches with LLM
    print("\n🧠 Extracting knowledge with LLM...")
    extract_file = output_dir / "extracted.jsonl"
    process_batches(input_file=batches_file, output_file=extract_file)
    
    # 4. Normalize extractions
    print("\n✨ Normalizing extractions...")
    normalized_file = output_dir / "extracted_normalized.jsonl"
    canonical_map_file = output_dir / "canonical_map.json"
    normalize_extractions(
        input_file=extract_file,
        output_file=normalized_file,
        canonical_map_file=canonical_map_file
    )
    
    print(f"\n✅ Pipeline completed successfully!")
    print(f"   - Raw chunks: {chunks_file}")
    print(f"   - LLM batches: {batches_file}")
    print(f"   - Raw extractions: {extract_file}")
    print(f"   - Normalized extractions: {normalized_file}")
    print(f"   - Canonical map: {canonical_map_file}")

def main():
    parser = argparse.ArgumentParser(description="Process documents into structured knowledge")
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing input documents (PDF, text, markdown)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for output files (default: data/processed)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of chunks per batch for LLM processing (default: 10)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1200,
        help="Target size for text chunks (default: 1200)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Overlap between chunks (default: 200)"
    )
    
    args = parser.parse_args()
    
    try:
        run_pipeline(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            batch_size=args.batch_size,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

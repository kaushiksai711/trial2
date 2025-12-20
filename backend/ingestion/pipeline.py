import json
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import argparse
from datetime import datetime
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths - go up one more level to reach the root of the project
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # Changed from parents[1] to parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_PDF_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Handle the script path with parentheses
script_name = "json_to_metta.py"
JSON_TO_METTA_SCRIPT = PROCESSED_DIR / script_name

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Debug: Print the script path to verify it's correct
print(f"MeTTa script path: {JSON_TO_METTA_SCRIPT}")
print(f"Script exists: {Path(JSON_TO_METTA_SCRIPT).exists()}")

# Output file paths
METTA_CHUNKS_PATH = PROCESSED_DIR / "metta_chunks.jsonl"
DOC_BATCHES_PATH = PROCESSED_DIR / "doc_batches.jsonl"
EXTRACTED_PATH = PROCESSED_DIR / "extracted.jsonl"
FINAL_OUTPUT_PATH = PROCESSED_DIR / "extracted_normalized.jsonl"
METTA_OUTPUT_DIR = PROCESSED_DIR / "metta_output"
METTA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_metta_chunker() -> None:
    """Run the MeTTa chunker to process PDFs into chunks."""
    from .metta_chunker import MeTTaOptimizedChunker
    
    logger.info("Starting MeTTa chunking process...")
    
    chunker = MeTTaOptimizedChunker(
        input_dir=RAW_PDF_DIR,
        output_file=METTA_CHUNKS_PATH,
        concept_chunk_size=1200,
        concept_overlap=100,
        enable_semantic=True
    )
    
    chunker.process_all()
    logger.info(f"MeTTa chunking completed. Output: {METTA_CHUNKS_PATH}")


def run_aggregate_docs() -> None:
    """Aggregate document chunks into batches for processing."""
    from .aggregate_docs import build_batches
    
    logger.info("Building document batches...")
    build_batches()
    logger.info(f"Document batching completed. Output: {DOC_BATCHES_PATH}")


def run_extraction() -> None:
    """Run the extraction process using Gemini."""
    from backend.nsai.extract import run as run_extraction
    
    logger.info("Starting document extraction with Gemini...")
    run_extraction()
    logger.info(f"Extraction completed. Output: {EXTRACTED_PATH}")


def run_normalization() -> None:
    """Normalize the extracted data."""
    from backend.nsai.normalize import run as run_normalization_process
    
    logger.info("Starting data normalization...")
    logger.info(f"Looking for input file: {EXTRACTED_PATH}")
    logger.info(f"Will write output to: {FINAL_OUTPUT_PATH}")
    
    # Ensure the output directory exists
    FINAL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    run_normalization_process()
    
    if not FINAL_OUTPUT_PATH.exists():
        logger.warning(f"Expected output file not found: {FINAL_OUTPUT_PATH}")
        # Try to find any normalized files that might have been created
        normalized_files = list(FINAL_OUTPUT_PATH.parent.glob('*normalized*.jsonl'))
        if normalized_files:
            logger.info(f"Found these potential normalized files: {[str(f) for f in normalized_files]}")
    else:
        logger.info(f"Normalization completed. Output: {FINAL_OUTPUT_PATH}")
        logger.info(f"File size: {FINAL_OUTPUT_PATH.stat().st_size} bytes")


def run_json_to_metta() -> None:
    """Convert the normalized JSON to MeTTa format."""
    logger.info("Starting JSON to MeTTa conversion...")
    
    # Debug: Print environment info
    import platform
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Current working directory: {Path.cwd()}")
    logger.info(f"Script path: {JSON_TO_METTA_SCRIPT}")
    logger.info(f"Absolute script path: {Path(JSON_TO_METTA_SCRIPT).resolve()}")
    logger.info(f"Script exists: {Path(JSON_TO_METTA_SCRIPT).exists()}")
    logger.info(f"Script is file: {Path(JSON_TO_METTA_SCRIPT).is_file()}")
    logger.info(f"Script permissions: {oct(Path(JSON_TO_METTA_SCRIPT).stat().st_mode)[-3:]}")
    
    # List files in the processed directory for debugging
    try:
        files = list(PROCESSED_DIR.glob('*'))
        logger.info(f"Files in {PROCESSED_DIR}:")
        for f in files:
            logger.info(f"- {f.name}")
    except Exception as e:
        logger.warning(f"Could not list files in {PROCESSED_DIR}: {str(e)}")
    
    logger.info(f"Input file: {FINAL_OUTPUT_PATH} (exists: {FINAL_OUTPUT_PATH.exists()})")
    logger.info(f"Output directory: {METTA_OUTPUT_DIR} (exists: {METTA_OUTPUT_DIR.exists()})")
    
    # Ensure the output directory exists
    METTA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Verify input file exists
    if not FINAL_OUTPUT_PATH.exists():
        error_msg = f"Input file not found: {FINAL_OUTPUT_PATH}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Verify the script exists
    if not Path(JSON_TO_METTA_SCRIPT).exists():
        error_msg = f"MeTTa conversion script not found: {JSON_TO_METTA_SCRIPT}\n"
        # Try to find the script in other locations
        possible_locations = [
            PROJECT_ROOT / "data" / "processed" / script_name,
            PROJECT_ROOT / "backend" / "data" / "processed" / script_name,
            Path("data/processed") / script_name,
            Path("../data/processed") / script_name,
        ]
        
        found_script = None
        for loc in possible_locations:
            if loc.exists():
                found_script = loc
                logger.info(f"Found script at alternative location: {found_script}")
                break
                
        if found_script is None:
            error_msg += "\nTried these locations but couldn't find the script:\n"
            error_msg += "\n".join([f"- {loc}" for loc in possible_locations])
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        # Use the found script path
        script_path = found_script
        
    
    try:
        # Prepare the command to run the json_to_metta script
        script_to_run = found_script if 'found_script' in locals() else JSON_TO_METTA_SCRIPT
        cmd = [
            sys.executable,  # Use the same Python interpreter
            str(script_to_run.resolve()),  # Convert to absolute path
            str(FINAL_OUTPUT_PATH.resolve()),
            "-o", 
            str((METTA_OUTPUT_DIR / "knowledge_base.py").resolve())
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        logger.info(f"Current working directory: {PROJECT_ROOT}")
        
        # Debug: Print the exact command being run
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run the command with a timeout of 300 seconds (5 minutes)
        # Use shell=True on Windows to handle paths with spaces/special characters
        is_windows = platform.system() == 'Windows'
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),  # Convert to string for better compatibility
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
            shell=is_windows  # Use shell on Windows to handle special characters
        )
        
        # Log detailed output
        if result.stdout:
            logger.info("Script output:\n" + result.stdout)
        
        if result.stderr:
            logger.warning("Script errors:\n" + result.stderr)
        
        if result.returncode != 0:
            error_msg = (
                f"Failed to convert JSON to MeTTa format. Exit code: {result.returncode}\n"
                f"Command: {' '.join(cmd)}\n"
                f"Working directory: {PROJECT_ROOT}\n"
                f"Error output:\n{result.stderr}"
            )
            logger.error(error_msg)
            raise RuntimeError(f"Failed to convert JSON to MeTTa format. See logs for details.")
        
        # Verify output was created
        output_file = METTA_OUTPUT_DIR / "knowledge_base.py"
        if not output_file.exists():
            error_msg = f"Expected output file was not created: {output_file}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info(f"MeTTa conversion completed successfully. Output in: {output_file}")
        
    except subprocess.TimeoutExpired:
        error_msg = "MeTTa conversion timed out after 5 minutes"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except subprocess.CalledProcessError as e:
        error_msg = f"Subprocess failed with return code {e.returncode}:\n{e.output}"
        logger.error(error_msg)
        raise RuntimeError(f"Failed to run MeTTa conversion: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during JSON to MeTTa conversion: {str(e)}", exc_info=True)
        raise


def run_full_pipeline() -> None:
    """Run the complete ingestion pipeline from PDFs to MeTTa format."""
    start_time = datetime.now()
    logger.info("Starting full ingestion pipeline...")
    
    try:
        # Step 1: Chunk PDFs into semantic chunks
        run_metta_chunker()
        
        # Step 2: Aggregate chunks into batches
        run_aggregate_docs()
        
        # Step 3: Process batches with Gemini
        run_extraction()
        
        # Step 4: Normalize the extracted data
        run_normalization()
        
        # Step 5: Convert to MeTTa format
        run_json_to_metta()
        
        duration = datetime.now() - start_time
        logger.info(f"Pipeline completed successfully in {duration}")
        logger.info(f"Final JSON output available at: {FINAL_OUTPUT_PATH}")
        logger.info(f"MeTTa output available in: {METTA_OUTPUT_DIR}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        raise


def main():
    """Command-line interface for the ingestion pipeline."""
    parser = argparse.ArgumentParser(description='Run the document ingestion pipeline.')
    
    parser.add_argument(
        '--step', 
        type=str,
        choices=['all', 'chunk', 'batch', 'extract', 'normalize', 'metta'],
        default='all',
        help='Pipeline step to run (default: all)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.step == 'all':
            run_full_pipeline()
        elif args.step == 'chunk':
            run_metta_chunker()
        elif args.step == 'batch':
            run_aggregate_docs()
        elif args.step == 'extract':
            run_extraction()
        elif args.step == 'normalize':
            run_normalization()
        elif args.step == 'metta':
            run_json_to_metta()
            
    except Exception as e:
        logger.error(f"Error in pipeline step '{args.step}': {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

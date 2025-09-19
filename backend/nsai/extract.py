import json
import os
import re
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone ,UTC
from pydantic import ValidationError
from .schema import (
    RelationType,
    DocumentExtraction,
    ExtractionBatchRecord,
    Concept,
    SubConcept,
    Evidence,
    Relation,
    CrossReference,
    Metadata,
    OperationalDetails,
    ContextualExamples,
    StakeholderEcosystem,
    ExecutionDetails,
    PerformanceIndicators,
    DomainSpecificPatterns,
    ExtractionCompleteness,
    MediaItem,
    MediaType,
    ConfidenceLevel,
    ImportanceLevel,
    ImplementationDifficulty,
    Assertion,
    AssertionType
)
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from dotenv import load_dotenv
load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BATCHES_PATH = PROJECT_ROOT / "data" / "processed" / "doc_batches.jsonl"
EXTRACTED_PATH = PROJECT_ROOT / "data" / "processed" / "extracted.jsonl"
PROMPT_TEMPLATE_PATH = PROJECT_ROOT / "backend" / "nsai" / "prompts" / "extract_prompt_2.txt"  # Updated to use enhanced prompt

# Choose provider via env var, default to Gemini
PROVIDER = os.getenv("NSAI_PROVIDER", "gemini").lower()

import multiprocessing as mp
from functools import partial  # For currying batch processor

# Worker function: Processes one batch (your existing logic, extracted)
def process_single_batch(batch_line: str, batch_index: int, total_batches: int) -> Optional[str]:
    """
    Worker function: Mirrors sequential logic for one batch.
    Returns JSONL line or None on error.
    """
    try:
        batch = json.loads(batch_line)
        doc_id = batch.get("doc_id", f"unknown_{batch_index}")
        batch_index = batch.get("batch_index", batch_index)  # Use provided or fallback
        total_batches = batch.get("total_batches", total_batches)
        
        logger.info(f"Worker {mp.current_process().name} starting batch {batch_index}/{total_batches} for {doc_id}")
        
        # Per-batch prompt assembly (from your working code)
        base_prompt = batch["nsai_extraction_prompt_doc"]
        examples = batch.get("metta_examples_doc", "")
        prompt = base_prompt
        if examples:
            prompt = f"{base_prompt}\n\nEXAMPLES (Heuristic, optional):\n{examples}"
        
        links_found = batch.get("links_found", [])
        # LLM call with retries
        response = _call_llm(prompt)
        
        # Clean and parse
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.strip())
        logger.info(f"Cleaned response for {doc_id}: {cleaned[:200]}...")  # Truncated log
        
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(cleaned)
            logger.error(f"Failed to parse JSON for {doc_id}: {e}")
            return None
        
        # Debug write (remove post-debug)
        parsed_json = json.loads(cleaned)  # Redundant but matches your code
        with open(f"cleaned_output_{doc_id}.json", "w", encoding="utf-8") as f:
            json.dump(parsed_json, f, indent=4, ensure_ascii=False)
        # with open(f"cleaned_output_{doc_id}.json", "r", encoding="utf-8") as f:
        #     payload=json.load(f)
        # Normalize extras (your function)
        processed_payload = normalize_extras(payload)
        # Extract links and post-process
        final_payload = _postprocess_payload(
            payload=processed_payload,
            doc_id=doc_id,
            links_found=links_found,
            batch_info={
                "batch_index": batch_index,
                "total_batches": total_batches
            }
        )
        if final_payload:
            record = ExtractionBatchRecord(
                doc_id=doc_id,
                payload=final_payload,
                batch_index=batch_index,
                total_batches=total_batches
            )
            return record.model_dump_json(exclude_none=True)
        else:
            logger.warning(f"Empty processed payload for {doc_id}")
            return None
            
    except Exception as e:
        logger.error(f"Worker error on batch {batch_index}: {str(e)}", exc_info=True)
        return None
def _load_prompt_template() -> str:
    """Load the enhanced extraction prompt template."""
    try:
        with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt template not found at {PROMPT_TEMPLATE_PATH}")
        raise
    except Exception as e:
        logger.error(f"Error loading prompt template: {str(e)}")
        raise


def _call_llm(prompt: str, max_retries: int = 3) -> str:
    """
    Call the LLM with the given prompt and return the response.
    
    Args:
        prompt: The prompt to send to the LLM
        max_retries: Maximum number of retry attempts on failure
        
    Returns:
        str: The raw text response from the LLM
        
    Raises:
        RuntimeError: If all retry attempts fail or API key is missing
    """
    if PROVIDER == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set. Configure environment before running extractor.")
            
        # Lazy import to avoid hard dependency when not used
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name)
        
        # Configure generation parameters
        generation_config = {
            "temperature": 0.2,  # Lower temperature for more focused, deterministic outputs
            "top_p": 0.95,
            "top_k": 40, # Increased for complex responses
            # "response_mime_type": "application/json"
        }
        
        last_error = None
        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    ],
                )
                
                # Extract text from response
                if hasattr(response, "text") and response.text:
                    return response.text.strip()
                    
                # Fallback: Try to extract text from candidates
                for candidate in getattr(response, "candidates", []):
                    if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                        parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, "text"):
                                parts.append(part.text)
                        if parts:
                            return "\n".join(parts).strip()
                
                # If we got here, no text was found in the response
                raise ValueError("No text found in LLM response")
                
            except Exception as e:
                last_error = e
                wait_time = (2 ** attempt) + 1  # Exponential backoff
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed. "
                    f"Retrying in {wait_time} seconds. Error: {str(e)}"
                )
                time.sleep(wait_time)
        
        # If we've exhausted all retries
        raise RuntimeError(f"Failed to get valid response after {max_retries} attempts. Last error: {str(last_error)}")
    
    else:
        raise ValueError(f"Unsupported provider: {PROVIDER}")


def _coerce_list(obj: Any) -> List[Dict[str, Any]]:
    """
    Ensure response is a list of JSON objects.
    
    Args:
        obj: The object to coerce into a list of dictionaries
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries
    """
    if obj is None:
        return []
    if isinstance(obj, dict):
        return [obj]
    if isinstance(obj, list):
        # Filter out non-dict items and empty dicts
        return [item for item in obj if isinstance(item, dict) and item]
    return []


def _merge_backcompat_into_evidence(sc: Dict[str, Any]) -> None:
    """
    Map back-compat fields (sources/links/media/tables) into evidence if present.
    
    Args:
        sc: The sub-concept or concept dictionary to process
    """
    if not isinstance(sc, dict):
        return
        
    # Initialize evidence if it doesn't exist
    if "evidence" not in sc or not isinstance(sc["evidence"], dict):
        sc["evidence"] = {}
    
    evidence = sc["evidence"]
    
    # Map old fields into evidence if they exist and evidence doesn't have them
    for field in ["sources", "links", "media", "tables"]:
        if field in sc and field not in evidence and sc[field]:
            evidence[field] = sc[field]
            # Optionally, you could remove the old field after migration
            # del sc[field]
    
    # Ensure required evidence fields exist
    for field in ["sources", "links", "media", "tables", "citations", "document_sections"]:
        if field not in evidence:
            if field in ["sources", "links", "media", "tables", "citations", "document_sections"]:
                evidence[field] = []


def _populate_sources_links_if_empty(sc, links_found=None):
    """Populate sources and links in the structured content if they're empty."""
    if links_found is None:
        links_found = []
    
    evidence = sc.get("evidence", {})
    
    # Only populate if both sources and links are empty
    if not evidence.get("sources") and not evidence.get("links"):
        # Only add links that aren't already in the evidence
        existing_links = set(evidence.get("links", []))
        new_links = [link for link in links_found if link not in existing_links]
        
        if new_links:
            if "links" not in evidence:
                evidence["links"] = []
            evidence["links"].extend(new_links)
    
    return sc

def _ensure_required_fields(concept: Dict[str, Any]) -> None:
    """Ensure all required fields are present in the concept.
    
    Args:
        concept: The concept dictionary to validate
    """
    # # Ensure required fields exist with default values if missing
    # concept.setdefault('name', 'Unnamed Concept')
    # concept.setdefault('concept_type', 'Concept')
    # concept.setdefault('operational_details', {})
    # concept.setdefault('contextual_examples', {})
    # concept.setdefault('related_concepts', [])
    # concept.setdefault('relations', [])
    # concept.setdefault('metadata', {})
    
    # # Ensure operational_details has all required sub-fields
    # op_details = concept['operational_details']
    # op_details.setdefault('practical_measures', [])
    # op_details.setdefault('implementation_steps', [])
    # op_details.setdefault('resources_required', [])
    # op_details.setdefault('timeline_indicators', [])
    # op_details.setdefault('success_criteria', [])
    # op_details.setdefault('common_challenges', [])
    # op_details.setdefault('best_practices', [])
    
    # # Ensure contextual_examples has all required sub-fields
    # #ctx_examples = concept['contextual_examples']
    # # ctx_examples.setdefault('real_world_cases', [])
    # # ctx_examples.setdefault('hypothetical_scenarios', [])
    # # ctx_examples.setdefault('quantitative_data', [])
    # # ctx_examples.setdefault('qualitative_indicators', [])
    
    # # Process sub-concepts if they exist
    # if 'sub_concepts' not in concept:
    #     concept['sub_concepts'] = []
    
    # # Recursively ensure required fields in sub-concepts
    # for sub_concept in concept['sub_concepts']:
    #     _ensure_required_fields(sub_concept)
    return


def normalize_relation(relation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize relation data to handle custom relation types.
    
    Args:
        relation_data: The raw relation data from the LLM
        
    Returns:
        Dict[str, Any]: Normalized relation data with proper type handling
    """
    if not isinstance(relation_data, dict) or 'type' not in relation_data:
        return relation_data
        
    try:
        # Try to convert to a standard relation type
        relation_type = relation_data["type"].lower().replace('_', '-')
        relation_data["type"] = RelationType(relation_type).value
        # Remove custom_type if it exists (not needed for standard types)
        if "custom_type" in relation_data:
            del relation_data["custom_type"]
    except (ValueError, AttributeError):
        # If the type isn't in our enum, convert to CUSTOM
        custom_type = str(relation_data.get("type", ""))
        relation_data["type"] = RelationType.CUSTOM.value
        relation_data["custom_type"] = custom_type
        logger.debug(f"Converted custom relation type to CUSTOM: {custom_type}")
        
    return relation_data


def _postprocess_payload(
    payload: Dict[str, Any], 
    doc_id: str, 
    links_found: List[str] = None,
    batch_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Post-process and validate the extracted payload.
    
    Args:
        payload: The raw payload from the LLM
        doc_id: Document identifier for logging
        links_found: List of links found in the document
        batch_info: Optional batch information (index, total)
        
    Returns:
        Dict[str, Any]: Processed and validated payload
    """
    if links_found is None:
        links_found = []
        
    try:
        # Ensure prerequisites is always a list
        if 'concepts' not in payload:
            payload['concepts'] = []
            
        # Process each concept
        for concept in payload.get('concepts', []):
            _ensure_required_fields(concept)
            
            # Normalize relations in the concept
            if 'relations' in concept and isinstance(concept['relations'], list):
                concept['relations'] = [normalize_relation(r) for r in concept['relations']]
            
            # Process sub-concepts
            for sub_concept in concept.get('sub_concepts', []):
                _ensure_required_fields(sub_concept)
                
        # Ensure relations have valid strength values
        def fix_relation_strength(rel):
            valid_strengths = {'low', 'medium', 'high', 'strong'}
            if 'strength' not in rel or not isinstance(rel['strength'], str) or rel['strength'].lower() not in valid_strengths:
                rel['strength'] = 'medium'  # Default to 'medium' if invalid or missing
            else:
                rel['strength'] = rel['strength'].lower()  # Ensure lowercase
            return rel
            
        # Apply to all relations in concepts and sub-concepts
        def process_relations_in_concept(concept_dict):
            if 'relations' in concept_dict and isinstance(concept_dict['relations'], list):
                concept_dict['relations'] = [fix_relation_strength(r) for r in concept_dict['relations']]
            
            # Process sub-concepts recursively
            for sub_concept in concept_dict.get('sub_concepts', []):
                process_relations_in_concept(sub_concept)
        
        # Process all concepts and their sub-concepts
        for concept in payload.get('concepts', []):
            process_relations_in_concept(concept)

        # Add processed_at with timezone
        payload['metadata'] = payload.get('metadata', {})
        payload['metadata']['processed_at'] = datetime.now(UTC).isoformat()

        # Populate sources/links if empty
        # for concept in payload.get('concepts', []):
        #     concept = _populate_sources_links_if_empty(concept, links_found)
        #     for sub_concept in concept.get('sub_concepts', []):
        #         _populate_sources_links_if_empty(sub_concept, links_found)
        payload = normalize_extras(payload)#check
        # Validate against the schema
        validated = DocumentExtraction(**payload)
        return validated.model_dump(exclude_none=True)
        
    except ValidationError as ve:
        logger.error(f"Validation error in document {doc_id}: {ve}")
        raise
    except Exception as e:
        logger.error(f"Error processing payload for document {doc_id}: {str(e)}", exc_info=True)
        # Return an empty dict to avoid breaking the pipeline
        return {}
def run():
    """
    Main entry point: Parallel extraction mirroring sequential logic.
    """
    if not BATCHES_PATH.exists():
        raise FileNotFoundError(f"Batches not found at {BATCHES_PATH}. Run aggregate_docs first.")
    
    logger.info("Starting parallel document extraction process...")
    start_time = time.time()
    
    # Ensure output directory exists
    EXTRACTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    error_count = 0
    
    try:
        with open(BATCHES_PATH, "r", encoding="utf-8") as f_in, \
             open(EXTRACTED_PATH, "w", encoding="utf-8") as f_out:
            
            lines = [line.strip() for line in f_in if line.strip()]  # Read and clean
            total_lines = len(lines)
            
            if total_lines == 0:
                logger.warning("No batches to process.")
                return
            
            logger.info(f"Processing {total_lines} batches from {BATCHES_PATH}")
            
            # Parallel processing
            num_workers = min(mp.cpu_count(), 6)  # Tune: 4-6 for Gemini quotas
            logger.info(f"Starting parallel extraction with {num_workers} workers on {total_lines} batches.")
            
            with mp.Pool(processes=num_workers) as pool:
                # No partial needed since prompt is per-batch; pass indices via enumerate
                batch_results = pool.starmap(
                    process_single_batch,
                    [(line, idx, total_lines) for idx, line in enumerate(lines)]
                )
            
            # Collect and write sequentially
            for idx, result in enumerate(batch_results):
                if result:
                    f_out.write(result + "\n")
                    processed_count += 1
                else:
                    error_count += 1
                    logger.warning(f"Batch {idx} failed; skipping.")
            
            # Post-facto progress
            elapsed = time.time() - start_time
            rate = total_lines / elapsed if elapsed > 0 else 0
            logger.info(f"Parallel progress: {total_lines}/{total_lines} ({100:.1f}%, {rate:.2f} batches/sec)")
    
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {BATCHES_PATH}")
        return
    except Exception as e:
        logger.error(f"Fatal error in extraction process: {str(e)}", exc_info=True)
        return
    
    # Summary
    elapsed = time.time() - start_time
    logger.info("\n=== Extraction Complete ===")
    logger.info(f"Total batches processed: {processed_count}")
    logger.info(f"Errors encountered: {error_count}")
    logger.info(f"Time taken: {elapsed:.2f} seconds")
    if processed_count > 0:
        logger.info(f"Average time per batch: {elapsed/processed_count:.2f} seconds")
    
    logger.info(f"Results written to: {EXTRACTED_PATH}")

# def run() -> None:
#     """
#     Main entry point for the extractor.
#     Processes batches of documents and extracts structured information using the LLM.
#     """
#     if not BATCHES_PATH.exists():
#         raise FileNotFoundError(f"Batches not found at {BATCHES_PATH}. Run aggregate_docs first.")
    
#     logger.info("Starting document extraction process...")
#     start_time = time.time()
    
#     # Load the prompt template
#     try:
#         prompt_template = _load_prompt_template()
#         logger.info("Loaded prompt template successfully")
#     except Exception as e:
#         logger.error(f"Failed to load prompt template: {str(e)}")
#         return
    
#     # Ensure output directory exists
#     EXTRACTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    
#     # Process each batch
#     processed_count = 0
#     error_count = 0
    
#     try:
#         with open(BATCHES_PATH, "r", encoding="utf-8") as f_in, \
#              open(EXTRACTED_PATH, "w", encoding="utf-8") as f_out:
            
#             total_lines = sum(1 for _ in f_in)
#             f_in.seek(0)  # Reset file pointer
            
#             logger.info(f"Processing {total_lines} batches from {BATCHES_PATH}")
            
#             for line_num, line in enumerate(f_in, 1):
#                 try:
#                     # Parse the batch
#                     batch = json.loads(line)
#                     doc_id = batch.get("doc_id", f"unknown_{line_num}")
#                     batch_index = batch.get("batch_index", 0)
#                     total_batches = batch.get("total_batches", 1)
#                     base_prompt = batch["nsai_extraction_prompt_doc"]
#                     examples = batch.get("metta_examples_doc", "")
#                     prompt = base_prompt
#                     if examples:
#                         prompt = f"{base_prompt}\n\nEXAMPLES (Heuristic, optional):\n{examples}"

#                     # Call the LLM with retries
#                     try:
#                         #check
#                         response = _call_llm(prompt)
#                         cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.strip())
#                         # with open("cleaned_output.json", "r", encoding="utf-8") as f:
#                         #     data = json.load(f)
#                         # cleaned = data
                        
#                         # Parse the response #check
#                         logger.info(cleaned)
#                         try:
#                             payload = json.loads(cleaned) #check
#                             #payload=cleaned
#                         except json.JSONDecodeError as e:
#                             logger.error(f"Failed to parse JSON response for {doc_id}: {e}")
#                             error_count += 1
#                             continue
#                         parsed_json = json.loads(cleaned)  # ensure it's valid JSON
#                         with open("cleaned_output.json", "w", encoding="utf-8") as f: #check
#                             json.dump(parsed_json, f, indent=4, ensure_ascii=False)
#                         # Extract links from batch data if available
#                         links_found = batch.get("links", [])
                        
#                         # Post-process the payload
#                         processed = _postprocess_payload(
#                             payload=payload,
#                             doc_id=doc_id,
#                             links_found=links_found,
#                             batch_info={
#                                 "batch_index": batch_index,
#                                 "total_batches": total_batches
#                             }
#                         )
                        
#                         # Write the result if we got valid data
#                         if processed:
#                             record = ExtractionBatchRecord(
#                                 doc_id=doc_id,
#                                 payload=processed,
#                                 batch_index=batch_index,
#                                 total_batches=total_batches
#                             )
#                             f_out.write(record.model_dump_json(exclude_none=True) + "\n")
#                             processed_count += 1
#                         else:
#                             logger.warning(f"Empty processed payload for {doc_id}")
#                             error_count += 1

#                             #check
#                         #return  
#                     except Exception as e:
#                         logger.error(f"Error processing batch for {doc_id}: {str(e)}", exc_info=True)
#                         error_count += 1
#                         continue
                    
#                     # Log progress periodically
#                     if line_num % 10 == 0 or line_num == total_lines:
#                         elapsed = time.time() - start_time
#                         rate = line_num / elapsed if elapsed > 0 else 0
#                         logger.info(
#                             f"Progress: {line_num}/{total_lines} batches processed "
#                             f"({line_num/total_lines*100:.1f}%, {rate:.2f} batches/sec)"
#                         )
                
#                 except json.JSONDecodeError as e:
#                     logger.error(f"Invalid JSON in batch at line {line_num}: {str(e)}")
#                     error_count += 1
#                 except Exception as e:
#                     logger.error(f"Unexpected error processing line {line_num}: {str(e)}", exc_info=True)
#                     error_count += 1
    
#     except FileNotFoundError as e:
#         logger.error(f"Input file not found: {BATCHES_PATH}")
#         return
#     except Exception as e:
#         logger.error(f"Fatal error in extraction process: {str(e)}", exc_info=True)
#         return
    
#     # Print summary
#     elapsed = time.time() - start_time
#     logger.info("\n=== Extraction Complete ===")
#     logger.info(f"Total batches processed: {processed_count}")
#     logger.info(f"Errors encountered: {error_count}")
#     logger.info(f"Time taken: {elapsed:.2f} seconds")
#     if processed_count > 0:
#         logger.info(f"Average time per batch: {elapsed/processed_count:.2f} seconds")
    
#     logger.info(f"Results written to: {EXTRACTED_PATH}")

def normalize_extras(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize LLM output by moving extra fields to extensions."""
    if not isinstance(payload, dict):
        return payload

    # Define core fields for each entity type
    CORE_FIELDS = {
        'concept': {
            'name', 'concept_type', 'explanation', 'operational_details',
            'contextual_examples', 'related_concepts', 'relations',
            'assertions', 'sub_concepts', 'metadata', 'extensions'
        },
        'relation': {
            'type', 'target', 'note', 'strength', 'custom_type',
            'conditions', 'confidence'
        },
        'assertion': {
            'text', 'assertion_type', 'confidence', 'citations'
        }
    }

    def process_entity(entity: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """Process a single entity (concept, relation, or assertion)."""
        if not isinstance(entity, dict):
            return entity

        # Make a copy to avoid modifying during iteration
        entity = entity.copy()
        extensions = entity.get('extensions', {}).copy()
        
        # Get core fields for this entity type
        core_fields = CORE_FIELDS.get(entity_type, set())
        
        # Process each field
        for key in list(entity.keys()):
            value = entity[key]
            
            # Skip core fields and extensions
            if key in core_fields or key == 'extensions':
                continue
                
            # Handle nested structures
            if isinstance(value, dict):
                # Handle relations
                if 'target' in value and 'type' in value:
                    entity[key] = process_entity(value, 'relation')
                # Handle assertions
                elif 'text' in value and 'assertion_type' in value:
                    entity[key] = process_entity(value, 'assertion')
                # Handle other dicts
                else:
                    entity[key] = process_entity(value, entity_type)
                continue
                
            # Handle lists
            if isinstance(value, list):
                entity[key] = [
                    process_entity(item, entity_type) if isinstance(item, dict) else item
                    for item in value
                ]
                continue
                
            # Move non-core fields to extensions
            extensions[key] = value
            del entity[key]
        
        # Update extensions if we found any
        if extensions:
            entity['extensions'] = {
                **extensions,
                **entity.get('extensions', {})
            }
            
        return entity

    # Process the entire payload
    normalized = payload.copy()
    
    # Process concepts
    if 'concepts' in normalized and isinstance(normalized['concepts'], list):
        normalized['concepts'] = [
            process_entity(concept, 'concept')
            for concept in normalized['concepts']
        ]
    
    return normalized

if __name__ == "__main__":
    run()

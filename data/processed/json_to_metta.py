
# METTA CODE GENERATOER WITH CUSTOMIZED FILE NAMES AND WITHOUT ATOMSPACES 
import json
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MettaFlatGenerator:
    """
    Generates a MeTTa script with a flat, relational hierarchy in a global space.
    """

    def __init__(self):
        self.metta_code: List[str] = []
        self.all_entities: Dict[str, str] = {}
        self.processed_concepts: set = set()
        self.seen_atoms: set = set()
        self.predicates: set = set()
        self.custom_types: set = set()

    @staticmethod
    def normalize_symbol(text: str) -> str:
        """Converts a string into a MeTTa-compatible symbol."""
        if not isinstance(text, str): text = str(text)
        text = text.replace('–', '-')
        text = re.sub(r'[\s/]+', '-', text)
        text = re.sub(r'[(),{}\[\]"\'`.:;!?™]', '', text)
        text = re.sub(r'-+', '-', text).strip('-').lower()
        return text if text else 'unnamed-entity'

    def _add_atom(self, content: str):
        """Helper to format and add a flat atom, preventing duplicates."""
        atom_string = f"({content})"
        if atom_string in self.seen_atoms:
            return
        self.metta_code.append(atom_string)
        self.seen_atoms.add(atom_string)
    
    def _add_comment(self, text: str, level: int = 1):
        """Adds a formatted comment to the MeTTa code."""
        prefix = ';' * level
        self.metta_code.append(f"\n{prefix} --- {text} ---")

    def _discover_entities_recursive(self, data: Any):
        """Recursively finds all named concepts and their types to build a global vocabulary."""
        if isinstance(data, dict):
            if name := data.get('name'):
                entity_id = self.normalize_symbol(name)
                entity_type = self.normalize_symbol(data.get('concept_type') or data.get('sub_type') or 'concept')
                
                if entity_id not in self.all_entities:
                    self.all_entities[entity_id] = entity_type

                if entity_type not in ['concept', 'atomspace']:
                    self.custom_types.add(entity_type)
            
            for key in ['related_concepts', 'primary_actors', 'supporting_actors']:
                if items := data.get(key):
                    for item_name in items:
                        item_id = self.normalize_symbol(item_name)
                        if item_id not in self.all_entities:
                            self.all_entities[item_id] = 'concept'

            for key in ['relations', 'cross_references']:
                 if relations := data.get(key):
                     for rel in relations:
                         if target_name := rel.get('target'):
                             target_id = self.normalize_symbol(target_name)
                             if target_id not in self.all_entities:
                                 self.all_entities[target_id] = 'concept'
            
            for value in data.values():
                self._discover_entities_recursive(value)

        elif isinstance(data, list):
            for item in data:
                self._discover_entities_recursive(item)

    def _process_document(self, doc_data: Dict):
        """Processes a single document's content."""
        doc_id = self.normalize_symbol(doc_data.get('doc_id', 'untitled-doc'))
        payload = doc_data.get('payload', {})
        
        self._add_comment(f"Document: {doc_id}", 3)
        self._add_atom(f"isa {doc_id} Document")

        if domain := payload.get('domain'):
            self.predicates.add("has-domain")
            self._add_atom(f"has-domain {doc_id} {self.normalize_symbol(domain)}")

        if concepts := payload.get('concepts'):
            for concept_data in concepts:
                self._process_concept(concept_data, parent_id=doc_id, parent_relation="has-concept")

    def _process_concept(self, concept_data: Dict, parent_id: str, parent_relation: str = "has-subconcept"):
        """Recursively processes a concept and adds all its info as flat atoms."""
        name = concept_data.get('name')
        if not name: return
        concept_id = self.normalize_symbol(name)
        
        if concept_id in self.processed_concepts: return
        
        self._add_comment(f"Concept: {name}", 1)
        self.predicates.add(parent_relation)
        self._add_atom(f"{parent_relation} {parent_id} {concept_id}")

        self.processed_concepts.add(concept_id)

        if explanation := concept_data.get('explanation'):
            self.predicates.add("has-explanation")
            self._add_atom(f"has-explanation {concept_id} \"{explanation.replace('"', '\\"')}\"")
        
        if relations := concept_data.get('relations'):
            for rel in relations:
                rel_type = self.normalize_symbol(rel.get('custom_type') or rel.get('type', 'related-to'))
                target_id = self.normalize_symbol(rel.get('target', ''))
                if target_id:
                    self.predicates.add(rel_type)
                    self._add_atom(f"{rel_type} {concept_id} {target_id}")

        if related_concepts := concept_data.get('related_concepts'):
            self.predicates.add("related-to")
            for rel_name in set(related_concepts):
                self._add_atom(f"related-to {concept_id} {self.normalize_symbol(rel_name)}")

        if op_details := concept_data.get('operational_details'):
            for key, values in op_details.items():
                if values:
                    pred = self.normalize_symbol(key)
                    self.predicates.add(pred)
                    for value in values:
                        self._add_atom(f"{pred} {concept_id} \"{value.replace('"', '')}\"")

        if stakeholders := concept_data.get('stakeholder_ecosystem'):
            for key, values in stakeholders.items():
                if values:
                    pred = f"has-{self.normalize_symbol(key.rstrip('s'))}"
                    self.predicates.add(pred)
                    for value in values:
                        self._add_atom(f"{pred} {concept_id} {self.normalize_symbol(value)}")
        
        if evidence := concept_data.get('evidence'):
            self._process_evidence(evidence, parent_id=concept_id)

        if assertions := concept_data.get('assertions'):
            for i, assert_data in enumerate(assertions):
                self._process_assertion(assert_data, i, parent_id=concept_id)
        
        if sub_concepts := concept_data.get('sub_concepts'):
            for sub_data in sub_concepts:
                self._process_concept(sub_data, parent_id=concept_id, parent_relation="has-subconcept")

    def _process_evidence(self, evidence_data: Dict, parent_id: str):
        for key, values in evidence_data.items():
            if not isinstance(values, list) or not values: continue
            predicate = f"has-{self.normalize_symbol(key.rstrip('s'))}"
            self.predicates.add(predicate)
            for value in values:
                object_part = f'"{value}"' if isinstance(value, str) and value.startswith('http') else f'"{str(value).replace("\"", "\\\"").lower()}"'
                self._add_atom(f"{predicate.lower()} {parent_id.lower()} {object_part}")

    def _process_assertion(self, assert_data: Dict, index: int, parent_id: str):
        assertion_id = f"assertion-{parent_id}-{index}"
        
        self.predicates.add("has-assertion")
        self._add_atom(f"has-assertion {parent_id.lower()} {assertion_id.lower()}")
        
        if text := assert_data.get('text'):
            self.predicates.add("has-text")
            quoted_text = f'"{text.replace("\"", "\\\"")}"'
            self._add_atom(f"has-text {assertion_id.lower()} {quoted_text.lower()}")

        if a_type := assert_data.get('assertion_type'):
            self.predicates.add("has-type")
            self._add_atom(f"has-type {assertion_id.lower()} {self.normalize_symbol(a_type)}")

        if evidence := assert_data.get('evidence'):
            self._process_evidence(evidence, parent_id=assertion_id)

        if cross_refs := assert_data.get('cross_references'):
           self.predicates.add("cross-reference")
           for ref in cross_refs:
               if target := ref.get('target'):
                   self._add_atom(f"cross-reference {parent_id} {self.normalize_symbol(target)}")

    def generate_from_jsonl(self, input_path: Path, output_path: Path, predicates_path: Path):
        logging.info(f"Starting flat relational extraction from '{input_path}'...")
        
        try:
            with open(input_path, 'r', encoding='utf-8') as infile:
                all_docs = [json.loads(line) for line in infile if line.strip()]

            # --- Determine all output filenames dynamically ---
            
            # Determine the base filename from the doc_id
            if all_docs and (doc_id := all_docs[0].get('doc_id')):
                base_filename = self.normalize_symbol(doc_id)
            else:
                base_filename = 'untitled-document'

            # Determine path for the Python script runner
            if output_path is None:
                final_python_path = Path(f"{base_filename}_runner.py")
            else:
                final_python_path = output_path
            
            # Determine path for the MeTTa file
            metta_file_path = final_python_path.parent / f"{base_filename}.metta"

            # **MODIFICATION**: Determine path for the predicates file
            if predicates_path is None:
                domain_str = 'unknown'  # Default domain if not found
                if all_docs and (payload := all_docs[0].get('payload')) and (domain := payload.get('domain')):
                    domain_str = self.normalize_symbol(domain)
                final_predicates_path = Path(f"predicates_{domain_str}.txt")
            else:
                final_predicates_path = predicates_path

            # --- Generation continues with the determined paths ---

            self._add_comment("Phase 1: Global Entity Declarations", 3)
            self._discover_entities_recursive(all_docs)
            
            self.metta_code.append(";; Declare custom types before using them")
            for custom_type in sorted(list(self.custom_types)):
                self.metta_code.append(f"(: {custom_type} Type)")
            self.metta_code.append("")

            self.metta_code.append(";; Declare all individual entities")
            for entity_id, entity_type in sorted(self.all_entities.items()):
                self.metta_code.append(f"(: {entity_id} {entity_type})")

            self._add_comment("Phase 2: Knowledge Base Construction", 3)
            for doc_data in tqdm(all_docs, desc="Processing Documents"):
                self._process_document(doc_data)
            
            self._add_comment("Phase 3: Global Inference Rules", 3)
            self.metta_code.append("(=> (And (has-subconcept $a $b) (has-subconcept $b $c)) (has-subconcept $a $c))")

            metta_code_str = "\n".join(self.metta_code)
            
            metta_file_path.write_text(metta_code_str, encoding='utf-8')
            logging.info(f"✅ Generated raw MeTTa file: '{metta_file_path}'")

            predicates_str = "\n".join(sorted(list(self.predicates)))
            final_predicates_path.write_text(predicates_str, encoding='utf-8')
            logging.info(f"✅ Generated predicates list: '{final_predicates_path}'")

            python_script = self._build_python_script(metta_code_str)
            final_python_path.write_text(python_script, encoding='utf-8')
            
            logging.info(f"✅ Generated Python script: '{final_python_path}'")

        except FileNotFoundError:
            logging.error(f"Input file not found: '{input_path}'")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}", exc_info=True)

    def _build_python_script(self, metta_code: str) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        queries = [
            ("Find all sub-concepts of 'Symptom'", 
             "!(match (has-subconcept symptom $sub) $sub)"),
            ("Find what 'Civil Unrest' is a sub-concept of",
             "!(match (has-subconcept $parent civil-unrest) $parent)"),
            ("Find the text and sources for an assertion about 'Drop Cover and Hold on'",
             '''!(match 
                  (And (has-assertion drop-cover-and-hold-on $assert)
                       (has-text $assert $txt)
                       (has-source $assert $src))
                  (list $txt $src))''')
        ]
        
        query_blocks = []
        for desc, query_logic in queries:
            query_blocks.append(f'''
    # Query: {desc}
    print(f"\\n🔍 {desc}")
    query = """{query_logic}"""
    try:
        results = runner.run(query)
        if results:
            print("    Results:")
            for result in results:
                res_str = str(result[0]) if isinstance(result, list) and len(result) == 1 else str(result)
                print(f"    - {{res_str}}")
        else:
            print("    - No results found.")
    except Exception as e:
        print(f"    - Query error: {{e}}")''')
        query_section = "\n".join(query_blocks)

        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeTTa Knowledge Base Script (Flat Model)
Generated on: {timestamp}
"""
from hyperon import MeTTa

# --- MeTTa Knowledge Base ---
METTA_CODE = """
{metta_code}
"""

def main():
    """Initialize MeTTa runner and demonstrate knowledge base queries."""
    print("🧠 Loading MeTTa knowledge base...")
    runner = MeTTa()
    
    try:
        runner.run(METTA_CODE)
        print("    ✅ Knowledge base loaded successfully.")
    except Exception as e:
        print(f"    ❌ Error loading knowledge base: {{e}}")
        return
    
    # --- Run relational queries in the global space --- {query_section}

if __name__ == '__main__':
    main()
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Generate a flat, relational Python/MeTTa KB from a JSONL file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("input_file", type=Path, help="Path to the input JSONL file")
    
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Path for the output Python script. Defaults to a name based on the document ID (e.g., my-doc-id_runner.py).")
    
    # **MODIFICATION**: Default is now None, to be handled dynamically
    parser.add_argument("-p", "--predicates-file", type=Path, default=None,
                        help="Path for the predicates file. Defaults to 'predicates_<domain>.txt' based on the document's domain.")
    
    args = parser.parse_args()
    
    generator = MettaFlatGenerator()
    generator.generate_from_jsonl(args.input_file, args.output, args.predicates_file)
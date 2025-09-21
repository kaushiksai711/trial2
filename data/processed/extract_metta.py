
# import json
# import re
# import argparse
# import logging
# from pathlib import Path
# from typing import List, Dict, Any, Optional, Set, Tuple
# from datetime import datetime
# from dataclasses import dataclass
# from tqdm import tqdm

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# @dataclass
# class RelationType:
#     """Defines properties of a semantic relation."""
#     name: str
#     is_symmetric: bool = False
#     is_transitive: bool = False

# class SemanticRelationRegistry:
#     """A registry to manage relation types and their logical properties."""
#     def __init__(self):
#         self.relation_types = {
#             'sub-concept-of': RelationType('sub-concept-of', is_transitive=True),
#             'part-of': RelationType('part-of', is_transitive=True),
#             'is-a': RelationType('is-a', is_transitive=True),
#             'has-phase': RelationType('has-phase'),
#             'synonym-of': RelationType('synonym-of', is_symmetric=True),
#             'related-to': RelationType('related-to', is_symmetric=True)
#         }

#     def get_relation_type(self, name: str) -> RelationType:
#         """Gets a relation type, creating a default if not found."""
#         norm_name = name.lower().replace('_', '-')
#         if norm_name not in self.relation_types:
#             # Dynamically add new relation types found in the data
#             self.relation_types[norm_name] = RelationType(norm_name)
#         return self.relation_types[norm_name]

# class MettaScriptGenerator:
#     """Orchestrates the conversion of JSONL to a runnable MeTTa Python script."""
    
#     RESERVED_TYPES = {'concept', 'document'}

#     def __init__(self):
#         # MeTTa code components
#         self.declarations: List[str] = []
#         self.relations: List[str] = []
#         self.assertions_evidence: List[str] = []
#         self.rules: List[str] = []
        
#         # Unified data store
#         self.all_entities: Dict[str, Tuple[str, str]] = {}  # {id: (type, original_name)}
#         self.relation_registry = SemanticRelationRegistry()
#         self.query_examples: List[Tuple[str, str]] = [] # (Description, Query Logic)

#     @staticmethod
#     def normalize_symbol(text: str) -> str:
#         """Converts a string into a MeTTa-compatible symbol."""
#         if not isinstance(text, str):
#             text = str(text)
#         text = text.replace('–', '-')
#         text = re.sub(r'[\s/]+', '-', text)
#         text = re.sub(r'[(),{}\[\]"\'`.:;!?]', '', text)
#         text = re.sub(r'-+', '-', text).strip('-').lower()
#         return text if text else 'unnamed-entity'

#     def _discover_entities(self, all_docs: List[Dict]):
#         """Phase 0: Discover all unique entities from all documents."""
#         for doc in all_docs:
#             payload = doc.get('payload', {})
#             for concept in payload.get('concepts', []):
#                 self._extract_entities_recursive(concept)
#         logging.info(f"Discovered {len(self.all_entities)} unique entities across all documents.")

#     def _extract_entities_recursive(self, data: Dict):
#         """Recursively find and store entity definitions."""
#         if name := data.get('name'):
#             entity_id = self.normalize_symbol(name)
#             entity_type = self.normalize_symbol(data.get('concept_type') or data.get('sub_type') or 'concept')
#             if entity_id not in self.all_entities and entity_id not in self.RESERVED_TYPES:
#                 self.all_entities[entity_id] = (entity_type, name)

#         if relations := data.get('relations'):
#             for rel in relations:
#                 if target := rel.get('target'):
#                     target_id = self.normalize_symbol(target)
#                     if target_id not in self.all_entities and target_id not in self.RESERVED_TYPES:
#                         self.all_entities[target_id] = ('concept', target)
        
#         if related_concepts := data.get('related_concepts'):
#             for rel_concept in related_concepts:
#                 rel_id = self.normalize_symbol(rel_concept)
#                 if rel_id not in self.all_entities and rel_id not in self.RESERVED_TYPES:
#                     self.all_entities[rel_id] = ('concept', rel_concept)

#         if sub_concepts := data.get('sub_concepts'):
#             for sub in sub_concepts:
#                 self._extract_entities_recursive(sub)

#     def _generate_declarations(self):
#         """Phase 1: Generate a single, unified declarations block."""
#         self.declarations.append(";; --- Phase 1: Entity Declarations ---")
#         for entity_id, (entity_type, original_name) in sorted(self.all_entities.items()):
#             self.declarations.append(f"(: {entity_id} {entity_type})")
#             escaped_name = original_name.replace('"', '\\"')
#             self.declarations.append(f'(has-label {entity_id} "{escaped_name}")')

#     def _process_document(self, doc_data: Dict):
#         """Phase 2: Process a single document to generate its relations and assertions."""
#         doc_name = doc_data.get('doc_id', 'untitled-document')
#         doc_id = self.normalize_symbol(doc_name)
#         payload = doc_data.get('payload', {})
#         domain = self.normalize_symbol(payload.get('domain', 'general'))

#         self.relations.append(f'\n;;; --- Document: {doc_name} ---')
#         self.relations.append(f'(: {doc_id} Document)')
#         self.relations.append(f'(has-label {doc_id} "{doc_name}")')
#         self.relations.append(f'(has-domain {doc_id} {domain})')

#         for concept_data in payload.get('concepts', []):
#             self._process_concept(concept_data, doc_id)
    
#     def _process_concept(self, concept_data: Dict, doc_id: str, parent_id: Optional[str] = None):
#         """Process a single concept and its sub-concepts."""
#         name = concept_data.get('name')
#         if not name: return
#         concept_id = self.normalize_symbol(name)
        
#         self.relations.append(f'\n;; Concept: {name}')
#         if parent_id:
#             self.relations.append(f"(sub-concept-of {concept_id} {parent_id})")
#         else:
#             self.relations.append(f"(has-concept {doc_id} {concept_id})")

#         if explanation := concept_data.get('explanation'):
#             self.relations.append(f'(has-explanation {concept_id} "{explanation.replace("`", "").replace("`", "")}")')
        
#         # Process explicitly typed relations
#         if relations := concept_data.get('relations'):
#             for rel in relations:
#                 rel_type_info = self.relation_registry.get_relation_type(rel['type'])
#                 predicate = rel_type_info.name
#                 target_id = self.normalize_symbol(rel['target'])
#                 self.relations.append(f"({predicate} {concept_id} {target_id})")
#                 if rel_type_info.is_symmetric:
#                     self.relations.append(f"({predicate} {target_id} {concept_id})")
        
#         # Process generic related_concepts
#         if related_concepts := concept_data.get('related_concepts'):
#             for rel_concept in related_concepts:
#                 target_id = self.normalize_symbol(rel_concept)
#                 self.relations.append(f"(related-to {concept_id} {target_id})")
#                 self.relations.append(f"(related-to {target_id} {concept_id})") # related-to is always symmetric

#         self._process_assertions_and_evidence(concept_id, concept_data)

#         if sub_concepts := concept_data.get('sub_concepts', []):
#             for sub_data in sub_concepts:
#                 self._process_concept(sub_data, doc_id, parent_id=concept_id)

#     def _process_assertions_and_evidence(self, concept_id: str, concept_data: Dict):
#         """Create structured atoms for assertions and their evidence."""
#         if assertions := concept_data.get('assertions'):
#             for i, assertion in enumerate(assertions):
#                 assertion_id = f"assertion-{concept_id}-{i}"
#                 self.assertions_evidence.append(f"(: {assertion_id} Assertion)")
#                 self.assertions_evidence.append(f"(has-assertion {concept_id} {assertion_id})")
                
#                 if text := assertion.get('text'):
#                     self.assertions_evidence.append(f'(has-text {assertion_id} "{text.replace("`", "").replace("`", "")}")')
                
#                 if evidence := assertion.get('evidence'):
#                     if sources := evidence.get('sources'):
#                         for source in sources:
#                             self.assertions_evidence.append(f'(has-source {assertion_id} "{source.replace("`", "").replace("`", "")}")')
#                     if citations := evidence.get('citations'):
#                         for cit in citations:
#                             self.assertions_evidence.append(f'(has-citation {assertion_id} "{cit}")')
    
#     def _generate_rules(self):
#         """Phase 3: Generate inference rules based on relation types found."""
#         self.rules.append("\n;; --- Phase 3: Inference Rules ---")
#         transitive_preds = {t.name for t in self.relation_registry.relation_types.values() if t.is_transitive}
#         for pred in sorted(list(transitive_preds)):
#             self.rules.append(f"\n;; Rule: Transitivity for '{pred}'")
#             self.rules.append(f"(=> (And ({pred} $a $b) ({pred} $b $c))\n    ({pred} $a $c))")

#     def _generate_queries(self, all_docs: List[Dict]):
#         """Generate a diverse set of guaranteed-to-work queries."""
#         self.query_examples.append(("Find all Military Operations", "!(match &space (: $op military-operation) $op)"))
#         self.query_examples.append(("What is Béchamel made with?", "!(match &space (made-with béchamel $ingredient) $ingredient)"))
#         self.query_examples.append(("Find the text of an assertion about the Normandy Landings", 
#                                     "!(match &space (And (has-assertion normandy-landings $a) (has-text $a $text)) $text)"))
#         self.query_examples.append(("Which protocol operates at the Application Layer? (INFERENCE)", 
#                                     "!(match &space (operates-at $proto application-layer) $proto)"))
#         self.query_examples.append(("Find concepts that are synonymous with D-Day (SYMMETRY)", 
#                                     "!(match &space (synonym-of d-day $syn) $syn)"))
    
#     def _build_python_script(self) -> str:
#         """Constructs the final Python script as a string."""
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         metta_code = "\n".join(self.declarations + self.relations + self.assertions_evidence + self.rules)

#         query_blocks = []
#         for desc, query_logic in self.query_examples:
#             query_blocks.append(f'''
#     # Query: {desc}
#     print(f"\\n🔍 {desc}")
#     query = """{query_logic}"""
#     try:
#         results = runner.run(query)
#         if results and results[0]:
#             print("   Results:")
#             flat_results = []
#             for res in results:
#                 if isinstance(res, list): flat_results.extend(res)
#                 else: flat_results.append(res)
#             for result in sorted(list(set(map(str, flat_results)))):
#                 print(f"   - {{result}}")
#         else:
#             print("   - No results found.")
#     except Exception as e:
#         print(f"   - Query error: {{e}}")''')
#         query_section = "\n".join(query_blocks)

#         return f'''#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# MeTTa Knowledge Base Script
# Generated on: {timestamp}

# This script contains a unified, multi-domain knowledge base.
# It includes specific relationship types and inference rules for advanced reasoning.
# """
# from hyperon import MeTTa

# # --- MeTTa Knowledge Base ---
# METTA_CODE = """
# {metta_code}
# """

# def main():
#     """Initialize MeTTa runner and demonstrate working queries."""
#     print("🧠 Loading MeTTa knowledge base...")
#     runner = MeTTa()
    
#     try:
#         runner.run(METTA_CODE)
#         print("   ✅ Knowledge base loaded successfully.")
#     except Exception as e:
#         print(f"   ❌ Error loading knowledge base: {{e}}")
#         return
    
#     # --- Run comprehensive smoke-test queries --- {query_section}

# if __name__ == '__main__':
#     main()
# '''

#     def generate_from_jsonl(self, input_path: Path, output_path: Path):
#         """Main method to process a JSONL file and generate the Python script."""
#         logging.info(f"Starting extraction from '{input_path}'...")
        
#         try:
#             with open(input_path, 'r', encoding='utf-8') as infile:
#                 all_docs = [json.loads(line) for line in infile if line.strip()]

#             # Phase 0: Discover entities from all documents first
#             self._discover_entities(all_docs)

#             # Phase 1: Generate a single, unified declaration block
#             self._generate_declarations()

#             # Phase 2: Process each document to build relations and assertions
#             for doc_data in tqdm(all_docs, desc="Processing Documents"):
#                 self._process_document(doc_data)

#             # Phase 3: Generate rules based on all discovered relations
#             self._generate_rules()
            
#             # Phase 4: Generate a diverse set of queries
#             self._generate_queries(all_docs)

#             # Final Step: Build and write the single Python script
#             python_script = self._build_python_script()
#             output_path.write_text(python_script, encoding='utf-8')
            
#             logging.info(f"✅ Generated Python script: '{output_path}'")

#         except FileNotFoundError:
#             logging.error(f"Input file not found: '{input_path}'")
#         except Exception as e:
#             logging.error(f"An unexpected error occurred: {e}", exc_info=True)

# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(
#         description="Generate a professional Python/MeTTa knowledge base from a JSONL file.",
#         formatter_class=argparse.ArgumentDefaultsHelpFormatter
#     )
#     parser.add_argument("input_file", type=Path, help="Path to the input JSONL file")
#     parser.add_argument("-o", "--output", type=Path, default=Path("unified_metta_kb.py"),
#                         help="Path for the output Python script")
    
#     args = parser.parse_args()
    
#     generator = MettaScriptGenerator()
#     generator.generate_from_jsonl(args.input_file, args.output)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Professional-grade JSON-to-MeTTa knowledge base generator.

This script transforms domain-specific JSONL into a modular MeTTa knowledge base,
creating a separate Atomspace for each domain. It maintains a global space for
entity declarations while placing all contextual facts into their respective domain spaces.
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Professional-grade JSON-to-MeTTa knowledge base generator.

This script transforms domain-specific JSONL into a modular MeTTa knowledge base,
creating a separate Atomspace for each domain. It maintains a global space for
entity declarations while placing all contextual facts into their respective domain spaces.
"""

import json
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class RelationType:
    """Defines properties of a semantic relation."""
    name: str
    is_symmetric: bool = False
    is_transitive: bool = False

class SemanticRelationRegistry:
    """A registry to manage relation types and their logical properties."""
    def __init__(self):
        self.relation_types = {
            'sub-concept-of': RelationType('sub-concept-of', is_transitive=True),
            'part-of': RelationType('part-of', is_transitive=True),
            'is-a': RelationType('is-a', is_transitive=True),
            'synonym-of': RelationType('synonym-of', is_symmetric=True),
            'related-to': RelationType('related-to', is_symmetric=True)
        }

    def get_relation_type(self, name: str) -> RelationType:
        norm_name = name.lower().replace('_', '-')
        if norm_name not in self.relation_types:
            self.relation_types[norm_name] = RelationType(norm_name)
        return self.relation_types[norm_name]

class MettaScriptGenerator:
    """Orchestrates the conversion of JSONL to a runnable MeTTa Python script."""
    
    RESERVED_TYPES = {'concept', 'document'}

    def __init__(self):
        # ARCHITECTURAL CHOICE: Atoms are separated into a global vocabulary and domain-specific facts.
        self.global_atoms: List[str] = []
        self.domain_atoms: Dict[str, List[str]] = {}  # {domain_name: [atoms]}
        
        self.all_entities: Dict[str, Tuple[str, str]] = {}
        self.relation_registry = SemanticRelationRegistry()
        self.query_examples: List[Tuple[str, str]] = []

    @staticmethod
    def normalize_symbol(text: str) -> str:
        """Converts a string into a MeTTa-compatible symbol."""
        if not isinstance(text, str):
            text = str(text)
        text = text.replace('–', '-')
        text = re.sub(r'[\s/]+', '-', text)
        text = re.sub(r'[(),{}\[\]"\'`.:;!?]', '', text)
        text = re.sub(r'-+', '-', text).strip('-').lower()
        return text if text else 'unnamed-entity'

    def _discover_entities(self, all_docs: List[Dict]):
        """Phase 0: Discover all unique entities from all documents to build the global vocabulary."""
        for doc in all_docs:
            payload = doc.get('payload', {})
            for concept in payload.get('concepts', []):
                self._extract_entities_recursive(concept)
        logging.info(f"Discovered {len(self.all_entities)} unique entities across all documents.")

    def _extract_entities_recursive(self, data: Dict):
        """Recursively find and store entity definitions."""
        if name := data.get('name'):
            entity_id = self.normalize_symbol(name)
            entity_type = self.normalize_symbol(data.get('concept_type') or data.get('sub_type') or 'concept')
            if entity_id not in self.all_entities and entity_id not in self.RESERVED_TYPES:
                self.all_entities[entity_id] = (entity_type, name)

        if relations := data.get('relations'):
            for rel in relations:
                if target := rel.get('target'):
                    target_id = self.normalize_symbol(target)
                    if target_id not in self.all_entities and target_id not in self.RESERVED_TYPES:
                        self.all_entities[target_id] = ('concept', target)
        
        if related_concepts := data.get('related_concepts'):
            for rel_concept in related_concepts:
                rel_id = self.normalize_symbol(rel_concept)
                if rel_id not in self.all_entities and rel_id not in self.RESERVED_TYPES:
                    self.all_entities[rel_id] = ('concept', rel_concept)

        if sub_concepts := data.get('sub_concepts'):
            for sub in sub_concepts:
                self._extract_entities_recursive(sub)

    def _generate_global_declarations(self):
        """Phase 1: Generate entity declarations to be placed in the global Atomspace."""
        self.global_atoms.append(";; --- Phase 1: Global Entity Declarations ---")
        self.global_atoms.append(";; These atoms define the shared vocabulary for all domain spaces.")
        for entity_id, (entity_type, original_name) in sorted(self.all_entities.items()):
            # These atoms go into the global_atoms list. They will NOT be wrapped in add-atom.
            self.global_atoms.append(f"(: {entity_id} {entity_type})")
            escaped_name = original_name.replace('"', '\\"')
            self.global_atoms.append(f'(has-label {entity_id} "{escaped_name}")')

    def _process_document_into_domain(self, doc_data: Dict):
        """Phase 2: Process a document and add its atoms to the correct domain space collection."""
        doc_name = doc_data.get('doc_id', 'untitled-document')
        payload = doc_data.get('payload', {})
        domain = self.normalize_symbol(payload.get('domain', 'general'))
        
        self.domain_atoms.setdefault(domain, [])

        # Pass the 'domain' name down so all sub-functions know which list to add atoms to.
        for concept_data in payload.get('concepts', []):
            self._process_concept(concept_data, domain)

    def _process_concept(self, concept_data: Dict, domain: str, parent_id: Optional[str] = None):
        """Process a concept, adding its relational atoms to the specified domain's atom list."""
        name = concept_data.get('name')
        if not name: return
        concept_id = self.normalize_symbol(name)
        
        # All atoms generated here are domain-specific context.
        domain_atom_list = self.domain_atoms[domain]
        domain_atom_list.append(f'\n;; Concept: {name}')

        if parent_id:
            domain_atom_list.append(f"(sub-concept-of {concept_id} {parent_id})")
        
        if explanation := concept_data.get('explanation'):
            domain_atom_list.append(f'(has-explanation {concept_id} "{explanation.replace("`", "")}")')
        
        if relations := concept_data.get('relations'):
            for rel in relations:
                rel_type_info = self.relation_registry.get_relation_type(rel['type'])
                predicate = rel_type_info.name
                target_id = self.normalize_symbol(rel['target'])
                domain_atom_list.append(f"({predicate} {concept_id} {target_id})")
                if rel_type_info.is_symmetric:
                    domain_atom_list.append(f"({predicate} {target_id} {concept_id})")
        
        if related_concepts := concept_data.get('related_concepts'):
            for rel_concept in related_concepts:
                target_id = self.normalize_symbol(rel_concept)
                domain_atom_list.append(f"(related-to {concept_id} {target_id})")
                domain_atom_list.append(f"(related-to {target_id} {concept_id})")

        self._process_assertions_and_evidence(concept_id, concept_data, domain)

        if sub_concepts := concept_data.get('sub_concepts', []):
            for sub_data in sub_concepts:
                self._process_concept(sub_data, domain, parent_id=concept_id)

    def _process_assertions_and_evidence(self, concept_id: str, concept_data: Dict, domain: str):
        """Create structured atoms for assertions, adding them to the specified domain's atom list."""
        if assertions := concept_data.get('assertions'):
            domain_atom_list = self.domain_atoms[domain]
            for i, assertion in enumerate(assertions):
                assertion_id = f"assertion-{concept_id}-{i}"
                domain_atom_list.append(f"(: {assertion_id} Assertion)")
                domain_atom_list.append(f"(has-assertion {concept_id} {assertion_id})")
                
                if text := assertion.get('text'):
                    domain_atom_list.append(f'(has-text {assertion_id} "{text.replace("`", "")}")')
                
                if evidence := assertion.get('evidence'):
                    if sources := evidence.get('sources'):
                        for source in sources:
                            domain_atom_list.append(f'(has-source {assertion_id} "{source.replace("`", "")}")')
                    if citations := evidence.get('citations'):
                        for cit in citations:
                            domain_atom_list.append(f'(has-citation {assertion_id} "{cit}")')
    
    def _generate_global_rules(self):
        """Phase 3: Generate inference rules to be placed in the global Atomspace."""
        self.global_atoms.append("\n;; --- Phase 3: Global Inference Rules ---")
        transitive_preds = {t.name for t in self.relation_registry.relation_types.values() if t.is_transitive}
        for pred in sorted(list(transitive_preds)):
            # These rules are global and will NOT be wrapped in add-atom.
            self.global_atoms.append(f"\n;; Rule: Transitivity for '{pred}'")
            self.global_atoms.append(f"(=> (And ({pred} $a $b) ({pred} $b $c))\n    ({pred} $a $c))")

    def _generate_queries(self):
        """Generate domain-aware query examples that target specific Atomspaces."""
        self.query_examples.append(("Find all Military Operations (querying the History space)", 
                                    "!(match &history-space (: $op military-operation) $op)"))
        self.query_examples.append(("What is Béchamel made with? (querying the Culinary Arts space)", 
                                    "!(match &culinary-arts-space (made-with béchamel $ingredient) $ingredient)"))
        self.query_examples.append(("Find assertion text for Normandy Landings (querying the History space)", 
                                    "!(match &history-space (And (has-assertion normandy-landings $a) (has-text $a $text)) $text)"))
    
    def _build_python_script(self) -> str:
        """Constructs the final Python script with a modular Atomspace structure."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        metta_parts = []
        
        # Step 1: Declare all domain Atomspaces at the top level.
        metta_parts.append(";; --- Atomspace Declarations ---")
        metta_parts.append(";; Each domain gets its own space for contextual facts.")
        for domain in sorted(self.domain_atoms.keys()):
            metta_parts.append(f"(: &{domain}-space Atomspace)")
        
        # Step 2: Add global declarations and rules directly into the main space.
        # These are NOT wrapped in !(add-atom ...).
        metta_parts.extend(self.global_atoms)

        # Step 3: Add domain-specific atoms to their respective spaces using !(add-atom ...).
        # This is the core of the modular design.
        for domain, atoms in self.domain_atoms.items():
            metta_parts.append(f"\n;; --- Facts for Domain: {domain} ---")
            for atom in atoms:
                if atom.strip() and not atom.strip().startswith(';;'):
                    metta_parts.append(f"!(add-atom &{domain}-space {atom})")
                else:
                    metta_parts.append(atom)

        metta_code = "\n".join(metta_parts)

        # Build query examples
        query_blocks = []
        for desc, query_logic in self.query_examples:
            query_blocks.append(f'''
    # Query: {desc}
    print(f"\\n🔍 {desc}")
    query = """{query_logic}"""
    try:
        results = runner.run(query)
        if results and results[0]:
            print("   Results:")
            flat_results = []
            for res in results:
                if isinstance(res, list): flat_results.extend(res)
                else: flat_results.append(res)
            for result in sorted(list(set(map(str, flat_results)))):
                print(f"   - {{result}}")
        else:
            print("   - No results found.")
    except Exception as e:
        print(f"   - Query error: {{e}}")''')
        query_section = "\n".join(query_blocks)

        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeTTa Knowledge Base Script
Generated on: {timestamp}

This script contains a modular, multi-domain knowledge base, with a
separate Atomspace for each domain, and a global space for shared vocabulary.
"""
from hyperon import MeTTa

# --- MeTTa Knowledge Base ---
METTA_CODE = """
{metta_code}
"""

def main():
    """Initialize MeTTa runner and demonstrate working queries."""
    print("🧠 Loading MeTTa knowledge base with domain-specific Atomspaces...")
    runner = MeTTa()
    
    try:
        runner.run(METTA_CODE)
        print("   ✅ Knowledge base loaded successfully.")
    except Exception as e:
        print(f"   ❌ Error loading knowledge base: {{e}}")
        return
    
    # --- Run comprehensive smoke-test queries --- {query_section}

if __name__ == '__main__':
    main()
'''

    def generate_from_jsonl(self, input_path: Path, output_path: Path):
        """Main method to process a JSONL file and generate the Python script."""
        logging.info(f"Starting extraction from '{input_path}'...")
        
        try:
            with open(input_path, 'r', encoding='utf-8') as infile:
                all_docs = [json.loads(line) for line in infile if line.strip()]

            self._discover_entities(all_docs)
            self._generate_global_declarations()

            for doc_data in tqdm(all_docs, desc="Processing Documents into Domains"):
                self._process_document_into_domain(doc_data)

            self._generate_global_rules()
            self._generate_queries()

            python_script = self._build_python_script()
            output_path.write_text(python_script, encoding='utf-8')
            
            logging.info(f"✅ Generated Python script: '{output_path}'")

        except FileNotFoundError:
            logging.error(f"Input file not found: '{input_path}'")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Generate a modular Python/MeTTa knowledge base from a JSONL file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("input_file", type=Path, help="Path to the input JSONL file")
    parser.add_argument("-o", "--output", type=Path, default=Path("modular_metta_kb.py"),
                        help="Path for the output Python script")
    
    args = parser.parse_args()
    
    generator = MettaScriptGenerator()
    generator.generate_from_jsonl(args.input_file, args.output)
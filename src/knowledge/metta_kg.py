import platform
import sys
import os

if platform.system() == 'Linux':
    from hyperon import MeTTa
else:
    print("Warning: MeTTa (hyperon) only works in Linux subsystem. Please run this code in WSL.")
    sys.exit(1)

from typing import List, Dict, Any, Optional

class MeTTaKnowledgeGraph:
    def __init__(self, kb_file: str = "knowledge_base.metta"):
        """Initialize MeTTa instance and load knowledge base."""
        self.metta = MeTTa()
        if os.path.exists(kb_file):
            self.load_knowledge_base(kb_file)
            
    def load_knowledge_base(self, kb_file: str):
        """Load knowledge base from a .metta file."""
        # First ensure the knowledge base space exists
        self.metta.run('!(bind! &kb (new-space))')
        
        # Read the knowledge base file
        with open(kb_file, 'r') as f:
            kb_content = f.read()
            
        # Load the entire knowledge base at once
        # Each line in the file should be a valid MeTTa fact
        for line in kb_content.strip().split('\n'):
            if line.strip() and not line.strip().startswith('#'):
                # Add each fact individually
                self.metta.run(f'!(add-atom &kb {line.strip()})')
                
        # Verify the knowledge base was loaded
        all_atoms = self.metta.run('!(get-atoms &kb)')
        print(f"Knowledge base loaded with {len(all_atoms[0]) if all_atoms and len(all_atoms) > 0 else 0} atoms")
        
    def add_fact(self, subject: str, predicate: str, object_value: str):
        """Add a triple (fact) to the knowledge graph."""
        # First ensure the knowledge base space exists
        self.metta.run('!(bind! &kb (new-space))')
        
        # Format the fact with proper MeTTa syntax
        # In MeTTa, the syntax is: !(add-atom &space (predicate subject object))
        fact = f'!(add-atom &kb ({predicate} "{subject}" "{object_value}"))'
        print(f"Adding fact: {fact}")
        result = self.metta.run(fact)
        print(f"Add fact result: {result}")
        
        # Verify the fact was added by querying for it
        verify_query = '!(get-atoms &kb)'
        all_atoms = self.metta.run(verify_query)
        print(f"All atoms after adding fact: {all_atoms}")
        
    def query(self, subject: Optional[str] = None, 
              predicate: Optional[str] = None,
              object_value: Optional[str] = None) -> List[Dict[str, str]]:
        """Query the knowledge graph with optional subject, predicate, object patterns."""
        print(f"Querying with subject={subject}, predicate={predicate}, object_value={object_value}")
        
        # Get all atoms from the knowledge base
        all_atoms_result = self.metta.run('!(get-atoms &kb)')
        print(f"All atoms result: {all_atoms_result}")
        
        # Extract atoms from the result
        extracted_atoms = []
        if isinstance(all_atoms_result, list) and len(all_atoms_result) > 0:
            for atom in all_atoms_result[0]:
                atom_str = str(atom)
                print(f"Processing atom: {atom_str}")
                parts = atom_str.strip('()').split()
                if len(parts) == 3:
                    extracted_atoms.append({
                        'predicate': parts[0],
                        'subject': parts[1].strip('"'),
                        'object': parts[2].strip('"')
                    })
        
        print(f"Extracted atoms: {extracted_atoms}")
        
        # Filter atoms based on the query parameters
        filtered_results = []
        for atom in extracted_atoms:
            subject_match = subject is None or atom['subject'] == subject
            predicate_match = predicate is None or atom['predicate'] == predicate
            object_match = object_value is None or atom['object'] == object_value
            
            if subject_match and predicate_match and object_match:
                filtered_results.append(atom)
        
        print(f"Filtered results: {filtered_results}")
        return filtered_results

    def get_related_concepts(self, concept: str) -> List[Dict[str, str]]:
        """Get all concepts related to a given concept."""
        # Get all atoms from the knowledge base
        all_atoms_result = self.metta.run('!(get-atoms &kb)')
        
        # Extract atoms from the result
        extracted_atoms = []
        if isinstance(all_atoms_result, list) and len(all_atoms_result) > 0:
            for atom in all_atoms_result[0]:
                atom_str = str(atom)
                parts = atom_str.strip('()').split()
                if len(parts) == 3:
                    extracted_atoms.append({
                        'predicate': parts[0],
                        'subject': parts[1].strip('"'),
                        'object': parts[2].strip('"')
                    })
        
        # Filter atoms where the concept is either the subject or object
        filtered_results = []
        for atom in extracted_atoms:
            if atom['subject'] == concept or atom['object'] == concept:
                filtered_results.append(atom)
        
        return filtered_results

    def get_specific_relations(self, relation_type: str, concept: str = None) -> List[Dict[str, str]]:
        """Get all facts with a specific relation type, optionally filtered by concept."""
        # Get all atoms from the knowledge base
        all_atoms_result = self.metta.run('!(get-atoms &kb)')
        
        # Extract atoms from the result
        extracted_atoms = []
        if isinstance(all_atoms_result, list) and len(all_atoms_result) > 0:
            for atom in all_atoms_result[0]:
                atom_str = str(atom)
                parts = atom_str.strip('()').split()
                if len(parts) == 3:
                    extracted_atoms.append({
                        'predicate': parts[0],
                        'subject': parts[1].strip('"'),
                        'object': parts[2].strip('"')
                    })
        
        # Filter atoms based on the relation type and concept
        filtered_results = []
        for atom in extracted_atoms:
            if atom['predicate'] == relation_type:
                if concept is None or atom['subject'] == concept or atom['object'] == concept:
                    filtered_results.append(atom)
        
        return filtered_results

    def add_hierarchical_relationship(self, parent: str, child: str, relationship_type: str = "is_a"):
        """Add hierarchical relationships to the knowledge graph."""
        self.add_fact(child, relationship_type, parent)

    def save_knowledge_base(self, kb_file: str):
        """Save knowledge base to a .metta file."""
        # Get all atoms from the knowledge base
        all_atoms_result = self.metta.run('!(get-atoms &kb)')
        
        if not all_atoms_result or not isinstance(all_atoms_result, list) or len(all_atoms_result) == 0:
            print("No atoms to save in the knowledge base.")
            return
            
        # Extract atoms from the result
        extracted_atoms = []
        for atom in all_atoms_result[0]:
            atom_str = str(atom)
            parts = atom_str.strip('()').split()
            if len(parts) == 3:
                extracted_atoms.append(atom_str)
        
        # Write atoms to the file
        with open(kb_file, 'w') as f:
            f.write("# Medical knowledge base\n")
            for atom in extracted_atoms:
                f.write(f"{atom}\n")
                
        print(f"Knowledge base saved to {kb_file} with {len(extracted_atoms)} atoms") 
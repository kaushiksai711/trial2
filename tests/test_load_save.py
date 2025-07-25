#!/usr/bin/env python3
"""
Test script for MeTTa knowledge graph load and save functionality.
"""

import os
import sys
import platform
import shutil

# Check if running in Linux (required for MeTTa)
if platform.system() != 'Linux':
    print("Warning: MeTTa (hyperon) only works in Linux subsystem.")
    print("Please run this script in WSL (Windows Subsystem for Linux).")
    sys.exit(1)

from hyperon import MeTTa
from src.knowledge.metta_kg import MeTTaKnowledgeGraph

def main():
    """Test the load and save functionality of the MeTTa knowledge graph."""
    print("Testing MeTTa knowledge graph load and save functionality...")
    
    # Create a knowledge graph instance
    kg = MeTTaKnowledgeGraph()
    
    # Add some test facts
    print("\nAdding test facts...")
    kg.add_fact("diabetes", "is_a", "medical_condition")
    kg.add_fact("insulin", "treats", "diabetes")
    kg.add_fact("increased_thirst", "symptom_of", "diabetes")
    
    # Save the knowledge base
    test_file = "test_kb.metta"
    print(f"\nSaving knowledge base to {test_file}...")
    kg.save_knowledge_base(test_file)
    
    # Create a new knowledge graph instance
    kg2 = MeTTaKnowledgeGraph()
    
    # Load the knowledge base
    print(f"\nLoading knowledge base from {test_file}...")
    kg2.load_knowledge_base(test_file)
    
    # Query the knowledge graph
    print("\nQuerying all facts...")
    all_facts = kg2.query()
    print(f"All facts: {all_facts}")
    
    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\nRemoved test file {test_file}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main() 
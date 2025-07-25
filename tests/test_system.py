import os
from dotenv import load_dotenv
from src.db.neo4j_connector import Neo4jConnector
from src.db.qdrant_connector import QdrantConnector
from src.utils.logger import setup_logger

def test_system():
    # Load environment variables from .env file
    load_dotenv()
    
    # Set up logging
    setup_logger("test_system")
    
    # Get database credentials from environment
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    # Initialize connectors
    neo4j = Neo4jConnector(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
    qdrant = QdrantConnector(url=qdrant_url, api_key=qdrant_api_key)
    
    # Test connections
    print("\nTesting database connections...")
    if neo4j.connect():
        print("✓ Connected to Neo4j successfully")
    else:
        print("✗ Failed to connect to Neo4j")
        return
    
    if qdrant.connect():
        print("✓ Connected to Qdrant successfully")
    else:
        print("✗ Failed to connect to Qdrant")
        neo4j.disconnect()
        return
    
    # Test 1: Basic Disease Information
    print("\nTest 1: Basic Disease Information")
    diseases = neo4j.execute_query("MATCH (d:Disease) RETURN d.name as name, d.description as description LIMIT 5")
    if diseases:
        print("✓ Retrieved diseases from Neo4j:")
        for disease in diseases:
            print(f"\nDisease: {disease['name']}")
            print(f"Description: {disease['description']}")
    else:
        print("✗ Failed to retrieve diseases from Neo4j")
    
    # Test 2: Disease-Symptom Relationships
    print("\nTest 2: Disease-Symptom Relationships")
    disease_symptoms = neo4j.execute_query("""
        MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom)
        RETURN d.name as disease, collect(s.name) as symptoms
        LIMIT 3
    """)
    if disease_symptoms:
        print("✓ Retrieved disease-symptom relationships:")
        for result in disease_symptoms:
            print(f"\nDisease: {result['disease']}")
            print("Symptoms:", ", ".join(result['symptoms']))
    else:
        print("✗ Failed to retrieve disease-symptom relationships")
    
    # Test 3: Treatment Information
    print("\nTest 3: Treatment Information")
    treatments = neo4j.execute_query("""
        MATCH (d:Disease)-[:TREATED_WITH]->(t:Treatment)
        RETURN d.name as disease, t.name as treatment, t.description as description
        LIMIT 3
    """)
    if treatments:
        print("✓ Retrieved treatment information:")
        for result in treatments:
            print(f"\nDisease: {result['disease']}")
            print(f"Treatment: {result['treatment']}")
            print(f"Description: {result['description']}")
    else:
        print("✗ Failed to retrieve treatment information")
    
    
    # Clean up
    neo4j.disconnect()
    qdrant.disconnect()
    print("\nTest completed!")

if __name__ == "__main__":
    test_system() 
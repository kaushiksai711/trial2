import os
from dotenv import load_dotenv
from src.db.neo4j_connector import Neo4jConnector
from src.db.qdrant_connector import QdrantConnector
from src.db.mongodb_connector import MongoDBConnector
from src.db.cloudinary_connector import CloudinaryConnector
from src.utils.logger import setup_logger
from datetime import datetime

def populate_mongodb_data(mongodb):
    """Populate MongoDB with sample medical data"""
    try:
        # Sample user data
        user_data = {
            "user_id": "user_001",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "created_at": datetime.utcnow()
        }
        result = mongodb.insert_document("users", user_data)
        if result:
            print("  - Created user data")
        else:
            raise Exception("Failed to create user data")
        
        # Sample chat data
        chat_data = {
            "chat_id": "chat_001",
            "user_id": "user_001",
            "messages": [
                {
                    "role": "user",
                    "content": "What are the symptoms of diabetes?",
                    "timestamp": datetime.utcnow()
                },
                {
                    "role": "assistant",
                    "content": "Common symptoms of diabetes include increased thirst, frequent urination, extreme hunger, unexplained weight loss, fatigue, irritability, and blurred vision.",
                    "timestamp": datetime.utcnow()
                }
            ],
            "created_at": datetime.utcnow()
        }
        result = mongodb.insert_document("chats", chat_data)
        if result:
            print("  - Created chat data")
        else:
            raise Exception("Failed to create chat data")
        
        # Sample medical record
        medical_record = {
            "record_id": "record_001",
            "user_id": "user_001",
            "conditions": ["Type 2 Diabetes"],
            "medications": ["Metformin"],
            "allergies": ["Penicillin"],
            "created_at": datetime.utcnow()
        }
        result = mongodb.insert_document("medical_records", medical_record)
        if result:
            print("  - Created medical record")
        else:
            raise Exception("Failed to create medical record")
        
        print("✓ Successfully populated MongoDB with sample data")
        return True
    except Exception as e:
        print(f"✗ Failed to populate MongoDB: {str(e)}")
        return False
def test_all_connections():
    # Load environment variables from .env file
    load_dotenv()
    
    # Set up logging
    setup_logger("test_connections")
    
    # Get database credentials from environment
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    mongodb_uri = os.getenv("MONGODB_URI")
    mongodb_db_name = os.getenv("MONGODB_DB_NAME")
    
    cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY")
    cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET")
    
    # Initialize connectors
    print("\nInitializing database connectors...")
    
    # Neo4j Connection Test
    print("\nTesting Neo4j connection...")
    neo4j = Neo4jConnector(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
    if neo4j.connect():
        print("✓ Connected to Neo4j successfully")
        # Test a simple query
        diseases = neo4j.execute_query("MATCH (d:Disease) RETURN d.name as name LIMIT 1")
        if diseases:
            print(f"  - Retrieved sample disease: {diseases[0]['name']}")
        neo4j.disconnect()
    else:
        print("✗ Failed to connect to Neo4j")
    
    # Qdrant Connection Test
    print("\nTesting Qdrant connection...")
    qdrant = QdrantConnector(url=qdrant_url, api_key=qdrant_api_key)
    if qdrant.connect():
        print("✓ Connected to Qdrant successfully")
        # Test a simple search
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_vector = model.encode("diabetes").tolist()
        results = qdrant.search(query_vector, limit=1)
        if results:
            print(f"  - Retrieved sample result: {results[0]['payload']['name']}")
        qdrant.disconnect()
    else:
        print("✗ Failed to connect to Qdrant")
    
    # MongoDB Connection Test
    print("\nTesting MongoDB connection...")
    try:
        mongodb = MongoDBConnector(uri=mongodb_uri, db_name=mongodb_db_name)
        if mongodb.connect():
            print("✓ Connected to MongoDB successfully")
            # Populate sample data
            if populate_mongodb_data(mongodb) is not None:
                # Test retrieving data
                users = mongodb.get_collection("users").find_one()
                if users:
                    print("  - Retrieved sample user data")
                    print(f"    Name: {users['name']}")
                    print(f"    Email: {users['email']}")
                
                chats = mongodb.get_collection("chats").find_one()
                if chats:
                    print("  - Retrieved sample chat data")
                    print(f"    Chat ID: {chats['chat_id']}")
                    print(f"    Messages: {len(chats['messages'])}")
                
                medical_records = mongodb.get_collection("medical_records").find_one()
                if medical_records:
                    print("  - Retrieved sample medical record")
                    print(f"    Conditions: {', '.join(medical_records['conditions'])}")
                    print(f"    Medications: {', '.join(medical_records['medications'])}")
            
            mongodb.disconnect()
        else:
            print("✗ Failed to connect to MongoDB")
    except Exception as e:
        print(f"✗ Error testing MongoDB connection: {str(e)}")
    
    # Cloudinary Connection Test
    print("\nTesting Cloudinary connection...")
    cloudinary = CloudinaryConnector(
        cloud_name=cloudinary_cloud_name,
        api_key=cloudinary_api_key,
        api_secret=cloudinary_api_secret
    )
    if cloudinary.connect():
        print("✓ Connected to Cloudinary successfully")
        # Test uploading a small test image
        try:
            result = cloudinary.upload_test_image()
            print(f"  - Uploaded test image: {result['url']}")
            # Clean up
            cloudinary.delete_image(result['public_id'])
            print("  - Cleaned up test image")
        except Exception as e:
            print(f"  - Test upload failed: {str(e)}")
    else:
        print("✗ Failed to connect to Cloudinary")
    
    print("\nAll connection tests completed!")

if __name__ == "__main__":
    test_all_connections() 
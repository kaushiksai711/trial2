"""
Qdrant vector database connector for semantic search.

This module provides a connector for the Qdrant vector database,
enabling semantic search capabilities for the medical chatbot.
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from src.utils.logger import setup_logger
import os

class QdrantConnector:
    """
    Connector for Qdrant vector database.
    
    This class handles all interactions with the Qdrant vector database,
    including connection management, collection operations, and vector search.
    """
    
    def __init__(self, url: str = None, api_key: str = None):
        """
        Initialize the Qdrant connector with configuration from parameters or environment variables.
        
        Args:
            url: Optional Qdrant server URL. If not provided, reads from QDRANT_URL env var
            api_key: Optional Qdrant API key. If not provided, reads from QDRANT_API_KEY env var
        """
        self.logger = setup_logger("qdrant_connector")
        self.client = None
        self.connected = False
        
        # Get configuration from parameters or environment variables
        self.url = url or os.getenv("QDRANT_URL", "https://90c18eba-c9f7-489f-9371-b46eea57639f.eu-central-1-0.aws.cloud.qdrant.io:6333")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.9n7a9Lqq9lUcJqppvoLQ0bb24bkhRAkx3Mvj3pIXs8k")
        self.collection_name = os.getenv("QDRANT_COLLECTION", "medical_knowledge")
        print(self.url,self.api_key)
        # Vector configuration
        self.vector_size = 384  # Size for all-MiniLM-L6-v2 embeddings
        self.distance = models.Distance.COSINE
        
        # ID mapping to track string IDs to integer IDs
        self.id_mapping = {}
        
        self.logger.info(f"Initializing Qdrant connector with URL: {self.url}")
    
    def connect(self) -> bool:
        """
        Establish connection to Qdrant server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Initialize Qdrant client with proper configuration
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=30.0,  # Increased timeout for initial connection
                  # Use gRPC for better performance
            )
            
            # Verify connection by getting collections
            collections = self.client.get_collections()
            self.logger.info(f"Connected to Qdrant. Found {len(collections.collections)} collections.")
            
            # Create collection if it doesn't exist
            if not any(c.name == self.collection_name for c in collections.collections):
                self._create_collection()
            
            self.connected = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Qdrant: {str(e)}")
            self.connected = False
            return False
    
    def _create_collection(self) -> None:
        """
        Create the medical knowledge collection if it doesn't exist.
        """
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=self.distance
                )
            )
            self.logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to create collection: {str(e)}")
            raise
    
    def is_connected(self) -> bool:
        """
        Check if the connector is connected to Qdrant.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.connected or self.client is None:
            return False
            
        try:
            # Simple health check
            self.client.get_collections()
            return True
        except Exception:
            self.connected = False
            return False
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the collection.
        
        Args:
            query_vector: The query vector to search with
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of search results with scores and payloads
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Qdrant")
        
        try:
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            return [
                {
                    "id": self.id_mapping.get(result.id, str(result.id)),
                    "score": result.score,
                    "payload": {
                        "name": result.payload.get("name", "Unknown"),
                        "description": result.payload.get("description", ""),
                        **result.payload
                    }
                }
                for result in search_results
            ]
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            raise
    
    def add_points(
        self,
        points: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> None:
        """
        Add points to the collection in batches.
        
        Args:
            points: List of points to add, each containing id, vector, and payload
            batch_size: Number of points to add in each batch
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Qdrant")
        
        try:
            # Convert points to Qdrant format
            qdrant_points = []
            for point in points:
                original_id = point["id"]
                int_id = self._convert_id_to_int(original_id)
                
                # Store the mapping
                self.id_mapping[int_id] = original_id
                
                qdrant_points.append(
                    models.PointStruct(
                        id=int_id,
                        vector=point["vector"],
                        payload=point["payload"]
                    )
                )
            
            # Add points in batches
            for i in range(0, len(qdrant_points), batch_size):
                batch = qdrant_points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            
            self.logger.info(f"Added {len(points)} points to collection")
            
        except Exception as e:
            self.logger.error(f"Failed to add points: {str(e)}")
            raise
    
    def _convert_id_to_int(self, id_value: Any) -> int:
        """
        Convert an ID to an integer for Qdrant compatibility.
        
        Args:
            id_value: The ID to convert
            
        Returns:
            An integer ID
        """
        if isinstance(id_value, int):
            return id_value
        
        # Convert string to integer using hash
        return abs(hash(str(id_value))) % (2**63)  # Ensure it's a positive 64-bit integer
    
    def delete_points(self, point_ids: List[str]) -> None:
        """
        Delete points from the collection.
        
        Args:
            point_ids: List of point IDs to delete
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Qdrant")
        
        try:
            # Convert string IDs to integers
            int_point_ids = []
            for pid in point_ids:
                int_id = self._convert_id_to_int(pid)
                int_point_ids.append(int_id)
                # Remove from mapping
                if int_id in self.id_mapping:
                    del self.id_mapping[int_id]
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=int_point_ids
                )
            )
            self.logger.info(f"Deleted {len(point_ids)} points from collection")
            
        except Exception as e:
            self.logger.error(f"Failed to delete points: {str(e)}")
            raise
    
    def close(self) -> None:
        """
        Close the connection to Qdrant.
        """
        if self.client:
            self.client.close()
            self.connected = False
            self.logger.info("Closed connection to Qdrant")
    
    def disconnect(self) -> None:
        """
        Disconnect from Qdrant. Alias for close() to maintain consistency with other connectors.
        """
        self.close()
        
    def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        """
        Upsert a single point to the collection.
        
        Args:
            id: The ID of the point
            vector: The vector embedding
            metadata: The metadata payload
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Qdrant")
        
        try:
            # Convert ID to integer
            int_id = self._convert_id_to_int(id)
            
            # Store the mapping
            self.id_mapping[int_id] = id
            
            # Create point
            point = models.PointStruct(
                id=int_id,
                vector=vector,
                payload=metadata
            )
            
            # Upsert point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            self.logger.info(f"Upserted point with ID: {id}")
            
        except Exception as e:
            self.logger.error(f"Failed to upsert point: {str(e)}")
            raise

trial=QdrantConnector()
trial.connect()

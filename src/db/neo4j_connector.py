"""
Neo4j connector for graph database functionality.

This module provides a real implementation of a Neo4j connector
that connects to a Neo4j database instance.
"""

import logging
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class Neo4jConnector:
    """
    Connector for Neo4j graph database.
    
    Responsibilities:
    - Connect to Neo4j database
    - Execute Cypher queries
    - Manage database transactions
    - Provide methods for common graph operations
    """
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        Initialize the Neo4j connector.
        
        Args:
            uri: Neo4j database URI
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
        self.connected = False
        
        logger.info(f"Initializing Neo4j connector to {self.uri}")
        
        # Connect and set up medical data
        if self.connect():
            self.execute_medical_data_setup()
    
    def is_connected(self) -> bool:
        """
        Check if the connector is connected to Neo4j.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected and self.driver is not None
    
    def connect(self) -> bool:
        """
        Connect to Neo4j database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.driver:
                self.driver.close()
                
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50
            )
            
            # Verify connection
            with self.driver.session() as session:
                session.run("RETURN 1")
                
            self.connected = True
            logger.info("Successfully connected to Neo4j")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            self.connected = False
            if self.driver:
                self.driver.close()
                self.driver = None
            return False
    
    def disconnect(self) -> None:
        """
        Disconnect from Neo4j database.
        """
        if self.driver:
            self.driver.close()
            self.driver = None
            self.connected = False
            logger.info("Disconnected from Neo4j")
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query.
        
        Args:
            query: Cypher query string
            params: Optional parameters for the query
            
        Returns:
            Query results as a list of dictionaries
        """
        if not self.connected or not self.driver:
            logger.warning("Not connected to Neo4j")
            return []
        
        logger.debug(f"Executing query: {query}")
        if params:
            logger.debug(f"With parameters: {params}")
        
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                records = [record.data() for record in result]
                logger.debug(f"Query returned {len(records)} records")
                return records
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            return []
    
    def create_entity(self, labels: List[str], properties: Dict[str, Any]) -> Optional[str]:
        """
        Create a new entity node.
        
        Args:
            labels: List of node labels
            properties: Node properties
            
        Returns:
            ID of the created node, or None if creation failed
        """
        if not self.connected:
            logger.warning("Not connected to Neo4j")
            return None
        
        labels_str = ':'.join(labels)
        query = f"""
        CREATE (n:{labels_str} $properties)
        RETURN n.id as id
        """
        
        try:
            results = self.execute_query(query, {"properties": properties})
            if results and 'id' in results[0]:
                return results[0]['id']
        except Exception as e:
            logger.error(f"Error creating entity: {str(e)}")
        
        return None
    
    def create_relationship(self, from_id: str, to_id: str, rel_type: str, 
                            properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a relationship between two nodes.
        
        Args:
            from_id: ID of the source node
            to_id: ID of the target node
            rel_type: Relationship type
            properties: Optional relationship properties
            
        Returns:
            True if relationship created successfully
        """
        if not self.connected:
            logger.warning("Not connected to Neo4j")
            return False
        
        query = """
        MATCH (a), (b)
        WHERE a.id = $from_id AND b.id = $to_id
        CREATE (a)-[r:`{}`]->(b)
        SET r = $properties
        RETURN type(r) as type
        """.format(rel_type)
        
        try:
            results = self.execute_query(query, {
                "from_id": from_id,
                "to_id": to_id,
                "properties": properties or {}
            })
            return len(results) > 0
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            return False
    
    def find_entity_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Find an entity by its ID.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity data or None if not found
        """
        if not self.connected:
            logger.warning("Not connected to Neo4j")
            return None
        
        query = """
        MATCH (n {id: $id})
        RETURN n
        """
        
        try:
            results = self.execute_query(query, {"id": entity_id})
            if results and 'n' in results[0]:
                return results[0]['n']
            return None
        except Exception as e:
            logger.error(f"Error finding entity: {str(e)}")
            return None
    
    def find_entity_by_property(self, prop_name: str, prop_value: Any) -> List[Dict[str, Any]]:
        """
        Find entities by a specific property value.
        
        Args:
            prop_name: Property name
            prop_value: Property value to match
            
        Returns:
            List of matching entities
        """
        if not self.connected:
            logger.warning("Not connected to Neo4j")
            return []
        
        query = f"""
        MATCH (n)
        WHERE n.{prop_name} = $value
        RETURN n
        """
        
        try:
            results = self.execute_query(query, {"value": prop_value})
            return [record['n'] for record in results]
        except Exception as e:
            logger.error(f"Error finding entity by property: {str(e)}")
            return []
    
    def get_relationships(self, entity_id: str, rel_types: Optional[List[str]] = None, 
                         direction: str = "both") -> List[Dict[str, Any]]:
        """
        Get relationships for an entity.
        
        Args:
            entity_id: Entity ID
            rel_types: Optional list of relationship types to filter
            direction: "outgoing", "incoming", or "both"
            
        Returns:
            List of relationships
        """
        if not self.connected:
            logger.warning("Not connected to Neo4j")
            return []
        
        # Build relationship type filter
        rel_filter = ""
        if rel_types and len(rel_types) > 0:
            rel_filter = ":" + "|:".join(rel_types)
        
        # Build query based on direction
        if direction == "outgoing":
            query = f"""
            MATCH (a {{id: $id}})-[r{rel_filter}]->(b)
            RETURN a, r, b
            """
        elif direction == "incoming":
            query = f"""
            MATCH (a)-[r{rel_filter}]->(b {{id: $id}})
            RETURN a, r, b
            """
        else:  # both
            query = f"""
            MATCH (a {{id: $id}})-[r{rel_filter}]-(b)
            RETURN a, r, b
            """
        
        try:
            results = self.execute_query(query, {"id": entity_id})
            relationships = []
            
            for record in results:
                source = record['a']
                target = record['b']
                relationship = record['r']
                
                rel_data = {
                    'source': source['id'],
                    'source_data': source,
                    'target': target['id'],
                    'target_data': target,
                    'type': relationship.type,
                    'properties': dict(relationship)
                }
                
                relationships.append(rel_data)
            
            return relationships
        except Exception as e:
            logger.error(f"Error getting relationships: {str(e)}")
            return []
    
    def execute_medical_data_setup(self) -> bool:
        """
        Set up medical data schema and constraints.
        
        Returns:
            True if setup successful
        """
        if not self.connected:
            logger.warning("Not connected to Neo4j")
            return False
        
        # Create constraints and indexes
        queries = [
            # Create constraints
            """CREATE CONSTRAINT entity_id IF NOT EXISTS
               FOR (n:Entity) REQUIRE n.id IS UNIQUE""",
            
            """CREATE CONSTRAINT disease_id IF NOT EXISTS
               FOR (d:Disease) REQUIRE d.id IS UNIQUE""",
            
            """CREATE CONSTRAINT symptom_id IF NOT EXISTS
               FOR (s:Symptom) REQUIRE s.id IS UNIQUE""",
            
            """CREATE CONSTRAINT treatment_id IF NOT EXISTS
               FOR (t:Treatment) REQUIRE t.id IS UNIQUE""",
            
            """CREATE CONSTRAINT medication_id IF NOT EXISTS
               FOR (m:Medication) REQUIRE m.id IS UNIQUE""",
            
            # Create indexes
            """CREATE INDEX entity_name IF NOT EXISTS
               FOR (n:Entity) ON (n.name)""",
            
            """CREATE INDEX disease_name IF NOT EXISTS
               FOR (d:Disease) ON (d.name)"""
        ]
        
        success = True
        for query in queries:
            try:
                self.execute_query(query)
            except Exception as e:
                logger.error(f"Error setting up schema: {str(e)}")
                success = False
        
        # Populate sample data
        if success:
            success = self.populate_sample_data()
            
        return success
        
    def populate_sample_data(self) -> bool:
        """
        Populate the database with sample medical data.
        
        Returns:
            True if population successful
        """
        if not self.connected:
            logger.warning("Not connected to Neo4j")
            return False
            
        try:
            # Create sample diseases with symptoms
            sample_data_query = """
            // Create diseases
            CREATE (d1:Disease {id: 'D1', name: 'Type 2 Diabetes', description: 'A chronic condition affecting blood sugar levels'})
            CREATE (d2:Disease {id: 'D2', name: 'Hypertension', description: 'High blood pressure condition'})
            CREATE (d3:Disease {id: 'D3', name: 'Asthma', description: 'Chronic respiratory condition'})
            
            // Create symptoms
            CREATE (s1:Symptom {id: 'S1', name: 'Increased thirst', description: 'Feeling thirsty more often than usual'})
            CREATE (s2:Symptom {id: 'S2', name: 'Frequent urination', description: 'Need to urinate more often'})
            CREATE (s3:Symptom {id: 'S3', name: 'Fatigue', description: 'Feeling tired and weak'})
            CREATE (s4:Symptom {id: 'S4', name: 'Headache', description: 'Pain in the head'})
            CREATE (s5:Symptom {id: 'S5', name: 'Shortness of breath', description: 'Difficulty breathing'})
            
            // Create treatments
            CREATE (t1:Treatment {id: 'T1', name: 'Insulin therapy', description: 'Regular insulin injections to control blood sugar'})
            CREATE (t2:Treatment {id: 'T2', name: 'Metformin', description: 'Oral medication to lower blood sugar levels'})
            CREATE (t3:Treatment {id: 'T3', name: 'ACE inhibitors', description: 'Medication to lower blood pressure'})
            CREATE (t4:Treatment {id: 'T4', name: 'Beta blockers', description: 'Medication to reduce heart rate and blood pressure'})
            CREATE (t5:Treatment {id: 'T5', name: 'Inhaled corticosteroids', description: 'Medication to reduce airway inflammation'})
            CREATE (t6:Treatment {id: 'T6', name: 'Bronchodilators', description: 'Medication to open airways'})
            
            // Create relationships between diseases and symptoms
            CREATE (d1)-[:HAS_SYMPTOM]->(s1)
            CREATE (d1)-[:HAS_SYMPTOM]->(s2)
            CREATE (d1)-[:HAS_SYMPTOM]->(s3)
            CREATE (d2)-[:HAS_SYMPTOM]->(s4)
            CREATE (d2)-[:HAS_SYMPTOM]->(s3)
            CREATE (d3)-[:HAS_SYMPTOM]->(s5)
            CREATE (d3)-[:HAS_SYMPTOM]->(s3)
            
            // Create relationships between diseases and treatments
            CREATE (d1)-[:TREATED_WITH]->(t1)
            CREATE (d1)-[:TREATED_WITH]->(t2)
            CREATE (d2)-[:TREATED_WITH]->(t3)
            CREATE (d2)-[:TREATED_WITH]->(t4)
            CREATE (d3)-[:TREATED_WITH]->(t5)
            CREATE (d3)-[:TREATED_WITH]->(t6)
            """
            
            # First, clear existing data
            self.execute_query("MATCH (n) DETACH DELETE n")
            
            # Then create new sample data
            self.execute_query(sample_data_query)
            
            logger.info("Successfully populated sample medical data")
            return True
            
        except Exception as e:
            logger.error(f"Error populating sample data: {str(e)}")
            return False 
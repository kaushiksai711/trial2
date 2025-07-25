"""
Query Interpreter for understanding user queries.

This module contains the implementation of the query interpreter
which is responsible for understanding user queries and extracting
relevant entities, intents, and other information.
"""

from typing import Dict, Any, List
#from utils.logger import setup_logger
import spacy

class QueryInterpreter:
    """
    Agent responsible for interpreting user queries.
    
    Responsibilities:
    - Extract entities and keywords from user queries
    - Identify question type and intent
    - Detect query complexity
    - Prepare the query for retrieval operations
    """
    
    def __init__(self):
        """
        Initialize the query interpreter with NLP model
        """
        self.nlp = spacy.load("en_core_web_sm")
        self.logger = setup_logger("query_interpreter")
        
        # Define intent patterns
        self.intent_patterns = {
            "symptoms": ["symptom", "sign", "manifestation", "indication"],
            "diagnosis": ["diagnose", "cause", "reason", "why"],
            "treatment": ["treat", "cure", "medicine", "therapy", "medication"],
            "prevention": ["prevent", "avoid", "protection", "prophylaxis"],
            "information": ["what", "how", "when", "where", "who"]
        }
        
        # Define medical entity patterns
        self.medical_entities = [
            # General medical terms
            "disease", "condition", "symptom", "treatment", "medication",
            "virus", "viruses", "bacteria", "infection", "syndrome", "disorder",
            
            # Common symptoms
            "fever", "pain", "cough", "headache", "fatigue", "nausea",
            "dizziness", "rash", "inflammation",
            
            # Common diseases
            "diabetes", "asthma", "cancer", "flu", "cold", "covid-19",
            "pneumonia", "bronchitis", "malaria", "hypertension",
            
            # Medications
            "aspirin", "ibuprofen", "paracetamol", "antibiotic",
            
            # Body parts
            "heart", "lung", "liver", "kidney", "brain", "stomach",
            
            # Compound terms
            "heart disease", "lung cancer", "blood pressure",
            "immune system", "respiratory system"
        ]
    
    async def interpret(self, query: str) -> Dict[str, Any]:
        """
        Interpret a user query to understand intent and extract entities.
        
        Args:
            query: The user's query string
            
        Returns:
            Dict containing interpretation results including:
            - intent: The primary intent of the query
            - entities: List of extracted entities
            - query_type: Type of query (factual, comparative, causal, temporal)
            - original_query: The original query
        """
        try:
            if not query:
                return {
                    "error": "Empty query provided",
                    "query": query
                }
            
            if not isinstance(query, str):
                return {
                    "error": f"Invalid query type: {type(query)}",
                    "query": query
                }
            
            # Process query with NLP model
            doc = self.nlp(query)
            
            # Extract entities using both NER and pattern matching
            entities = self._extract_entities(doc)
            
            # Determine query type
            query_type = self._determine_query_type(doc)
            
            # Extract intent
            intent = self._extract_intent(doc)
            
            interpretation = {
                "intent": intent,
                "entities": entities,
                "query_type": query_type,
                "original_query": query
            }
            
            self.logger.info(f"Interpreted query: {interpretation}")
            return interpretation
            
        except Exception as e:
            self.logger.error(f"Error interpreting query: {str(e)}")
            return {
                "error": str(e),
                "query": query
            }
    
    def _determine_query_type(self, doc) -> str:
        """Determine the type of query based on linguistic patterns"""
        # Check for comparative patterns
        if any(token.text.lower() in ["vs", "versus", "compared", "compare"] for token in doc):
            return "comparative"
        
        # Check for causal patterns
        if any(token.dep_ == "mark" and token.text.lower() in ["because", "since", "as"] for token in doc):
            return "causal"
        
        # Check for temporal patterns
        if any(token.dep_ == "advmod" and token.text.lower() in ["when", "how long"] for token in doc):
            return "temporal"
        
        # Check for causal patterns in the text (not just dependency parsing)
        query_text = doc.text.lower()
        if any(word in query_text for word in ["because", "since", "as", "due to", "caused by", "why"]):
            return "causal"
        
        # Default to factual
        return "factual"
    
    def _extract_intent(self, doc) -> str:
        """Extract the primary intent from the query"""
        # Convert query to lowercase for matching
        query_text = doc.text.lower()
        
        # Check for temporal patterns first
        if any(token.dep_ == "advmod" and token.text.lower() in ["when", "how long"] for token in doc):
            return "information"
        
        # Check for specific intent patterns
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in query_text for pattern in patterns):
                return intent
        
        # Check for symptom-related patterns
        if "symptom" in query_text or "sign" in query_text:
            return "symptoms"
        
        # Check for treatment-related patterns
        if "treat" in query_text or "cure" in query_text or "medicine" in query_text:
            return "treatment"
        
        # Default to information
        return "information"
    
    def _extract_entities(self, doc) -> List[str]:
        """Extract medical entities from the query using NER and pattern matching"""
        entities = []
        
        # Extract named entities from spaCy
        for ent in doc.ents:
            if ent.label_ in ["DISEASE", "ORG", "PRODUCT"]:
                # Preserve original case for entities like COVID-19
                entities.append(ent.text)
        
        # Pattern matching for medical terms
        text = doc.text.lower()
        
        # Check for compound terms first
        for entity in self.medical_entities:
            if " " in entity and entity in text:
                entities.append(entity)
        
        # Then check individual tokens
        for token in doc:
            token_text = token.text.lower()
            # Check if token is a medical entity
            if token_text in self.medical_entities:
                # Use original case from the text
                entities.append(token.text)
            # Check compound words (e.g., "heart disease")
            if token.dep_ == "compound":
                compound = f"{token.text} {token.head.text}".lower()
                if compound in self.medical_entities:
                    # Use original case from the text
                    entities.append(f"{token.text} {token.head.text}")
        
        # Remove duplicates while preserving order and case
        seen = set()
        result = []
        for entity in entities:
            if entity.lower() not in seen:
                seen.add(entity.lower())
                result.append(entity)
        return result
    
    def _identify_intent(self, query):
        """
        Identify the intent of the user query.
        
        Args:
            query: Raw user query as a string
            
        Returns:
            Dictionary with intent type and confidence
        """
        # Mock implementation for Phase 1
        # In a real implementation, this would use a classifier
        
        # Simple rule-based intent detection
        query_lower = query.lower()
        
        if "what is" in query_lower or "definition" in query_lower:
            return {"type": "definition", "confidence": 0.8}
        elif "how does" in query_lower or "how to" in query_lower:
            return {"type": "explanation", "confidence": 0.8}
        elif "why" in query_lower:
            return {"type": "reason", "confidence": 0.7}
        elif "compare" in query_lower or "difference between" in query_lower:
            return {"type": "comparison", "confidence": 0.8}
        else:
            return {"type": "information", "confidence": 0.5}
    
    def _assess_complexity(self, query, entities):
        """
        Assess the complexity of the query.
        
        Args:
            query: Raw user query as a string
            entities: Extracted entities
            
        Returns:
            Complexity assessment ("simple" or "complex")
        """
        # Simple heuristic for Phase 1
        # In a real implementation, this would be more sophisticated
        
        words = query.split()
        
        if len(words) > 15 or len(entities) > 2:
            return "complex"
        else:
            return "simple" 
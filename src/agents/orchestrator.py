"""
Orchestrator module for coordinating workflow between agents.

This module contains the main orchestrator class that coordinates
the interaction between the query interpreter, retrieval agent,
and renderer components.
"""

from typing import Dict, Any
from src.utils.logger import setup_logger
from src.agents.query_interpreter import QueryInterpreter
from src.agents.query_decomposer import QueryDecomposer
from src.agents.retrieval_agent import RetrievalAgent

class Orchestrator:
    """
    Orchestrator class for coordinating the workflow between different agents.
    
    Responsibilities:
    - Coordinate the workflow between query interpreter and retrieval agent
    - Manage the processing pipeline for user queries
    - Control the flow of information between components
    - Deliver final responses using appropriate renderers
    """
    
    def __init__(self, query_interpreter: QueryInterpreter, query_decomposer: QueryDecomposer, retrieval_agent: RetrievalAgent):
        """Initialize the orchestrator with required agents"""
        self.query_interpreter = query_interpreter
        self.query_decomposer = query_decomposer
        self.retrieval_agent = retrieval_agent
        self.logger = setup_logger("orchestrator")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query through the workflow.
        
        Args:
            query: The user's query string
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            # Interpret the query
            interpretation = await self.query_interpreter.interpret(query)
            
            # If query is complex, decompose it
            if interpretation.get("is_complex", False):
                sub_queries = await self.query_interpreter.decompose_query(query)
                responses = []
                
                for sub_query in sub_queries:
                    # Process each sub-query
                    knowledge = await self.retrieval_agent.retrieve(sub_query)
                    if knowledge.get("status") == "success":
                        responses.append(self._format_response(knowledge))
                
                return {
                    "status": "success",
                    "response": "\n\n".join(responses),
                    "metadata": {
                        "original_query": query,
                        "interpretation": interpretation,
                        "sub_queries": sub_queries
                    }
                }
            
            # Process single query
            knowledge = await self.retrieval_agent.retrieve(query)
            
            if knowledge.get("status") == "success":
                response = self._format_response(knowledge)
                return {
                    "status": "success",
                    "response": response,
                    "metadata": {
                        "original_query": query,
                        "interpretation": interpretation
                    }
                }
            else:
                return {
                    "status": "error",
                    "response": "Error processing query",
                    "error": knowledge.get("error", "Unknown error")
                }
                
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {
                "status": "error",
                "response": "Error processing query",
                "error": str(e)
            }
            
    def _format_response(self, knowledge: Dict[str, Any]) -> str:
        """
        Format the knowledge into a readable response.
        
        Args:
            knowledge: Dict containing retrieved knowledge
            
        Returns:
            Formatted response string
        """
        if not knowledge.get("knowledge"):
            return "No information found."
            
        knowledge_data = knowledge["knowledge"]
        
        # If knowledge is a list of results
        if isinstance(knowledge_data, list):
            formatted_responses = []
            
            for item in knowledge_data:
                if isinstance(item, dict):
                    content = item.get("content", "")
                    metadata = item.get("metadata", {})
                    source = item.get("source", "unknown")
                    
                    # Try to parse content if it's a string representation of a dict
                    try:
                        if isinstance(content, str) and content.startswith("{"):
                            content_dict = eval(content)
                            if isinstance(content_dict, dict):
                                # Format disease information
                                if "disease" in content_dict and "description" in content_dict:
                                    response = f"{content_dict['disease']}: {content_dict['description']}"
                                    
                                    # Add relationships if present
                                    if "relationships" in content_dict:
                                        for rel in content_dict["relationships"]:
                                            if isinstance(rel, dict):
                                                rel_type = rel.get("type", "")
                                                rel_node = rel.get("node", {})
                                                if rel_type and rel_node:
                                                    node_name = rel_node.get("name", "")
                                                    node_desc = rel_node.get("description", "")
                                                    if node_name and node_desc:
                                                        response += f"\n{rel_type}: {node_name} - {node_desc}"
                                    
                                    formatted_responses.append(response)
                                else:
                                    formatted_responses.append(str(content_dict))
                            else:
                                formatted_responses.append(content)
                        else:
                            formatted_responses.append(content)
                    except:
                        formatted_responses.append(content)
                else:
                    formatted_responses.append(str(item))
            
            # Join all responses with newlines
            return "\n\n".join(formatted_responses)
        
        # If knowledge is a string
        return str(knowledge_data) 
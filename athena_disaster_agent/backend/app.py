from dotenv import load_dotenv
import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from hyperon import MeTTa
from hyperon.ext import register_tokens
from hyperon import *

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Athena Multi-Domain Expert System", version="2.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    success: bool
    domain: str
    expert_name: str
    error: str = None

class KnowledgeGraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = {}

class KnowledgeGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    properties: Dict[str, Any] = {}

class KnowledgeGraphResponse(BaseModel):
    nodes: list[KnowledgeGraphNode]
    links: list[KnowledgeGraphEdge]
    success: bool
    error: str = None

class HealthResponse(BaseModel):
    status: str
    message: str
    domains_active: Dict[str, bool]

# Global variables
domain_agents = {}
DOMAINS = {
    "disaster": {
        "name": "🚨 Athena - Disaster Specialist",
        "file": "domains/disaster.msa",
        "theme": {"primary": "#dc2626", "secondary": "#ea580c"}
    },
    "healthcare": {
        "name": "🩺 Dr. Athena - Medical Advisor", 
        "file": "domains/healthcare.msa",
        "theme": {"primary": "#2563eb", "secondary": "#16a34a"}
    },
    "legal": {
        "name": "⚖️ Attorney Athena - Legal Consultant",
        "file": "domains/legal.msa", 
        "theme": {"primary": "#1e40af", "secondary": "#b45309"}
    }
}

def initialize_domain_agents():
    """Initialize all MeTTa domain agents"""
    global domain_agents
    
    # Check if OpenRouter API key exists
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if not openrouter_key:
        logger.error("❌ OPENROUTER_API_KEY environment variable not found")
        return False
    
    logger.info("✅ OpenRouter API key loaded")
    
    try:
        for domain, config in DOMAINS.items():
            logger.info(f"🔄 Initializing {domain} agent...")
            
            # Create MeTTa instance
            agent = MeTTa()
            
            # Import motto
            agent.run("!(import! &self motto)") #Importing motto
            
            # Load domain-specific agent
            bind_command = f'!(bind! &chat (dialog-agent "{config["file"]}"))' #binding command
            result = agent.run(bind_command)
            
            # Store agent
            domain_agents[domain] = agent
            logger.info(f"✅ {config['name']} initialized successfully")
        
        logger.info("🔥 All domain agents ready!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize domain agents: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("🚨 Starting Athena Multi-Domain Expert System")
    
    if initialize_domain_agents():
        logger.info("📱 System ready at: http://localhost:8000")
    else:
        logger.error("💥 Failed to initialize system")

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Athena Multi-Domain Expert System",
        "version": "2.0",
        "domains": list(DOMAINS.keys()),
        "status": "active"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    domains_status = {}
    
    for domain in DOMAINS:
        domains_status[domain] = domain in domain_agents and domain_agents[domain] is not None
    
    all_healthy = all(domains_status.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        message="Multi-domain system operational" if all_healthy else "Some domains unavailable",
        domains_active=domains_status
    )

@app.get("/domains", response_model=Dict[str, Any])
async def get_domains():
    """Get available domains and their information"""
    return {
        "domains": DOMAINS,
        "active_domains": list(domain_agents.keys())
    }

@app.post("/chat/{domain}", response_model=ChatResponse)
async def chat_endpoint(domain: str, message: ChatMessage):
    """Chat with specific domain expert"""
    
    # Validate domain
    if domain not in DOMAINS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid domain. Available domains: {list(DOMAINS.keys())}"
        )
    
    # Check if domain agent is available
    if domain not in domain_agents:
        raise HTTPException(
            status_code=503,
            detail=f"Domain agent '{domain}' is not available"
        )
    
    try:
        # Get domain agent
        agent = domain_agents[domain]
        domain_config = DOMAINS[domain]
        
        # Prepare MeTTa query
        query_script = f'!(&chat (user "{message.message}"))' #User query
        
        logger.info(f"🔍 [{domain.upper()}] Executing: {query_script}")
        
        # Execute query
        result = agent.run(query_script)
        
        logger.info(f"📨 [{domain.upper()}] Raw result: {result}")
        
        # Process result
        if result and len(result) > 0:
            response_atom = result[0]
            response_text = str(response_atom)
            
            # Clean response text
            if response_text.startswith('["') and response_text.endswith('"]'):
                response_text = response_text[2:-2]
            elif response_text.startswith('[') and response_text.endswith(']'):
                response_text = response_text[1:-1]
            
            response_text = response_text.replace('\\"', '"').strip()
            
            logger.info(f"🔧 [{domain.upper()}] Processed response: {response_text}")
            
            return ChatResponse(
                response=response_text,
                success=True,
                domain=domain,
                expert_name=domain_config["name"]
            )
        else:
            logger.warning(f"⚠️ [{domain.upper()}] Empty or invalid result")
            return ChatResponse(
                response=f"I'm having trouble processing your request right now. Please try again.",
                success=False,
                domain=domain,
                expert_name=domain_config["name"],
                error="Empty result from agent"
            )
            
    except Exception as e:
        logger.error(f"❌ [{domain.upper()}] Error: {str(e)}")
        
        # Domain-specific error messages
        error_messages = {
            "disaster": "I'm having trouble with my disaster response system. For immediate emergencies, please call 911.",
            "healthcare": "I'm having trouble with my medical systems right now. For medical emergencies, please call 911 or visit your nearest emergency room.",
            "legal": "I'm having trouble with my legal consultation system. For urgent legal matters, please contact a licensed attorney immediately."
        }
        
        return ChatResponse(
            response=error_messages.get(domain, "System temporarily unavailable. Please try again."),
            success=False,
            domain=domain, 
            expert_name=DOMAINS[domain]["name"],
            error=str(e)
        )

@app.get("/metta/status")
async def metta_status():
    """Get MeTTa system status"""
    try:
        status = {
            "version": "1.0.0",
            "domains_loaded": list(DOMAINS.keys()),
            "status": "operational"
        }
        return {"status": "success", "data": status}
    except Exception as e:
        logger.error(f"Error getting MeTTa status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge-graph/search")
async def search_knowledge_graph(
    keywords: str = Query(..., description="Comma-separated list of keywords to search for"),
    domain: str = "disaster"
):
    """
    Search the knowledge graph for nodes and relationships matching the given keywords.
    Returns a graph structure with nodes and edges.
    """
    try:
        if domain not in domain_agents:
            raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")

        metta = domain_agents[domain]
        
        # Prepare the search query
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        if not keyword_list:
            return KnowledgeGraphResponse(nodes=[], links=[], success=True)
        
        # Format the search query
        search_terms = ' '.join([f'"{k}"' for k in keyword_list])
        query = f"!(search-multiple ({search_terms}))"
        
        # Execute the query
        results = metta.run(query)
        
        # Process results into nodes and edges
        nodes = set()
        links = []
        node_id = 0
        edge_id = 0
        
        # This is a simplified example - you'll need to adjust based on your actual MeTTa response structure
        for result in results:
            if not result:
                continue
                
            # Example processing - adjust based on your actual data structure
            if isinstance(result, dict):
                # Handle node
                node_id_str = str(result.get('assertion-id', node_id))
                nodes.add((node_id_str, {
                    'id': node_id_str,
                    'label': result.get('text', 'Unnamed Node'),
                    'type': result.get('type', 'concept'),
                    'properties': {k: v for k, v in result.items() if k not in ['id', 'label', 'type']}
                }))
                
                # Handle relationships (simplified)
                if 'sub_concept' in result:
                    target_id = f"sub_{node_id}"
                    links.append({
                        'id': f"edge_{edge_id}",
                        'source': node_id_str,
                        'target': target_id,
                        'label': 'sub-concept-of',
                        'properties': {}
                    })
                    edge_id += 1
                    
                    # Add the sub-concept node
                    nodes.add((target_id, {
                        'id': target_id,
                        'label': result.get('sub_concept', 'Sub-concept'),
                        'type': 'concept',
                        'properties': {}
                    }))
                
                node_id += 1
        
        # Convert to response model
        return KnowledgeGraphResponse(
            nodes=[KnowledgeGraphNode(**node[1]) for node in nodes],
            links=[KnowledgeGraphEdge(**link) for link in links],
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error searching knowledge graph: {str(e)}")
        return KnowledgeGraphResponse(
            nodes=[],
            links=[],
            success=False,
            error=str(e)
        )
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Athena Multi-Domain Expert System...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

from dotenv import load_dotenv
import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from hyperon import MeTTa
from hyperon.ext import register_tokens
from hyperon import *

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Athena Multi-Domain Expert System", version="2.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    success: bool
    domain: str
    expert_name: str
    error: str = None

class HealthResponse(BaseModel):
    status: str
    message: str
    domains_active: Dict[str, bool]

# Global variables
domain_agents = {}
DOMAINS = {
    "disaster": {
        "name": "🚨 Athena - Disaster Specialist",
        "file": "domains/disaster.msa",
        "theme": {"primary": "#dc2626", "secondary": "#ea580c"}
    },
    "healthcare": {
        "name": "🩺 Dr. Athena - Medical Advisor", 
        "file": "domains/healthcare.msa",
        "theme": {"primary": "#2563eb", "secondary": "#16a34a"}
    },
    "legal": {
        "name": "⚖️ Attorney Athena - Legal Consultant",
        "file": "domains/legal.msa", 
        "theme": {"primary": "#1e40af", "secondary": "#b45309"}
    }
}

def initialize_domain_agents():
    """Initialize all MeTTa domain agents"""
    global domain_agents
    
    # Check if OpenRouter API key exists
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if not openrouter_key:
        logger.error("❌ OPENROUTER_API_KEY environment variable not found")
        return False
    
    logger.info("✅ OpenRouter API key loaded")
    
    try:
        for domain, config in DOMAINS.items():
            logger.info(f"🔄 Initializing {domain} agent...")
            
            # Create MeTTa instance
            agent = MeTTa()
            
            # Import motto
            agent.run("!(import! &self motto)") #Importing motto
            
            # Load domain-specific agent
            bind_command = f'!(bind! &chat (dialog-agent "{config["file"]}"))' #binding command
            result = agent.run(bind_command)
            
            # Store agent
            domain_agents[domain] = agent
            logger.info(f"✅ {config['name']} initialized successfully")
        
        logger.info("🔥 All domain agents ready!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize domain agents: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("🚨 Starting Athena Multi-Domain Expert System")
    
    if initialize_domain_agents():
        logger.info("📱 System ready at: http://localhost:8000")
    else:
        logger.error("💥 Failed to initialize system")

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Athena Multi-Domain Expert System",
        "version": "2.0",
        "domains": list(DOMAINS.keys()),
        "status": "active"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    domains_status = {}
    
    for domain in DOMAINS:
        domains_status[domain] = domain in domain_agents and domain_agents[domain] is not None
    
    all_healthy = all(domains_status.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        message="Multi-domain system operational" if all_healthy else "Some domains unavailable",
        domains_active=domains_status
    )

@app.get("/domains", response_model=Dict[str, Any])
async def get_domains():
    """Get available domains and their information"""
    return {
        "domains": DOMAINS,
        "active_domains": list(domain_agents.keys())
    }

@app.post("/chat/{domain}", response_model=ChatResponse)
async def chat_endpoint(domain: str, message: ChatMessage):
    """Chat with specific domain expert"""
    
    # Validate domain
    if domain not in DOMAINS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid domain. Available domains: {list(DOMAINS.keys())}"
        )
    
    # Check if domain agent is available
    if domain not in domain_agents:
        raise HTTPException(
            status_code=503,
            detail=f"Domain agent '{domain}' is not available"
        )
    
    try:
        # Get domain agent
        agent = domain_agents[domain]
        domain_config = DOMAINS[domain]
        
        # Prepare MeTTa query
        query_script = f'!(&chat (user "{message.message}"))' #User query
        
        logger.info(f"🔍 [{domain.upper()}] Executing: {query_script}")
        
        # Execute query
        result = agent.run(query_script)
        
        logger.info(f"📨 [{domain.upper()}] Raw result: {result}")
        
        # Process result
        if result and len(result) > 0:
            response_atom = result[0]
            response_text = str(response_atom)
            
            # Clean response text
            if response_text.startswith('["') and response_text.endswith('"]'):
                response_text = response_text[2:-2]
            elif response_text.startswith('[') and response_text.endswith(']'):
                response_text = response_text[1:-1]
            
            response_text = response_text.replace('\\"', '"').strip()
            
            logger.info(f"🔧 [{domain.upper()}] Processed response: {response_text}")
            
            return ChatResponse(
                response=response_text,
                success=True,
                domain=domain,
                expert_name=domain_config["name"]
            )
        else:
            logger.warning(f"⚠️ [{domain.upper()}] Empty or invalid result")
            return ChatResponse(
                response=f"I'm having trouble processing your request right now. Please try again.",
                success=False,
                domain=domain,
                expert_name=domain_config["name"],
                error="Empty result from agent"
            )
            
    except Exception as e:
        logger.error(f"❌ [{domain.upper()}] Error: {str(e)}")
        
        # Domain-specific error messages
        error_messages = {
            "disaster": "I'm having trouble with my disaster response system. For immediate emergencies, please call 911.",
            "healthcare": "I'm having trouble with my medical systems right now. For medical emergencies, please call 911 or visit your nearest emergency room.",
            "legal": "I'm having trouble with my legal consultation system. For urgent legal matters, please contact a licensed attorney immediately."
        }
        
        return ChatResponse(
            response=error_messages.get(domain, "System temporarily unavailable. Please try again."),
            success=False,
            domain=domain, 
            expert_name=DOMAINS[domain]["name"],
            error=str(e)
        )

@app.get("/metta/status")
async def metta_status():
    """Get MeTTa system status"""
    try:
        status = {}
        for domain, agent in domain_agents.items():
            # Test if agent is responsive
            test_result = agent.run('!(+ 1 1)')
            status[domain] = {
                "status": "active" if test_result else "inactive",
                "name": DOMAINS[domain]["name"]
            }
        
        return {
            "status": "active",
            "message": "MeTTa multi-domain system operational",
            "domains": status
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"MeTTa system error: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Athena Multi-Domain Expert System...")
    uvicorn.run(app, host="0.0.0.0", port=8000)'''

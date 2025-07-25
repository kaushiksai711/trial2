# FAQ Chatbot with Knowledge Retrieval and Research Capabilities

## Core Idea
An intelligent FAQ chatbot system that combines knowledge base retrieval with external research capabilities, leveraging both semantic search and graph-based knowledge representation to provide comprehensive, accurate answers. The system features adaptive learning to improve over time, multi-format response capabilities, and advanced query decomposition techniques.

## Key Features
- **Multi-Agent Architecture**: Coordinated workflow between specialized agents
- **Knowledge Retrieval**: Semantic search and graph traversal for internal knowledge
- **External Research**: Web search and content extraction when internal knowledge is insufficient
- **Query Understanding**: Interprets user queries and determines required information
- **Graph-Based Knowledge**: Represents information as connected entities with relationships
- **Vector Embeddings**: Enables semantic similarity search for concepts
- **Hybrid Search**: Combines structured (graph) and unstructured (vector) search
- **Response Synthesis**: Generates natural language responses from multiple sources
- **Source Attribution**: Cites information sources for transparency
- **Confidence Scoring**: Evaluates confidence in retrieval and research results
- **Response Evaluation**: Assesses response quality across multiple dimensions
- **Adaptive Learning**: Updates knowledge graph based on user interactions and feedback
- **Multi-Format Responses**: Delivers information as text, images, links, and interactive elements
- **Complex Query Handling**: Decomposes complex queries into manageable sub-questions

## System Architecture

The system consists of five main components:

1. **Retrieval Agent**: Searches internal knowledge bases using vector embeddings and graph databases to find relevant information. It can perform semantic search, graph traversal, and query rewriting to improve results.

2. **Research Agent**: When the knowledge base doesn't have sufficient information, this agent conducts ethical web searches, extracts content from relevant pages, and synthesizes the information into a comprehensive answer.

3. **Orchestrator**: Coordinates the workflow between the different agents, determining when to use the knowledge base vs. external research, and combines the results to generate the final response.

4. **Learning Manager**: Continuously improves the knowledge base by incorporating new information from user interactions, feedback, and research results.

5. **Response Renderer**: Formats responses in multiple formats including text, images, links, and interactive elements based on content type and user preferences.

## Project Structure

```
src/
├── agents/                          # Agent components
│   ├── __init__.py                  # Package initialization
│   ├── agent_types.py               # Agent type definitions
│   ├── agent_orchestrator.py        # Multi-agent orchestration framework
│   ├── orchestrator.py              # Main orchestrator for agent workflow
│   ├── retrieval_agent.py           # Agent for knowledge base retrieval
│   ├── research_agent.py            # Agent for external research
│   ├── query_interpreter.py         # Agent for query understanding
│   ├── query_decomposer.py          # Agent for breaking down complex queries
│   ├── graph_navigator.py           # Agent for graph traversal
│   ├── context_builder.py           # Agent for building context from results
│   ├── response_generator.py        # Agent for generating final responses
│   ├── learning_agent.py            # Agent for knowledge base updates
│   └── reasoning_agent.py           # Agent for logical reasoning
├── knowledge/                       # Knowledge management
│   ├── graph_manager.py             # Interface for graph database operations
│   ├── embedding_service.py         # Vector embedding generation and search
│   ├── knowledge_updater.py         # Service for updating knowledge base
│   └── feedback_processor.py        # Service for processing user feedback
├── rendering/                       # Response rendering components
│   ├── text_renderer.py             # Text response formatting
│   ├── image_renderer.py            # Image generation and formatting
│   ├── link_renderer.py             # Link formatting and embedding
│   └── interactive_renderer.py      # Interactive elements generation
├── db/                              # Database connectors
│   ├── neo4j_connector.py           # Neo4j graph database connector
│   ├── qdrant_connector.py          # Qdrant vector database connector
│   └── media_store_connector.py     # Media storage connector
├── api/                             # API endpoints
│   ├── main.py                      # API server entry point
│   ├── chat_routes.py               # Chat interaction endpoints
│   └── feedback_routes.py           # User feedback endpoints
├── crawler/                         # Web crawling functionality
│   ├── web_crawler.py               # Ethical web crawler
│   └── media_extractor.py           # Extract images and media from web
├── main.py                          # Main application entry point
└── utils/                           # Utility functions
    ├── config.py                    # Configuration loader
    ├── logger.py                    # Logging utilities
    └── media_utils.py               # Media processing utilities
```

## Detailed Component Descriptions

### `src/agents/retrieval_agent.py`
The retrieval agent searches the knowledge base for relevant information.

- **Classes:**
  - `SearchQuery`: Model for search query parameters (query string, filters, top_k)
  - `RelatedEntities`: Model for entity relation search parameters (entity_id, relation_types, max_depth)
  - `QueryRewriter`: Model for query rewriting parameters (original_query, context, focus)
  - `RetrievalAgent`: Main agent implementation

- **Methods:**
  - `__init__(graph_manager, embedding_manager, llm)`: Initializes the agent with graph database, embedding service, and language model
  - `_create_tools()`: Creates tools for semantic search, graph search, finding related entities, and query rewriting
  - `_create_agent_executor()`: Sets up the LangChain agent executor with appropriate prompt
  - `_semantic_search(query, filters, top_k)`: Performs semantic search using embeddings
  - `_graph_search(query, filters, top_k)`: Searches for entities in the knowledge graph
  - `_find_related_entities(entity_id, relation_types, max_depth)`: Finds entities related to a given entity
  - `_rewrite_query(original_query, context, focus)`: Rewrites queries to improve search results
  - `evaluate_confidence(results)`: Evaluates confidence in the retrieval results
  - `run(state)`: Orchestrates the retrieval process and updates the state

### `src/agents/query_decomposer.py`
The query decomposer breaks down complex queries into simpler sub-questions.

- **Classes:**
  - `ComplexQuery`: Model for complex query parameters
  - `SubQuestion`: Model for decomposed sub-questions
  - `QueryDecomposer`: Main decomposer implementation

- **Methods:**
  - `__init__(llm)`: Initializes the decomposer with language model
  - `identify_complexity(query)`: Determines if a query needs decomposition
  - `decompose_query(query)`: Breaks down complex queries into sub-questions
  - `prioritize_subquestions(sub_questions)`: Orders sub-questions by priority
  - `run(state)`: Updates state with decomposed queries

### `src/agents/learning_agent.py`
The learning agent updates the knowledge base with new information.

- **Classes:**
  - `KnowledgeUpdate`: Model for knowledge update parameters
  - `UserFeedback`: Model for user feedback parameters
  - `LearningAgent`: Main agent implementation

- **Methods:**
  - `__init__(graph_manager, embedding_service, llm)`: Initializes the agent
  - `process_interaction(interaction)`: Extracts knowledge from user interactions
  - `process_feedback(feedback)`: Processes explicit user feedback
  - `validate_new_knowledge(knowledge)`: Validates potential new knowledge
  - `update_knowledge_base(validated_knowledge)`: Updates the knowledge base
  - `run(state)`: Updates state with learning outcomes

### `src/knowledge/knowledge_updater.py`
Service for updating the knowledge base with new information.

- **Class:**
  - `KnowledgeUpdater`: Service for knowledge base updates

- **Methods:**
  - `__init__(graph_manager, embedding_service)`: Initializes the service
  - `create_new_entity(entity_data)`: Creates a new entity in the knowledge graph
  - `update_entity(entity_id, updated_data)`: Updates an existing entity
  - `create_relationship(from_id, to_id, relationship_type, properties)`: Creates a new relationship
  - `update_embeddings(entity_id, text)`: Updates vector embeddings for an entity

### `src/rendering/image_renderer.py`
Service for generating and formatting image responses.

- **Class:**
  - `ImageRenderer`: Service for image rendering

- **Methods:**
  - `__init__(media_store)`: Initializes the renderer with media storage
  - `generate_image(prompt)`: Generates an image based on a prompt
  - `format_image_response(image, caption)`: Formats image with caption
  - `retrieve_relevant_image(query, context)`: Finds a relevant image for a query

### `src/rendering/interactive_renderer.py`
Service for generating interactive response elements.

- **Class:**
  - `InteractiveRenderer`: Service for interactive elements

- **Methods:**
  - `__init__()`: Initializes the renderer
  - `create_expandable_section(title, content)`: Creates expandable content sections
  - `create_table(headers, rows)`: Formats data as an interactive table
  - `create_decision_tree(nodes, edges)`: Creates an interactive decision tree
  - `format_interactive_response(elements)`: Combines interactive elements

## Implementation Plan (2 Phases)

### Phase 1: Core System & Basic Frontend (Deliverable by 6pm on Day 1)

#### Project Structure for Phase 1
```
src/
├── agents/
│   ├── __init__.py                  # Package initialization
│   ├── orchestrator.py              # Basic orchestrator for agent workflow
│   ├── retrieval_agent.py           # Core retrieval agent with basic capabilities
│   ├── query_interpreter.py         # Basic query understanding
│   └── query_decomposer.py          # Simple query decomposition (foundation)
├── knowledge/
│   ├── graph_manager.py             # Mock graph database interface
│   └── embedding_service.py         # Mock vector embedding service
├── db/
│   ├── neo4j_connector.py           # Mock Neo4j connector 
│   └── qdrant_connector.py          # Mock Qdrant connector
├── api/
│   ├── main.py                      # Basic API server
│   └── chat_routes.py               # Simple chat endpoints
├── rendering/
│   └── text_renderer.py             # Basic text response formatting
├── main.py                          # Demo application with mock components
└── utils/
    ├── config.py                    # Configuration loader
    └── logger.py                    # Logging utilities
```

#### Backend Development (First Half)
- Set up project structure and core framework
- Implement knowledge module with mock database services
- Develop basic retrieval agent with semantic search
- Implement query interpretation and basic decomposition functionality
- Set up foundation for adaptive learning

#### Frontend & API Development (Second Half)
- Create minimal API endpoints for chatbot interaction
- Develop basic frontend UI with query input and response display
- Implement text response rendering with source attribution
- Add simple feedback collection mechanism
- Connect frontend to backend services
- Prepare demo with basic functionality and documentation

**Deliverable**: Working MVP with frontend and backend integration for code review session

### Phase 2: Advanced Features & Final Integration (Deliverable by 1:30pm on Day 2)

#### Project Structure for Phase 2 (Additions to Phase 1)
```
src/
├── agents/
│   ├── research_agent.py            # Research agent for external information
│   ├── learning_agent.py            # Agent for knowledge base updates
│   ├── graph_navigator.py           # Advanced graph traversal
│   ├── context_builder.py           # Context building from multiple sources
│   ├── response_generator.py        # Enhanced response generation
│   └── reasoning_agent.py           # Logical reasoning capabilities
├── knowledge/
│   ├── knowledge_updater.py         # Knowledge base update service
│   └── feedback_processor.py        # User feedback processing
├── rendering/
│   ├── image_renderer.py            # Image response generation
│   ├── link_renderer.py             # Link formatting
│   └── interactive_renderer.py      # Interactive elements
├── db/
│   └── media_store_connector.py     # Media storage for images
├── api/
│   └── feedback_routes.py           # Feedback collection endpoints
└── crawler/
    ├── web_crawler.py               # Ethical web crawler
    └── media_extractor.py           # Media extraction from web
```

#### Research & Orchestration Capabilities
- Implement research agent with web search capabilities
- Add content extraction and synthesis functionality
- Develop the full orchestrator to coordinate between agents
- Enhance response generation with combined knowledge
- Implement advanced query decomposition for complex questions

#### Multi-Format & Adaptive Learning
- Implement image and link rendering capabilities
- Add interactive element generation
- Develop knowledge updater for continuous learning
- Implement feedback processor for refining responses
- Connect learning agent to knowledge management system

#### Refinement & Evaluation
- Add confidence scoring and response evaluation
- Implement error handling and logging
- Optimize performance and responsiveness
- Conduct comprehensive testing with complex queries
- Create final documentation and deployment guide

**Deliverable**: Complete system with all features implemented, tested, and documented

## System Workflow Diagrams

### Phase 1 Workflow (Core System)
```
                                              ┌──────────────────┐
                                              │                  │
                                ┌────────────►│  Knowledge Base  │◄───────────┐
                                │             │  (Mock Services) │            │
                                │             │                  │            │
                                │             └──────────────────┘            │
                                │                                             │
┌─────────────┐      ┌─────────┴──────────┐   ┌─────────────────────┐   ┌────┴─────────┐
│             │      │                    │   │                     │   │              │
│  User Query ├─────►│ Query Interpreter  ├──►│  Retrieval Agent    ├──►│ Orchestrator │
│             │      │                    │   │                     │   │              │
└─────────────┘      └────────────────────┘   └─────────────────────┘   └────┬─────────┘
                                                                              │
                               ┌───────────────────────────────────────┐      │
                               │                                       │      │
                               │            Text Renderer              │◄─────┘
                               │                                       │
                               └───────────────┬───────────────────────┘
                                               │
                               ┌───────────────▼───────────────────────┐
                               │                                       │
                               │               Response                │
                               │                                       │
                               └───────────────────────────────────────┘
```

### Phase 2 Workflow (Complete System)
```
                   ┌───────────────────┐              ┌──────────────────┐
                   │                   │              │                  │
                   │  Web Resources    │              │  Knowledge Base  │◄─────────┐
                   │                   │              │                  │          │
                   └─────────┬─────────┘              └─────┬──────┬─────┘          │
                             │                              │      │                │
                             │                              │      │                │
                             ▼                              │      │                │
┌─────────────┐    ┌────────────────┐    ┌─────────────────▼┐     │          ┌─────┴─────────┐
│             │    │                │    │                  │     │          │               │
│  User Query ├───►│    Query       ├───►│  Retrieval Agent │     │          │ Learning Agent│
│             │    │  Decomposer    │    │                  │     │          │               │
└─────────────┘    └─────┬──────────┘    └─────────┬────────┘     │          └───────────────┘
                         │                         │              │                  ▲
                         │                         │              │                  │
                         │                         │              │                  │
                         │                  ┌──────▼──────┐       │                  │
                         │                  │             │       │          ┌───────┴───────┐
                         │                  │  Research   │       │          │               │
                         │                  │   Agent     │       │          │    Feedback   │
                         │                  │             │       │          │   Processor   │
                         │                  └──────┬──────┘       │          │               │
                         │                         │              │          └───────────────┘
                         │                         │              │                  ▲
                         │                         │              │                  │
                         ▼                         ▼              ▼                  │
                  ┌─────────────────────────────────────────────────────┐           │
                  │                                                     │           │
                  │                    Orchestrator                     │◄──────────┘
                  │                                                     │
                  └───────────────────────────┬─────────────────────────┘
                                              │
                                              │
                  ┌─────────────────────┬─────┴────┬───────────────────────┐
                  │                     │          │                       │
                  ▼                     ▼          ▼                       ▼
         ┌────────────────┐    ┌────────────┐    ┌─────────────┐    ┌─────────────────┐
         │                │    │            │    │             │    │                 │
         │ Text Renderer  │    │   Image    │    │    Link     │    │   Interactive   │
         │                │    │  Renderer  │    │   Renderer  │    │     Renderer    │
         └───────┬────────┘    └─────┬──────┘    └──────┬──────┘    └────────┬────────┘
                 │                   │                   │                    │
                 │                   │                   │                    │
                 └───────────────────┼───────────────────┼────────────────────┘
                                     │                   │
                                     ▼                   ▼
                           ┌───────────────────────────────────────────┐
                           │                                           │
                           │            Unified Response                │
                           │                                           │
                           └───────────────────────────────────────────┘
```

## Usage

### Running the Demo

The demo script demonstrates how the system works with mock implementations:

```bash
python src/main.py
```

This will process several example queries and show the results, including the responses and their evaluations.

### Using Multi-Format Responses

To enable different response formats:

```python
# Configure format preferences in the context
context = {
    "user_id": "user123",
    "format_preferences": {
        "include_images": True,
        "include_links": True,
        "interactive_elements": ["expandable_sections", "tables"]
    }
}

# Process a query with format preferences
results = orchestrator.process("Your question here?", context=context)
```

### Providing Feedback for Adaptive Learning

To enable the system to learn from user feedback:

```python
# Submit feedback after receiving a response
feedback = {
    "query_id": "query_12345",
    "helpful": True,
    "corrections": {
        "entity_id": "concept_123",
        "suggested_update": "Updated definition of the concept"
    },
    "additional_info": "The concept is also related to X and Y"
}

# Submit feedback to the learning agent
learning_agent.process_feedback(feedback)
```

### Integrating with Your Own Systems

To use the system with your own knowledge base:

1. Implement adapters for your vector and graph databases
2. Configure search tools and content extractors for web research
3. Use the `Orchestrator` class to process queries:

```python
from agents.orchestrator import Orchestrator
from agents.retrieval_agent import RetrievalAgent
from agents.research_agent import ResearchAgent
from agents.learning_agent import LearningAgent

# Initialize agents with your own components
retrieval_agent = RetrievalAgent(
    llm=your_llm,
    embedding_manager=your_vector_db,
    graph_manager=your_graph_db
)

research_agent = ResearchAgent(
    llm=your_llm,
    search_tool=your_search_tool,
    content_extractor=your_content_extractor
)

learning_agent = LearningAgent(
    llm=your_llm,
    graph_manager=your_graph_db,
    embedding_service=your_vector_db
)

# Create the orchestrator
orchestrator = Orchestrator(
    llm=your_llm,
    retrieval_agent=retrieval_agent,
    research_agent=research_agent,
    learning_agent=learning_agent
)

# Process a query
results = orchestrator.process("Your question here?", context={"user_id": "user123"})
```

## Extending the System

The system is designed to be modular and extensible:

- **Add new tools**: Extend the `_create_tools` method in each agent to add new capabilities
- **Custom databases**: Implement adapters for your specific knowledge storage systems
- **Additional research methods**: Add more research methods to the research agent
- **New response formats**: Extend the rendering system with additional format handlers
- **Enhanced learning mechanisms**: Add specialized learning algorithms to the learning agent

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
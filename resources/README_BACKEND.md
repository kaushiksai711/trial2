# Medical Chatbot Backend Documentation

## Overview
This backend implements a medical chatbot system with knowledge retrieval capabilities. It uses a multi-agent architecture to process queries, retrieve information from various knowledge bases, and generate responses.

## System Architecture

### Components
1. **Agents**
   - `QueryInterpreter`: Understands user queries and extracts entities/intents
   - `QueryDecomposer`: Breaks down complex queries into simpler sub-questions
   - `RetrievalAgent`: Searches knowledge bases for relevant information
   - `Orchestrator`: Coordinates the workflow between agents

2. **Database Connectors**
   - `Neo4jConnector`: Graph database for structured medical knowledge
   - `QdrantConnector`: Vector database for semantic search
   - `MongoDBConnector`: Document database for additional information

3. **API**
   - FastAPI server with endpoints for chat and health checks
   - CORS middleware for frontend integration
   - Response formatting and error handling

## API Endpoints

### 1. Chat Endpoint
```http
POST /chat
```

**Request Body:**
```json
{
  "query": "What are the symptoms of asthma?",
  "context": {}  // Optional
}
```

**Response:**
```json
{
  "response": "From medical database: Asthma symptoms include...",
  "sources": ["graph", "vector"],
  "status": "success"
}
```

### 2. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "neo4j": true,
    "qdrant": true,
    "mongodb": true
  }
}
```

## Environment Setup

### Required Environment Variables
```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_api_key

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=medical_chatbot

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Model Configuration
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Logging
LOG_LEVEL=INFO
```

## Running the Backend

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the API server:
```bash
uvicorn src.api.main:app --reload
```

## Integration with Vercel Frontend

### 1. Backend Deployment
- Deploy the backend to a hosting service (e.g., Heroku, AWS, GCP)
- Ensure CORS is properly configured for your Vercel domain

### 2. Frontend Configuration
In your Vercel frontend, configure the API client:

```typescript
// api.ts
const API_BASE_URL = 'https://your-backend-url.com';

export const chat = async (query: string, context?: any) => {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, context }),
  });
  return response.json();
};

export const checkHealth = async () => {
  const response = await fetch(`${API_BASE_URL}/health`);
  return response.json();
};
```

### 3. Example Frontend Usage
```typescript
// ChatComponent.tsx
import { chat } from './api';

const ChatComponent = () => {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const result = await chat(message);
      setResponse(result.response);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button type="submit">Send</button>
      </form>
      <div>{response}</div>
    </div>
  );
};
```

## Error Handling

The backend returns standardized error responses:

```json
{
  "status": "error",
  "response": "Error message",
  "sources": [],
  "error": "Detailed error information"
}
```

Common error scenarios:
1. Database connection failures
2. Invalid queries
3. Missing information
4. Server errors

## Testing

Run the test suite:
```bash
pytest tests/
```

Key test files:
- `test_retrieval_agent.py`: Tests knowledge retrieval functionality
- `test_backend.py`: End-to-end backend tests
- `test_api.py`: API endpoint tests

## Development Guidelines

1. **Code Structure**
   - Keep agent logic separate from database operations
   - Use type hints for better code maintainability
   - Follow PEP 8 style guidelines

2. **Error Handling**
   - Use proper exception handling
   - Log errors with appropriate context
   - Return meaningful error messages

3. **Documentation**
   - Document all public methods and classes
   - Keep README updated with changes
   - Add comments for complex logic

## Deployment Considerations

1. **Environment Variables**
   - Use different values for development and production
   - Keep sensitive information secure
   - Use environment-specific configuration files

2. **Scaling**
   - Consider database connection pooling
   - Implement caching for frequent queries
   - Monitor resource usage

3. **Security**
   - Implement rate limiting
   - Use HTTPS
   - Validate all inputs
   - Implement proper authentication if needed

## Troubleshooting

Common issues and solutions:

1. **Database Connection Issues**
   - Check environment variables
   - Verify database services are running
   - Check network connectivity

2. **API Errors**
   - Check CORS configuration
   - Verify request format
   - Check server logs

3. **Performance Issues**
   - Monitor database queries
   - Check for memory leaks
   - Optimize response times

## Support

For issues or questions:
1. Check the documentation
2. Review server logs
3. Contact the development team

## License

[MIT License](LICENSE) 
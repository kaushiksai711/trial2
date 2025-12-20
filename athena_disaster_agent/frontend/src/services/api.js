import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper function to handle API errors
const handleApiError = (error, defaultMessage = 'An error occurred') => {
  console.error('API Error:', error);
  if (error.response) {
    // The request was made and the server responded with a status code
    // that falls out of the range of 2xx
    throw new Error(error.response.data?.error || defaultMessage);
  } else if (error.request) {
    // The request was made but no response was received
    throw new Error('No response from server. Please check your connection.');
  } else {
    // Something happened in setting up the request that triggered an Error
    throw new Error(error.message || defaultMessage);
  }
};

export const apiService = {
  // Send chat message to specific domain
  sendMessage: async (message, domain = 'disaster', sessionId = 'web-client') => {
    try {
      const response = await api.post(`/chat/${domain}`, {
        message,
        session_id: sessionId,
      });
      return response.data;
    } catch (error) {
      console.error(`API Error [${domain}]:`, error);
      
      // Domain-specific error messages
      const errorMessages = {
        disaster: 'Failed to connect to disaster response system. For emergencies, call 911.',
        healthcare: 'Failed to connect to medical advisory system. For medical emergencies, call 911.',
        legal: 'Failed to connect to legal consultation system. For urgent matters, contact an attorney.'
      };
      
      throw new Error(errorMessages[domain] || 'Failed to connect to expert system');
    }
  },

  // Get available domains
  getDomains: async () => {
    try {
      const response = await api.get('/domains');
      return response.data;
    } catch (error) {
      console.error('Domains API Error:', error);
      return { domains: {} };
    }
  },

  // Check backend health
  checkHealth: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health Check Error:', error);
      return { status: 'unhealthy', domains_active: {} };
    }
  },

  // Get MeTTa status for all domains
  getMettaStatus: async () => {
    try {
      const response = await api.get('/metta/status');
      return response.data;
    } catch (error) {
      console.error('MeTTa Status Error:', error);
      return { status: 'error', domains: {} };
    }
  },

  // Search knowledge graph
  searchKnowledgeGraph: async (keywords, domain = 'disaster') => {
    try {
      const response = await api.get('/api/knowledge-graph/search', {
        params: { keywords, domain }
      });
      return response.data;
    } catch (error) {
      console.error('Knowledge Graph Search Error:', error);
      return { success: false, error: 'Failed to search knowledge graph', nodes: [], links: [] };
    }
  },

  // Get node details by ID
  getNodeDetails: async (nodeId, domain = 'disaster') => {
    try {
      const response = await api.get(`/api/knowledge-graph/nodes/${nodeId}`, {
        params: { domain }
      });
      return response.data;
    } catch (error) {
      console.error('Node Details Error:', error);
      return { success: false, error: 'Failed to get node details' };
    }
  },

  // Get related nodes
  getRelatedNodes: async (nodeId, relationshipType, domain = 'disaster') => {
    try {
      const response = await api.get(`/api/knowledge-graph/nodes/${nodeId}/related`, {
        params: { relationship: relationshipType, domain }
      });
      return response.data;
    } catch (error) {
      console.error('Related Nodes Error:', error);
      return { success: false, error: 'Failed to get related nodes', nodes: [], links: [] };
    }
  },
};

export default apiService;

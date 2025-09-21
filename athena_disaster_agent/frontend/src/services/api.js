import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
};

export default apiService;

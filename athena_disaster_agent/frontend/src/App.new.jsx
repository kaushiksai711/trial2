import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import ChatInterface from './components/ChatInterface';
import KnowledgeGraph from './components/KnowledgeGraph';
import DomainTabs from './components/DomainTabs';
import DomainQuickActions from './components/DomainQuickActions';
import DomainExpertHeader from './components/DomainExpertHeader';
import StatusIndicator from './components/StatusIndicator';
import ThemeToggle from './components/ThemeToggle';
import SoundEffects from './components/SoundEffects';
import { apiService } from './services/api';
import './App.css';
import './components/KnowledgeGraph.css';

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const isKnowledgeGraph = location.pathname === '/knowledge-graph';
  
  // Domain and conversation state
  const [selectedDomain, setSelectedDomain] = useState('disaster');
  const [conversations, setConversations] = useState({
    disaster: [],
    healthcare: [],
    legal: []
  });
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState(null);
  const [sessionId] = useState(() => `web-${Date.now()}`);

  // Check backend status on load
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const health = await apiService.checkHealth();
        const metta = await apiService.getMettaStatus();
        setBackendStatus({ health, metta });
        console.log('✅ Backend status:', { health, metta });
      } catch (error) {
        console.error('Status check failed:', error);
        setBackendStatus({ 
          health: { status: 'unhealthy' }, 
          metta: { status: 'error' } 
        });
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleDomainChange = (domain) => {
    console.log(`🔄 Switching to domain: ${domain}`);
    setSelectedDomain(domain);
    if (window.athenaSounds?.success) {
      window.athenaSounds.success();
    }
  };

  const handleSendMessage = async (message) => {
    if (!message.trim()) return;

    const userMessage = {
      id: Date.now().toString(),
      message,
      response: '',
      timestamp: new Date(),
      isUser: true,
      domain: selectedDomain
    };

    setConversations(prev => ({
      ...prev,
      [selectedDomain]: [...prev[selectedDomain], userMessage]
    }));

    setIsLoading(true);

    try {
      if (window.athenaSounds?.messageSent) {
        window.athenaSounds.messageSent();
      }
    } catch (error) {
      console.log('Send sound failed:', error);
    }

    try {
      const apiResponse = await apiService.sendMessage(message, selectedDomain, sessionId);
      
      const expertMessage = {
        id: (Date.now() + 1).toString(),
        message: '',
        response: apiResponse.response,
        timestamp: new Date(),
        isUser: false,
        domain: selectedDomain,
        expertName: apiResponse.expert_name
      };

      setConversations(prev => ({
        ...prev,
        [selectedDomain]: [...prev[selectedDomain], expertMessage]
      }));

      try {
        if (window.athenaSounds?.messageReceived) {
          window.athenaSounds.messageReceived();
        }
      } catch (error) {
        console.log('Receive sound failed:', error);
      }

    } catch (error) {
      console.error(`❌ Error in ${selectedDomain} domain:`, error);
      
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        message: '',
        response: error.message || `I'm having trouble with the ${selectedDomain} system. Please try again.`,
        timestamp: new Date(),
        isUser: false,
        domain: selectedDomain,
        expertName: `${selectedDomain} Expert`
      };

      setConversations(prev => ({
        ...prev,
        [selectedDomain]: [...prev[selectedDomain], errorMessage]
      }));

      try {
        if (window.athenaSounds?.error) {
          window.athenaSounds.error();
        }
      } catch (error) {
        console.log('Error sound failed:', error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (question) => {
    handleSendMessage(question);
  };

  const currentConversation = conversations[selectedDomain] || [];

  const getDomainEmergencyHeader = () => ({
    disaster: {
      title: "🚨 Emergency Disaster Response",
      subtitle: "For immediate life-threatening emergencies, call 911 first",
      buttonText: "📞 CALL 911 NOW"
    },
    healthcare: {
      title: "🩺 Medical Emergency Response", 
      subtitle: "For medical emergencies, call 911 or go to nearest ER",
      buttonText: "📞 CALL 911 NOW"
    },
    legal: {
      title: "⚖️ Legal Emergency Assistance",
      subtitle: "For urgent legal matters, contact an attorney immediately", 
      buttonText: "📞 FIND ATTORNEY"
    }
  })[selectedDomain] || {};

  const emergencyHeader = getDomainEmergencyHeader();
  const navigateToGraph = () => navigate('/knowledge-graph');
  const navigateToChat = () => navigate('/');

  return (
    <div className={`app ${selectedDomain}`}>
      {/* Emergency Header */}
      <div className="emergency-header" style={{
        background: selectedDomain === 'disaster' ? 'linear-gradient(135deg, #ef4444, #dc2626)' :
                   selectedDomain === 'healthcare' ? 'linear-gradient(135deg, #2563eb, #1d4ed8)' :
                   'linear-gradient(135deg, #1e40af, #1d4ed8)',
        padding: '1rem',
        color: 'white',
        textAlign: 'center'
      }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          {emergencyHeader.title}
        </h1>
        <p style={{ marginBottom: '1rem', opacity: '0.9' }}>
          {emergencyHeader.subtitle}
        </p>
        <button 
          className="btn-emergency" 
          onClick={() => {
            if (selectedDomain === 'legal') {
              window.open('https://www.findlaw.com/find-an-attorney/', '_blank');
            } else if (window.confirm('This will attempt to call emergency services. Are you sure?')) {
              window.location.href = 'tel:911';
            }
          }}
          style={{ 
            fontSize: '1.1rem', 
            padding: '0.75rem 2rem',
            background: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 'bold',
            color: selectedDomain === 'disaster' ? '#dc2626' : 
                  selectedDomain === 'healthcare' ? '#1d4ed8' : '#1e40af'
          }}
        >
          {emergencyHeader.buttonText}
        </button>
      </div>

      {/* Main Header */}
      <div className="header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1rem',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <DomainExpertHeader domain={selectedDomain} />
        <div className="header-controls" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <StatusIndicator status={backendStatus} />
          <button 
            onClick={isKnowledgeGraph ? navigateToChat : navigateToGraph}
            style={{
              margin: '0 10px',
              padding: '8px 16px',
              borderRadius: '4px',
              border: 'none',
              background: '#4a90e2',
              color: 'white',
              cursor: 'pointer',
              transition: 'background 0.3s'
            }}
            onMouseOver={(e) => e.target.style.background = '#357abd'}
            onMouseOut={(e) => e.target.style.background = '#4a90e2'}
          >
            {isKnowledgeGraph ? 'Back to Chat' : 'View Knowledge Graph'}
          </button>
          <ThemeToggle />
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content" style={{
        display: 'flex',
        flex: 1,
        overflow: 'hidden',
        maxWidth: '1200px',
        margin: '0 auto',
        width: '100%',
        padding: '1rem'
      }}>
        {!isKnowledgeGraph ? (
          <>
            <div className="sidebar" style={{
              width: '250px',
              padding: '1rem',
              borderRight: '1px solid #e5e7eb'
            }}>
              <DomainTabs 
                selectedDomain={selectedDomain}
                onDomainChange={handleDomainChange}
              />
              <DomainQuickActions 
                domain={selectedDomain} 
                onQuickAction={handleQuickAction} 
              />
            </div>

            <div className="chat-container" style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              maxHeight: 'calc(100vh - 300px)',
              overflow: 'hidden'
            }}>
              <ChatInterface 
                messages={conversations[selectedDomain]}
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
                domain={selectedDomain}
              />
            </div>
          </>
        ) : (
          <div className="knowledge-graph-page" style={{
            width: '100%',
            height: 'calc(100vh - 200px)',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            <KnowledgeGraph domain={selectedDomain} />
          </div>
        )}
      </div>
      
      {/* Footer */}
      <footer style={{
        textAlign: 'center',
        padding: '1rem',
        borderTop: '1px solid #e5e7eb',
        marginTop: 'auto',
        fontSize: '0.875rem',
        color: '#6b7280'
      }}>
        <p>
          {selectedDomain === 'disaster' && '⚠️ For immediate life-threatening emergencies, always call 911 first'}
          {selectedDomain === 'healthcare' && '⚠️ For medical emergencies, call 911 or visit your nearest emergency room'}
          {selectedDomain === 'legal' && '⚠️ For urgent legal matters, contact a licensed attorney immediately'}
        </p>
        <p style={{ marginTop: '0.5rem' }}>
          Powered by MeTTa + OpenRouter • Multi-Domain Expert System • {selectedDomain.charAt(0).toUpperCase() + selectedDomain.slice(1)} Specialist Active
        </p>
      </footer>

      {/* Sound Effects */}
      <SoundEffects domain={selectedDomain} />

      {/* Debug Info (development only) */}
      {process.env.NODE_ENV === 'development' && (
        <div style={{
          position: 'fixed',
          bottom: '10px',
          left: '10px',
          background: 'rgba(0,0,0,0.8)',
          color: 'white',
          padding: '0.5rem',
          borderRadius: '4px',
          fontSize: '0.7rem',
          fontFamily: 'monospace',
          zIndex: 1000
        }}>
          Domain: {selectedDomain} | Messages: {currentConversation.length} | Loading: {isLoading.toString()}
        </div>
      )}
    </div>
  );
}

export default App;

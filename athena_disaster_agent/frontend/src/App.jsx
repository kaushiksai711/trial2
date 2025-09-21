import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import DomainTabs from './components/DomainTabs';
import DomainQuickActions from './components/DomainQuickActions';
import DomainExpertHeader from './components/DomainExpertHeader';
import EmergencyHeader from './components/EmergencyHeader';
import StatusIndicator from './components/StatusIndicator';
import ThemeToggle from './components/ThemeToggle';
import SoundEffects from './components/SoundEffects';
import { apiService } from './services/api';
import './App.css';

function App() {
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
    
    // Periodic status checks every 30 seconds
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleDomainChange = (domain) => {
    console.log(`🔄 Switching to domain: ${domain}`);
    setSelectedDomain(domain);
    
    // Play domain switch sound
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

    // Add user message to current domain's conversation
    setConversations(prev => ({
      ...prev,
      [selectedDomain]: [...prev[selectedDomain], userMessage]
    }));

    setIsLoading(true);

    // Play send sound
    try {
      if (window.athenaSounds?.messageSent) {
        window.athenaSounds.messageSent();
      }
    } catch (error) {
      console.log('Send sound failed:', error);
    }

    try {
      console.log(`📨 Sending message to ${selectedDomain} domain:`, message);
      
      const apiResponse = await apiService.sendMessage(message, selectedDomain, sessionId);
      
      console.log(`📨 Response from ${selectedDomain}:`, apiResponse);

      const expertMessage = {
        id: (Date.now() + 1).toString(),
        message: '',
        response: apiResponse.response,
        timestamp: new Date(),
        isUser: false,
        domain: selectedDomain,
        expertName: apiResponse.expert_name
      };

      // Add expert response to current domain's conversation
      setConversations(prev => ({
        ...prev,
        [selectedDomain]: [...prev[selectedDomain], expertMessage]
      }));

      // Play receive sound
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

      // Play error sound
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

  // Get current domain's conversation
  const currentConversation = conversations[selectedDomain] || [];

  // Get domain-specific emergency header based on selected domain
  const getDomainEmergencyHeader = () => {
    const headers = {
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
    };
    
    return headers[selectedDomain] || headers.disaster;
  };

  const emergencyHeader = getDomainEmergencyHeader();

  return (
    <div className={`min-h-screen domain-${selectedDomain}`}>
      <div className="container">
        {/* Sound Effects */}
        <SoundEffects enabled={true} />
        
        {/* Theme Toggle Button */}
        <ThemeToggle />
        
        {/* Domain-Specific Emergency Header */}
        <div className="emergency-header" style={{
          background: selectedDomain === 'disaster' ? 'linear-gradient(135deg, #ef4444, #dc2626)' :
                     selectedDomain === 'healthcare' ? 'linear-gradient(135deg, #2563eb, #1d4ed8)' :
                     'linear-gradient(135deg, #1e40af, #1d4ed8)'
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
              } else {
                if (window.confirm('This will attempt to call emergency services. Are you sure?')) {
                  window.location.href = 'tel:911';
                }
              }
            }}
            style={{ fontSize: '1.1rem', padding: '0.75rem 2rem' }}
          >
            {emergencyHeader.buttonText}
          </button>
        </div>
        
        {/* Backend Status Indicator */}
        <StatusIndicator status={backendStatus} />

        {/* Domain Selection Tabs */}
        <DomainTabs 
          selectedDomain={selectedDomain}
          onDomainChange={handleDomainChange}
        />

        {/* Main Chat Interface */}
        <div className="chat-container">
          {/* Domain-Specific Chat Header */}
          <div className={`chat-header domain-${selectedDomain}`}>
            <h2 className="text-xl font-semibold flex items-center gap-2">
              {selectedDomain === 'disaster' && '🚨 Athena Disaster Response Agent'}
              {selectedDomain === 'healthcare' && '🩺 Dr. Athena Medical Advisory'}
              {selectedDomain === 'legal' && '⚖️ Attorney Athena Legal Consultation'}
            </h2>
            <p className="text-blue-100 text-sm mt-1">
              {selectedDomain === 'disaster' && 'Emergency preparedness and disaster safety guidance'}
              {selectedDomain === 'healthcare' && 'Medical information and health guidance • Not a substitute for professional care'}
              {selectedDomain === 'legal' && 'Legal information and consultation • Not a substitute for licensed attorney'}
            </p>
          </div>

          {/* Domain Expert Header */}
          <DomainExpertHeader 
            domain={selectedDomain}
            isLoading={isLoading}
          />

          {/* Domain-Specific Quick Actions */}
          <DomainQuickActions 
            domain={selectedDomain}
            onQuickAction={handleQuickAction}
          />

          {/* Chat Interface */}
          <ChatInterface
            messages={currentConversation}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            domain={selectedDomain}
          />
        </div>

        {/* Domain-Specific Footer */}
        <div style={{
          textAlign: 'center',
          color: 'var(--text-muted)',
          fontSize: '0.875rem',
          marginTop: '1.5rem'
        }}>
          <p>
            {selectedDomain === 'disaster' && '⚠️ For immediate life-threatening emergencies, always call 911 first'}
            {selectedDomain === 'healthcare' && '⚠️ For medical emergencies, call 911 or visit your nearest emergency room'}
            {selectedDomain === 'legal' && '⚠️ For urgent legal matters, contact a licensed attorney immediately'}
          </p>
          <p style={{ marginTop: '0.5rem' }}>
            Powered by MeTTa + OpenRouter • Multi-Domain Expert System • {selectedDomain.charAt(0).toUpperCase() + selectedDomain.slice(1)} Specialist Active
          </p>
        </div>

        {/* Domain Status Debug Info (only in development) */}
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
            fontFamily: 'monospace'
          }}>
            Domain: {selectedDomain} | Messages: {currentConversation.length} | Loading: {isLoading.toString()}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

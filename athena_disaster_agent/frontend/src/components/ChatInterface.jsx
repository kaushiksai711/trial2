import React, { useState, useRef, useEffect } from 'react';
import { useVoice } from '../hooks/useVoice';

const ChatInterface = ({ messages, onSendMessage, isLoading, domain = 'disaster' }) => {
  const [inputValue, setInputValue] = useState('');
  const [autoReadAloud, setAutoReadAloud] = useState(false); // User preference for auto read-aloud
  const [currentlySpeaking, setCurrentlySpeaking] = useState(null); // Track which message is being read
  const [speechUtterance, setSpeechUtterance] = useState(null); // Track current speech
  const messagesEndRef = useRef(null);
  const { voiceConfig, startListening, stopListening, speak, stopSpeaking } = useVoice();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-speak Athena responses ONLY if autoReadAloud is enabled
  useEffect(() => {
    if (autoReadAloud && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (!lastMessage.isUser && lastMessage.response) {
        handleReadAloud(lastMessage.response, lastMessage.id);
      }
    }
  }, [messages, autoReadAloud]);

  // Monitor speech synthesis events
  useEffect(() => {
    const handleSpeechEnd = () => {
      setCurrentlySpeaking(null);
      setSpeechUtterance(null);
    };

    const handleSpeechError = () => {
      setCurrentlySpeaking(null);
      setSpeechUtterance(null);
    };

    // Clean up speech events
    return () => {
      if (speechUtterance) {
        speechUtterance.removeEventListener('end', handleSpeechEnd);
        speechUtterance.removeEventListener('error', handleSpeechError);
      }
    };
  }, [speechUtterance]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleVoiceStart = () => {
    // FIXED: Don't auto-enable read-aloud when using mic
    startListening(
      (transcript) => {
        setInputValue(transcript);
        // Auto-submit voice input
        setTimeout(() => {
          if (transcript.trim()) {
            onSendMessage(transcript.trim());
            setInputValue('');
          }
        }, 500);
      },
      (error) => {
        console.error('Voice recognition error:', error);
        alert('Voice recognition failed: ' + error);
      }
    );
  };

  const handleVoiceStop = () => {
    stopListening();
  };

  const toggleAutoReadAloud = () => {
    // If currently speaking, stop it
    if (currentlySpeaking) {
      stopSpeech();
    }
    setAutoReadAloud(!autoReadAloud);
  };

  // Unified speech control function
  const handleReadAloud = (text, messageId) => {
    // If currently speaking the same message, stop it
    if (currentlySpeaking === messageId) {
      stopSpeech();
      return;
    }

    // If speaking a different message, stop it first
    if (currentlySpeaking) {
      stopSpeech();
    }

    // Clean text for speech (remove markdown formatting)
    const cleanText = text.replace(/\*\*(.*?)\*\*/g, '$1').replace(/\\n/g, ' ');

    // Start new speech
    if (window.speechSynthesis) {
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      utterance.volume = 0.8;

      // Set up event listeners
      utterance.onstart = () => {
        setCurrentlySpeaking(messageId);
        setSpeechUtterance(utterance);
        console.log('Started speaking message:', messageId);
      };

      utterance.onend = () => {
        setCurrentlySpeaking(null);
        setSpeechUtterance(null);
        console.log('Finished speaking message:', messageId);
      };

      utterance.onerror = (event) => {
        console.error('Speech error:', event.error);
        setCurrentlySpeaking(null);
        setSpeechUtterance(null);
      };

      // Start speaking
      window.speechSynthesis.cancel(); // Cancel any existing speech
      window.speechSynthesis.speak(utterance);
    }
  };

  const stopSpeech = () => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setCurrentlySpeaking(null);
      setSpeechUtterance(null);
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  // ENHANCED MESSAGE FORMATTER - Handles \n and **bold** text
  const formatMessage = (text) => {
    if (!text) return '';
    
    // Step 1: Convert \n to actual line breaks
    const withLineBreaks = text.replace(/\\n/g, '\n');
    
    // Step 2: Split into lines and process each one
    return withLineBreaks.split('\n').map((line, lineIndex) => {
      if (line.trim() === '') {
        // Empty line - add spacing
        return <div key={`empty-${lineIndex}`} style={{ height: '0.5rem' }} />;
      }
      
      // Step 3: Process bold formatting **text**
      const parts = [];
      let currentIndex = 0;
      const boldRegex = /\*\*(.*?)\*\*/g;
      let match;
      
      while ((match = boldRegex.exec(line)) !== null) {
        // Add normal text before bold
        if (match.index > currentIndex) {
          parts.push(line.substring(currentIndex, match.index));
        }
        
        // Add bold text
        parts.push(
          <strong key={`bold-${lineIndex}-${match.index}`} style={{ fontWeight: '700', color: 'inherit' }}>
            {match[1]}
          </strong>
        );
        
        currentIndex = match.index + match[0].length;
      }
      
      // Add remaining normal text
      if (currentIndex < line.length) {
        parts.push(line.substring(currentIndex));
      }
      
      return (
        <div key={lineIndex} style={{ marginBottom: '0.25rem' }}>
          {parts.length > 0 ? parts : line}
        </div>
      );
    });
  };

  // Domain-specific welcome messages
  const getWelcomeMessage = () => {
    const welcomeData = {
      disaster: {
        icon: '🚨',
        title: 'Welcome to Athena!',
        message: 'I\'m your disaster management expert. Ask me about emergency preparedness, or use the quick actions above.'
      },
      healthcare: {
        icon: '🩺',
        title: 'Welcome to Dr. Rivera!',
        message: 'I\'m your medical advisor. Ask me about health questions, symptoms, and wellness guidance.'
      },
      legal: {
        icon: '⚖️',
        title: 'Welcome to Attorney Chen!',
        message: 'I\'m your legal consultant. Ask me about legal matters, rights, and legal consultation.'
      }
    };
    
    return welcomeData[domain] || welcomeData.disaster;
  };

  // Domain-specific input placeholders
  const getInputPlaceholder = () => {
    const placeholders = {
      disaster: "Ask about disaster preparedness...",
      healthcare: "Ask about health concerns...",
      legal: "Ask about legal matters..."
    };
    
    return placeholders[domain] || placeholders.disaster;
  };

  // Direct Action Buttons Component with Synchronized Speech
  const DirectActionButtons = ({ message, messageId }) => {
    const [copied, setCopied] = useState(false);
    const isThisMessageSpeaking = currentlySpeaking === messageId;

    const copyToClipboard = async () => {
      try {
        // Clean the message before copying (remove \n and markdown)
        const cleanMessage = message.replace(/\\n/g, '\n').replace(/\*\*(.*?)\*\*/g, '$1');
        await navigator.clipboard.writeText(cleanMessage);
        setCopied(true);
        
        if (window.athenaSounds?.success) {
          window.athenaSounds.success();
        }
        
        setTimeout(() => setCopied(false), 2000);
      } catch (error) {
        console.error('Copy failed:', error);
      }
    };

    const shareMessage = async () => {
      const cleanMessage = message.replace(/\\n/g, '\n').replace(/\*\*(.*?)\*\*/g, '$1');
      
      if (navigator.share) {
        try {
          await navigator.share({
            title: `${domain.charAt(0).toUpperCase() + domain.slice(1)} Expert Advice`,
            text: cleanMessage
          });
        } catch (error) {
          if (error.name !== 'AbortError') {
            copyToClipboard();
          }
        }
      } else {
        copyToClipboard();
      }
    };

    const printMessage = () => {
      const printWindow = window.open('', '_blank');
      const expertNames = {
        disaster: 'Athena - Disaster Specialist',
        healthcare: 'Dr. Alex Rivera - Medical Advisor',
        legal: 'Attorney Sam Chen - Legal Consultant'
      };
      
      // Clean and format message for printing
      const cleanMessage = message.replace(/\\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      
      printWindow.document.write(`
        <html>
          <head>
            <title>${expertNames[domain]} Advice</title>
            <style>
              body { font-family: Arial, sans-serif; padding: 20px; max-width: 600px; line-height: 1.6; }
              h2 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }
              .content { background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }
              .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 14px; color: #666; }
              strong { font-weight: 700; color: #2d3748; }
            </style>
          </head>
          <body>
            <h2>${domain === 'disaster' ? '🚨' : domain === 'healthcare' ? '🩺' : '⚖️'} ${expertNames[domain]}</h2>
            <div class="content">
              <div>${cleanMessage}</div>
            </div>
            <div class="footer">
              <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
              <p><strong>⚠️ Important:</strong> This is AI-generated guidance. 
              ${domain === 'disaster' ? 'For emergencies, call 911.' : 
                domain === 'healthcare' ? 'For medical emergencies, call 911 or see a doctor.' : 
                'For urgent legal matters, consult a licensed attorney.'}</p>
            </div>
          </body>
        </html>
      `);
      printWindow.document.close();
      setTimeout(() => {
        printWindow.focus();
        printWindow.print();
        printWindow.close();
      }, 500);
    };

    return (
      <div className="direct-action-buttons">
        <button 
          onClick={copyToClipboard} 
          className="direct-action-btn" 
          title="Copy to clipboard"
        >
          {copied ? '✅ Copied' : '📋 Copy'}
        </button>
        
        <button 
          onClick={shareMessage} 
          className="direct-action-btn" 
          title="Share this advice"
        >
          📤 Share
        </button>
        
        <button 
          onClick={printMessage} 
          className="direct-action-btn" 
          title="Print this advice"
        >
          🖨️ Print
        </button>
        
        {/* SYNCHRONIZED READ BUTTON */}
        <button 
          onClick={() => handleReadAloud(message, messageId)} 
          className={`direct-action-btn ${isThisMessageSpeaking ? 'speaking' : ''}`}
          title={isThisMessageSpeaking ? "Stop reading" : "Read this aloud"}
          style={{
            background: isThisMessageSpeaking ? '#ef4444' : undefined,
            color: isThisMessageSpeaking ? 'white' : undefined,
            borderColor: isThisMessageSpeaking ? '#ef4444' : undefined,
            animation: isThisMessageSpeaking ? 'pulse 1s infinite' : undefined
          }}
        >
          {isThisMessageSpeaking ? '⏹️ Stop' : '🔊 Read'}
        </button>
      </div>
    );
  };

  const welcomeMessage = getWelcomeMessage();

  return (
    <div className="whatsapp-chat">
      {/* Messages Area */}
      <div className="chat-messages whatsapp-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <div className="welcome-content">
              <div className="athena-avatar">{welcomeMessage.icon}</div>
              <div className="welcome-text">
                <h3>{welcomeMessage.title}</h3>
                <p>{welcomeMessage.message}</p>
              </div>
            </div>
          </div>
        )}
        
        {messages.map((message) => (
          <div key={message.id} className={`message-container ${message.isUser ? 'user-message' : 'athena-message'}`}>
            {message.isUser ? (
              <div className="user-bubble">
                <div className="message-content">
                  {formatMessage(message.message)}
                </div>
                <div className="message-time user-time">
                  {formatTime(message.timestamp)}
                </div>
              </div>
            ) : (
              <div className="athena-bubble">
                <div className="athena-header">
                  <div className="athena-avatar small">
                    {domain === 'disaster' ? '🚨' : domain === 'healthcare' ? '🩺' : '⚖️'}
                  </div>
                  <span className="athena-name">
                    {domain === 'disaster' ? 'Athena' : domain === 'healthcare' ? 'Dr. Rivera' : 'Attorney Chen'}
                  </span>
                </div>
                <div className="message-content">
                  {formatMessage(message.response)}
                </div>
                {/* SYNCHRONIZED ACTION BUTTONS */}
                <DirectActionButtons message={message.response} messageId={message.id} />
                <div className="message-time athena-time">
                  {formatTime(message.timestamp)}
                </div>
              </div>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="message-container athena-message">
            <div className="athena-bubble typing">
              <div className="athena-header">
                <div className="athena-avatar small">
                  {domain === 'disaster' ? '🚨' : domain === 'healthcare' ? '🩺' : '⚖️'}
                </div>
                <span className="athena-name">
                  {domain === 'disaster' ? 'Athena' : domain === 'healthcare' ? 'Dr. Rivera' : 'Attorney Chen'}
                </span>
              </div>
              <div className="typing-indicator">
                <div className="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span className="typing-text">typing...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area with Synchronized Voice Controls */}
      <form onSubmit={handleSubmit} className="whatsapp-input">
        <div className="input-container">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={getInputPlaceholder()}
            className="whatsapp-input-field"
            disabled={isLoading}
          />
          
          {/* Voice Controls - SYNCHRONIZED */}
          <div className="voice-controls">
            {voiceConfig.isSupported && (
              <>
                {/* Microphone for voice input */}
                <button
                  type="button"
                  className={`voice-btn ${voiceConfig.isRecording ? 'recording' : ''}`}
                  onClick={voiceConfig.isRecording ? handleVoiceStop : handleVoiceStart}
                  title={voiceConfig.isRecording ? 'Stop recording' : 'Voice input'}
                >
                  {voiceConfig.isRecording ? '🔴' : '🎤'}
                </button>
                
                {/* SYNCHRONIZED Auto Read-Aloud Button */}
                <button
                  type="button"
                  className="voice-btn"
                  onClick={toggleAutoReadAloud}
                  title={`Auto read-aloud: ${autoReadAloud ? 'ON' : 'OFF'}${currentlySpeaking ? ' (Currently reading)' : ''}`}
                  style={{ 
                    background: autoReadAloud ? '#10b981' : '#6b7280',
                    opacity: currentlySpeaking ? '0.7' : '1',
                    animation: currentlySpeaking ? 'pulse 1s infinite' : undefined
                  }}
                >
                  {currentlySpeaking ? '⏹️' : (autoReadAloud ? '🔊' : '🔇')}
                </button>
              </>
            )}
          </div>
          
          <button 
            type="submit" 
            className="send-btn"
            disabled={isLoading || !inputValue.trim()}
          >
            {isLoading ? <div className="loading-spinner small"></div> : '📤'}
          </button>
        </div>
      </form>

      {/* Voice Status - Shows Synchronized State */}
      {voiceConfig.isRecording && (
        <div className="voice-status recording">
          🎤 Listening... speak now
        </div>
      )}
      
      {autoReadAloud && (
        <div className="voice-status enabled">
          🔊 Auto read-aloud enabled {currentlySpeaking ? '(Currently reading)' : ''}
        </div>
      )}

      {currentlySpeaking && !autoReadAloud && (
        <div className="voice-status enabled">
          🔊 Reading message aloud...
        </div>
      )}
    </div>
  );
};

export default ChatInterface;

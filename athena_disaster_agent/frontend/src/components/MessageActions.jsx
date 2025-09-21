import React, { useState } from 'react';

const MessageActions = ({ message, isAthenaMessage }) => {
  const [showActions, setShowActions] = useState(false);
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      
      // Play success sound
      if (window.athenaSounds?.success) {
        window.athenaSounds.success();
      }
      
      // Reset copied state
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const shareMessage = async (text) => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Athena Disaster Advice',
          text: text,
          url: window.location.href
        });
        
        if (window.athenaSounds?.success) {
          window.athenaSounds.success();
        }
      } catch (error) {
        if (error.name !== 'AbortError') {
          console.error('Sharing failed:', error);
        }
      }
    } else {
      // Fallback: copy to clipboard
      copyToClipboard(text);
    }
  };

  const printMessage = () => {
    const printWindow = window.open('', '_blank');
    const timestamp = new Date().toLocaleString();
    
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Athena Disaster Response</title>
          <style>
            body { 
              font-family: Arial, sans-serif; 
              max-width: 600px; 
              margin: 40px auto; 
              padding: 20px;
              line-height: 1.6;
            }
            .header { 
              border-bottom: 2px solid #2563eb; 
              margin-bottom: 20px; 
              padding-bottom: 10px;
            }
            .message { 
              background: #f8fafc; 
              padding: 15px; 
              border-radius: 8px; 
              margin: 10px 0;
            }
            .timestamp { 
              color: #666; 
              font-size: 0.9em; 
              margin-top: 10px;
            }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>🚨 Athena Disaster Response</h1>
            <p>Emergency Preparedness Guidance</p>
          </div>
          <div class="message">
            <h3>Disaster Management Advice:</h3>
            <p>${message.replace(/\n/g, '<br>')}</p>
            <div class="timestamp">Generated: ${timestamp}</div>
          </div>
          <div style="margin-top: 30px; font-size: 0.9em; color: #666;">
            <p><strong>⚠️ Important:</strong> This guidance is for preparedness purposes. 
            For immediate life-threatening emergencies, always call 911 first.</p>
          </div>
        </body>
      </html>
    `);
    
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 250);
    
    if (window.athenaSounds?.success) {
      window.athenaSounds.success();
    }
  };

  if (!isAthenaMessage) return null;

  return (
    <div 
      className="message-actions"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className={`actions-toolbar ${showActions ? 'visible' : ''}`}>
        <button
          onClick={() => copyToClipboard(message)}
          className="action-btn"
          title="Copy message"
        >
          {copied ? '✅' : '📋'}
        </button>
        
        <button
          onClick={() => shareMessage(message)}
          className="action-btn"
          title="Share message"
        >
          📤
        </button>
        
        <button
          onClick={printMessage}
          className="action-btn"
          title="Print message"
        >
          🖨️
        </button>
        
        <button
          onClick={() => {
            if (window.speechSynthesis) {
              const utterance = new SpeechSynthesisUtterance(message);
              utterance.rate = 0.9;
              utterance.pitch = 1.0;
              window.speechSynthesis.speak(utterance);
            }
          }}
          className="action-btn"
          title="Read aloud"
        >
          🔊
        </button>
      </div>
    </div>
  );
};

export default MessageActions;

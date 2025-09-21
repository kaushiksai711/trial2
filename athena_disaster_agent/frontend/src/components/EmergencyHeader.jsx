import React from 'react';

const EmergencyHeader = () => {
  const callEmergency = () => {
    if (window.confirm('This will attempt to call emergency services. Are you sure?')) {
      window.location.href = 'tel:911';
    }
  };

  return (
    <div className="emergency-header">
      <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
        🚨 Emergency Disaster Response
      </h1>
      <p style={{ marginBottom: '1rem', opacity: '0.9' }}>
        For immediate life-threatening emergencies, call 911 first
      </p>
      <button 
        className="btn-emergency" 
        onClick={callEmergency}
        style={{ fontSize: '1.1rem', padding: '0.75rem 2rem' }}
      >
        📞 CALL 911 NOW
      </button>
    </div>
  );
};

export default EmergencyHeader;

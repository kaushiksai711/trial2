import React from 'react';

const DomainTabs = ({ selectedDomain, onDomainChange }) => {
  const domains = [
    {
      id: 'disaster',
      name: 'Disaster',
      icon: '🚨',
      expert: 'Athena',
      color: '#dc2626',
      description: 'Emergency & Safety'
    },
    {
      id: 'healthcare', 
      name: 'Healthcare',
      icon: '🩺',
      expert: 'Dr. Athena',
      color: '#2563eb',
      description: 'Medical & Wellness'
    },
    {
      id: 'legal',
      name: 'Legal',
      icon: '⚖️', 
      expert: 'Attorney Athena',
      color: '#1e40af',
      description: 'Legal Consultation'
    }
  ];

  return (
    <div className="domain-tabs-container">
      <h3 style={{ 
        textAlign: 'center', 
        marginBottom: '1rem',
        color: 'var(--text-primary)',
        fontSize: '1.1rem',
        fontWeight: '600'
      }}>
        🎯 Choose Your Expert Domain
      </h3>
      
      <div className="domain-tabs">
        {domains.map((domain) => (
          <button
            key={domain.id}
            onClick={() => onDomainChange(domain.id)}
            className={`domain-tab ${selectedDomain === domain.id ? 'active' : ''}`}
            style={{
              borderColor: selectedDomain === domain.id ? domain.color : 'var(--border-color)',
              color: selectedDomain === domain.id ? domain.color : 'var(--text-secondary)',
              background: selectedDomain === domain.id ? `${domain.color}10` : 'var(--bg-secondary)'
            }}
          >
            <div className="domain-icon">{domain.icon}</div>
            <div className="domain-info">
              <div className="domain-name">{domain.name}</div>
              <div className="domain-expert">{domain.expert}</div>
              <div className="domain-description">{domain.description}</div>
            </div>
            {selectedDomain === domain.id && (
              <div className="active-indicator" style={{ background: domain.color }}></div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

export default DomainTabs;

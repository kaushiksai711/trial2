import React from 'react';

const DomainExpertHeader = ({ domain, expertName, isLoading }) => {
  const expertData = {
    disaster: {
      avatar: '🚨',
      name: 'Athena',
      title: 'Disaster Response Specialist',
      specialty: 'Emergency preparedness, natural disasters, safety protocols',
      greeting: 'I\'m here to help with disaster preparedness and emergency safety guidance.'
    },
    healthcare: {
      avatar: '🩺',
      name: 'Dr. Athena', 
      title: 'Medical Advisor',
      specialty: 'General medicine, health conditions, wellness guidance',
      greeting: 'I\'m here to provide medical information and health guidance.'
    },
    legal: {
      avatar: '⚖️',
      name: 'Attorney Athena',
      title: 'Legal Consultant', 
      specialty: 'Contract law, family law, employment law, civil matters',
      greeting: 'I\'m here to provide legal information and consultation.'
    }
  };

  const expert = expertData[domain] || expertData.disaster;

  return (
    <div className={`domain-expert-header domain-${domain}`}>
      <div className="expert-avatar">
        {expert.avatar}
      </div>
      
      <div className="expert-name">
        {expert.name}
      </div>
      
      <div className="expert-specialty">
        {expert.title} • {expert.specialty}
      </div>
      
      <div style={{ 
        fontSize: '0.85rem', 
        color: 'var(--text-secondary)', 
        marginTop: '0.5rem',
        fontStyle: 'italic'
      }}>
        {isLoading ? "Thinking..." : expert.greeting}
      </div>
    </div>
  );
};

export default DomainExpertHeader;

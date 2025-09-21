import React from 'react';

const DomainQuickActions = ({ domain, onQuickAction }) => {
  const quickActionsData = {
    disaster: {
      title: '🚨 Emergency Quick Help',
      actions: [
        { id: 'earthquake', text: 'Earthquake Safety', question: 'What should I do during an earthquake?' },
        { id: 'fire', text: 'Fire Emergency', question: 'How do I escape from a fire emergency?' },
        { id: 'flood', text: 'Flood Safety', question: 'What should I do if there\'s flooding?' },
        { id: 'hurricane', text: 'Hurricane Prep', question: 'How do I prepare for a hurricane?' },
        { id: 'emergency-kit', text: 'Emergency Kit', question: 'What should be in my emergency kit?' },
        { id: 'evacuation', text: 'Evacuation Plan', question: 'How do I create an evacuation plan?' },
      ]
    },
    healthcare: {
      title: '🩺 Health Quick Assistance',
      actions: [
        { id: 'chest-pain', text: 'Chest Pain', question: 'I\'m experiencing chest pain, what should I do?' },
        { id: 'first-aid', text: 'First Aid', question: 'What are basic first aid steps I should know?' },
        { id: 'medication', text: 'Medication Info', question: 'How do I safely manage medications?' },
        { id: 'mental-health', text: 'Mental Health', question: 'I\'m feeling anxious and stressed, can you help?' },
        { id: 'wellness', text: 'Wellness Tips', question: 'What are some daily wellness tips for healthy living?' },
        { id: 'symptoms', text: 'Symptom Check', question: 'How do I know when symptoms need medical attention?' },
      ]
    },
    legal: {
      title: '⚖️ Legal Quick Consultation',
      actions: [
        { id: 'contract', text: 'Contract Issues', question: 'I have questions about a contract I need to sign.' },
        { id: 'employment', text: 'Employment Law', question: 'I\'m having issues at work, what are my rights?' },
        { id: 'family-law', text: 'Family Law', question: 'I need guidance on family law matters.' },
        { id: 'tenant-rights', text: 'Tenant Rights', question: 'What are my rights as a tenant?' },
        { id: 'legal-process', text: 'Legal Process', question: 'How do legal proceedings typically work?' },
        { id: 'find-lawyer', text: 'Find Attorney', question: 'How do I find and choose the right attorney?' },
      ]
    }
  };

  const domainData = quickActionsData[domain] || quickActionsData.disaster;

  return (
    <div className={`quick-actions domain-${domain}`}>
      <h3 style={{ 
        fontSize: '1rem', 
        fontWeight: '700', 
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}>
        {domainData.title}
      </h3>
      
      <div className="quick-actions-grid">
        {domainData.actions.map((action) => (
          <button
            key={action.id}
            className={`btn-${domain}-quick`}
            onClick={() => onQuickAction(action.question)}
          >
            {action.text}
          </button>
        ))}
      </div>
    </div>
  );
};

export default DomainQuickActions;

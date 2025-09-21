import React from 'react';

const DisasterQuickActions = ({ onQuickAction }) => {
  const quickActions = [
    { id: 'earthquake', text: 'Earthquake Safety', question: 'What should I do during an earthquake?' },
    { id: 'hurricane', text: 'Hurricane Prep', question: 'How do I prepare for a hurricane?' },
    { id: 'flood', text: 'Flood Safety', question: 'What should I do if there\'s flooding?' },
    { id: 'wildfire', text: 'Wildfire Escape', question: 'How do I evacuate from a wildfire?' },
    { id: 'emergency-kit', text: 'Emergency Kit', question: 'What should be in my emergency kit?' },
    { id: 'evacuation', text: 'Evacuation Plan', question: 'How do I create an evacuation plan?' },
  ];

  return (
    <div className="quick-actions">
      <h3>🚀 Quick Disaster Help</h3>
      <div className="quick-actions-grid">
        {quickActions.map((action) => (
          <button
            key={action.id}
            className="btn-disaster"
            onClick={() => onQuickAction(action.question)}
          >
            {action.text}
          </button>
        ))}
      </div>
    </div>
  );
};

export default DisasterQuickActions;

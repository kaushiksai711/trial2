import React from 'react';

const StatusIndicator = ({ status }) => {
  if (!status) return null;

  const getStatusInfo = () => {
    if (status.health?.status === 'healthy' && status.metta?.status === 'active') {
      return {
        className: 'status-healthy',
        icon: '✅',
        text: 'Athena is online and ready',
        detail: 'MeTTa dialog-agent active'
      };
    } else if (status.health?.status === 'healthy') {
      return {
        className: 'status-warning',
        icon: '⚠️',
        text: 'Backend online, MeTTa initializing',
        detail: 'Some features may be limited'
      };
    } else {
      return {
        className: 'status-error',
        icon: '❌',
        text: 'Connection issues detected',
        detail: 'Check backend server status'
      };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className={`status-indicator ${statusInfo.className}`}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span>{statusInfo.icon}</span>
        <div>
          <div style={{ fontWeight: '600', fontSize: '0.875rem' }}>
            {statusInfo.text}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
            {statusInfo.detail}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatusIndicator;

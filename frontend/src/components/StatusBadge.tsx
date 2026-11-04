import React from 'react';
import { ServiceStatus } from '../api/types';

export const StatusBadge: React.FC<{ status: ServiceStatus }> = ({ status }) => {
  const getBadgeClass = () => {
    switch (status) {
      case 'healthy':
        return 'badge-healthy';
      case 'degraded':
        return 'badge-degraded';
      case 'down':
        return 'badge-down';
      default:
        return 'badge-unknown';
    }
  };

  return (
    <span className={`badge ${getBadgeClass()}`}>
      <span className="pulse-dot" />
      {status}
    </span>
  );
};

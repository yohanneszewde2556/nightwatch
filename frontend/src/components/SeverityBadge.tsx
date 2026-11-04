import React from 'react';
import { Severity } from '../api/types';

export const SeverityBadge: React.FC<{ severity: Severity }> = ({ severity }) => {
  const getBadgeClass = () => {
    switch (severity) {
      case 'P1':
        return 'badge-p1';
      case 'P2':
        return 'badge-p2';
      case 'P3':
        return 'badge-p3';
      default:
        return 'badge-unknown';
    }
  };

  return <span className={`badge ${getBadgeClass()}`}>{severity}</span>;
};

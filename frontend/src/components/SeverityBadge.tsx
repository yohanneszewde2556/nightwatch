import React from 'react';
import { Severity } from '../api/types';
import { Chip, ChipVariant } from './ui/Chip';

export const SeverityBadge: React.FC<{ severity: Severity }> = ({ severity }) => {
  const variantMap: Record<Severity, ChipVariant> = {
    P1: 'critical',
    P2: 'degraded',
    P3: 'neutral',
  };

  return (
    <Chip variant={variantMap[severity] || 'neutral'} size="sm">
      {severity}
    </Chip>
  );
};

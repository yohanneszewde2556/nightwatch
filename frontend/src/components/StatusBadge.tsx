import React from 'react';
import { ServiceStatus } from '../api/types';
import { Chip, ChipVariant } from './ui/Chip';
import { StatusDot } from './ui/StatusDot';

export const StatusBadge: React.FC<{ status: ServiceStatus }> = ({ status }) => {
  const variantMap: Record<ServiceStatus, ChipVariant> = {
    healthy: 'healthy',
    degraded: 'degraded',
    down: 'critical',
    unknown: 'neutral',
  };

  const variant = variantMap[status] || 'neutral';

  return (
    <Chip
      variant={variant}
      size="sm"
      icon={<StatusDot status={variant} size={6} pulse={status === 'down'} />}
    >
      {status}
    </Chip>
  );
};

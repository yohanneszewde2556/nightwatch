import React from 'react';

export interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '16px',
  borderRadius = 'var(--radius-control)',
  className = '',
  style,
}) => {
  return (
    <div
      className={`nw-skeleton ${className}`}
      style={{
        width,
        height,
        borderRadius,
        backgroundColor: 'var(--bg-raised)',
        backgroundImage: 'linear-gradient(90deg, var(--bg-raised) 0%, var(--bg-hover) 50%, var(--bg-raised) 100%)',
        backgroundSize: '200% 100%',
        animation: 'nw-shimmer 1.8s infinite',
        display: 'inline-block',
        ...style,
      }}
      aria-hidden="true"
    />
  );
};

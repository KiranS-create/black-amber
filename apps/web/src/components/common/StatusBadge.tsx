import React from 'react';
import { DataSourceOrigin } from '../../types';

interface StatusBadgeProps {
  label: string;
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'primary';
  size?: 'xs' | 'sm' | 'md';
  dot?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  label,
  variant = 'neutral',
  size = 'sm',
  dot = false,
  className = '',
  style = {}
}) => {
  const getColors = () => {
    switch (variant) {
      case 'success':
        return {
          bg: 'var(--success-subtle)',
          color: 'var(--success-text)',
          border: 'var(--success-border)',
          dotColor: 'var(--success)'
        };
      case 'warning':
        return {
          bg: 'var(--warning-subtle)',
          color: 'var(--warning-text)',
          border: 'var(--warning-border)',
          dotColor: 'var(--warning)'
        };
      case 'danger':
        return {
          bg: 'var(--danger-subtle)',
          color: 'var(--danger-text)',
          border: 'var(--danger-border)',
          dotColor: 'var(--danger)'
        };
      case 'info':
        return {
          bg: 'var(--info-subtle)',
          color: 'var(--info-text)',
          border: 'var(--info-border)',
          dotColor: 'var(--info)'
        };
      case 'primary':
        return {
          bg: 'var(--primary-subtle)',
          color: 'var(--primary-text)',
          border: 'var(--primary-border)',
          dotColor: 'var(--primary)'
        };
      case 'neutral':
      default:
        return {
          bg: 'var(--surface-hover)',
          color: 'var(--text-secondary)',
          border: 'var(--border)',
          dotColor: 'var(--text-tertiary)'
        };
    }
  };

  const colors = getColors();

  const sizeStyles = {
    xs: { padding: '2px 6px', fontSize: '10px', height: '18px' },
    sm: { padding: '2px 8px', fontSize: '11.5px', height: '22px' },
    md: { padding: '4px 10px', fontSize: '12.5px', height: '26px' }
  }[size];

  return (
    <span
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        borderRadius: 'var(--radius-full)',
        backgroundColor: colors.bg,
        color: colors.color,
        border: `1px solid ${colors.border}`,
        fontWeight: 600,
        letterSpacing: '0.01em',
        lineHeight: 1,
        whiteSpace: 'nowrap',
        boxSizing: 'border-box',
        ...sizeStyles,
        ...style
      }}
    >
      {dot && (
        <span
          style={{
            width: size === 'xs' ? '5px' : '6px',
            height: size === 'xs' ? '5px' : '6px',
            borderRadius: '50%',
            backgroundColor: colors.dotColor,
            flexShrink: 0
          }}
        />
      )}
      {label}
    </span>
  );
};

export const OriginBadge: React.FC<{ origin?: DataSourceOrigin; style?: React.CSSProperties }> = ({
  origin,
  style
}) => {
  if (!origin) return null;

  switch (origin) {
    case 'REAL_BACKEND_RESULT':
      return <StatusBadge label="REAL BACKEND" variant="success" size="xs" dot style={style} />;
    case 'REAL_LOCAL_COMPUTATION':
      return <StatusBadge label="LOCAL COMPUTATION" variant="primary" size="xs" dot style={style} />;
    case 'SIMULATED_DEMO_SCENARIO':
      return <StatusBadge label="SIMULATED SCENARIO" variant="warning" size="xs" dot style={style} />;
    case 'PLACEHOLDER_UNAVAILABLE':
      return <StatusBadge label="UNAVAILABLE" variant="danger" size="xs" dot style={style} />;
    default:
      return <StatusBadge label={origin} variant="neutral" size="xs" style={style} />;
  }
};

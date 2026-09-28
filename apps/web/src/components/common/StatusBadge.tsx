import React from 'react';
import { CheckCircle2, AlertCircle, XCircle, Clock, Info, ShieldCheck } from 'lucide-react';
import { DataSourceOrigin } from '../../types';

interface StatusBadgeProps {
  label: string;
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'primary';
  size?: 'xs' | 'sm' | 'md';
  dot?: boolean;
  icon?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * StatusBadge Component — Forensic Luxury Edition
 * Text + subtle indicator, high WCAG contrast, no neon bloom.
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({
  label,
  variant = 'neutral',
  size = 'sm',
  dot = false,
  icon = false,
  className = '',
  style = {}
}) => {
  const getSemanticDetails = () => {
    switch (variant) {
      case 'success':
        return {
          bg: 'var(--success-subtle)',
          color: 'var(--success-text)',
          border: 'var(--success-border)',
          dotClass: 'status-dot-verified',
          IconComponent: CheckCircle2
        };
      case 'warning':
        return {
          bg: 'var(--warning-subtle)',
          color: 'var(--warning-text)',
          border: 'var(--warning-border)',
          dotClass: 'status-dot-warning',
          IconComponent: AlertCircle
        };
      case 'danger':
        return {
          bg: 'var(--danger-subtle)',
          color: 'var(--danger-text)',
          border: 'var(--danger-border)',
          dotClass: 'status-dot-danger',
          IconComponent: XCircle
        };
      case 'info':
        return {
          bg: 'var(--info-subtle)',
          color: 'var(--info-text)',
          border: 'var(--info-border)',
          dotClass: 'status-dot-info',
          IconComponent: Info
        };
      case 'primary':
        return {
          bg: 'var(--primary-subtle)',
          color: 'var(--primary-text)',
          border: 'var(--primary-border)',
          dotClass: 'status-dot-info',
          IconComponent: ShieldCheck
        };
      case 'neutral':
      default:
        return {
          bg: 'rgba(255, 255, 255, 0.04)',
          color: 'var(--text-secondary)',
          border: 'var(--border)',
          dotClass: 'status-dot-neutral',
          IconComponent: Clock
        };
    }
  };

  const { bg, color, border, dotClass, IconComponent } = getSemanticDetails();

  const sizeStyles = {
    xs: { padding: '2px 6px', fontSize: '11px', height: '20px', iconSize: 11 },
    sm: { padding: '3px 8px', fontSize: '12px', height: '22px', iconSize: 12 },
    md: { padding: '4px 10px', fontSize: '13px', height: '26px', iconSize: 13 }
  }[size];

  return (
    <span
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        borderRadius: 'var(--radius-xs)',
        backgroundColor: bg,
        border: `1px solid ${border}`,
        color: color,
        fontWeight: 500,
        lineHeight: 1,
        whiteSpace: 'nowrap',
        ...sizeStyles,
        ...style
      }}
    >
      {dot && <span className={`status-dot ${dotClass}`} />}
      {icon && <IconComponent size={sizeStyles.iconSize} style={{ flexShrink: 0 }} />}
      <span>{label}</span>
    </span>
  );
};

export const OriginBadge: React.FC<{ origin?: DataSourceOrigin }> = ({ origin }) => {
  if (!origin) return null;

  switch (origin) {
    case 'REAL_BACKEND_RESULT':
      return <StatusBadge label="Backend verified" variant="success" size="xs" dot />;
    case 'REAL_LOCAL_COMPUTATION':
      return <StatusBadge label="Local computation" variant="primary" size="xs" dot />;
    case 'SIMULATED_DEMO_SCENARIO':
      return <StatusBadge label="Simulation only" variant="warning" size="xs" dot />;
    case 'PLACEHOLDER_UNAVAILABLE':
      return <StatusBadge label="Unavailable" variant="neutral" size="xs" dot />;
    default:
      return null;
  }
};

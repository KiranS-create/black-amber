import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: React.ComponentType<any>;
  status?: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'primary';
  badge?: string;
}

/**
 * MetricCard Component — Forensic Luxury Edition
 * Compact, restrained operational indicator with subtle elevation and typography.
 */
export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  icon: Icon,
  status = 'neutral',
  badge
}) => {
  const getAccentColor = () => {
    switch (status) {
      case 'success':
        return 'var(--success-text)';
      case 'warning':
        return 'var(--warning-text)';
      case 'danger':
        return 'var(--danger-text)';
      case 'info':
        return 'var(--info-text)';
      case 'primary':
        return 'var(--primary-text)';
      case 'neutral':
      default:
        return 'var(--text-secondary)';
    }
  };

  const accentColor = getAccentColor();

  return (
    <div
      className="workstation-card"
      style={{
        padding: 'var(--space-4)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        borderRadius: 'var(--radius-sm)',
        minHeight: '92px'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
        <span
          style={{
            fontSize: 'var(--text-xs)',
            fontWeight: 500,
            color: 'var(--text-tertiary)'
          }}
        >
          {label}
        </span>
        {badge && (
          <span
            style={{
              fontSize: '11px',
              color: accentColor,
              fontWeight: 500,
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              padding: '1px 6px',
              borderRadius: 'var(--radius-xs)',
              border: '1px solid var(--border-subtle)'
            }}
          >
            {badge}
          </span>
        )}
        {Icon && !badge && (
          <Icon size={15} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
        <span
          style={{
            fontSize: 'var(--text-xl)',
            fontWeight: 700,
            color: 'var(--text)',
            letterSpacing: '-0.02em',
            lineHeight: 1.1
          }}
        >
          {value}
        </span>
      </div>

      {subtext && (
        <div
          style={{
            fontSize: '11.5px',
            color: 'var(--text-secondary)',
            marginTop: '4px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}
        >
          {subtext}
        </div>
      )}
    </div>
  );
};

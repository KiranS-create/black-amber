import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: React.ComponentType<any>;
  status?: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'primary';
  badge?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  icon: Icon,
  status = 'neutral',
  badge
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'var(--success)';
      case 'warning':
        return 'var(--warning)';
      case 'danger':
        return 'var(--danger)';
      case 'info':
        return 'var(--info)';
      case 'neutral':
      default:
        return 'var(--primary)';
    }
  };

  return (
    <div
      style={{
        backgroundColor: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-4) var(--space-5)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        boxShadow: 'var(--shadow-sm)',
        transition: 'border-color var(--transition-fast)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
        <span
          style={{
            fontSize: 'var(--text-xs)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            color: 'var(--text-tertiary)'
          }}
        >
          {label}
        </span>
        {Icon && (
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: getStatusColor()
            }}
          >
            <Icon size={15} />
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: 'var(--space-1)' }}>
        <span
          style={{
            fontSize: 'var(--text-2xl)',
            fontWeight: 700,
            color: 'var(--text)',
            letterSpacing: '-0.02em',
            lineHeight: 1.1
          }}
        >
          {value}
        </span>
        {badge && (
          <span
            style={{
              fontSize: '11px',
              fontWeight: 600,
              padding: '1px 6px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: 'var(--surface-hover)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border)'
            }}
          >
            {badge}
          </span>
        )}
      </div>

      {subtext && (
        <div
          style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}
        >
          {subtext}
        </div>
      )}
    </div>
  );
};

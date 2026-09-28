import React from 'react';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  primaryAction?: {
    label: string;
    onClick: () => void;
    icon?: LucideIcon;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
    icon?: LucideIcon;
  };
  className?: string;
  style?: React.CSSProperties;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  primaryAction,
  secondaryAction,
  className = '',
  style = {}
}) => {
  return (
    <div
      className={`workstation-card ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: 'var(--space-12) var(--space-6)',
        backgroundColor: 'var(--surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-sm)',
        minHeight: '260px',
        ...style
      }}
    >
      {/* Subtle abstract geometric emblem */}
      <div
        style={{
          width: '44px',
          height: '44px',
          borderRadius: 'var(--radius-xs)',
          backgroundColor: 'var(--surface-elevated)',
          border: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-tertiary)',
          marginBottom: 'var(--space-4)'
        }}
      >
        {Icon ? (
          <Icon size={20} strokeWidth={1.5} />
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <line x1="3" y1="9" x2="21" y2="9" />
            <line x1="9" y1="21" x2="9" y2="9" />
          </svg>
        )}
      </div>

      {/* Title */}
      <h3
        style={{
          fontSize: '15px',
          fontWeight: 600,
          color: 'var(--text)',
          marginBottom: 'var(--space-1)',
          letterSpacing: '-0.01em'
        }}
      >
        {title}
      </h3>

      {/* Concise One-Sentence Description */}
      <p
        style={{
          fontSize: '13px',
          color: 'var(--text-secondary)',
          maxWidth: '420px',
          margin: '0 0 var(--space-6) 0',
          lineHeight: 1.5
        }}
      >
        {description}
      </p>

      {/* Actions */}
      {(primaryAction || secondaryAction) && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          {primaryAction && (
            <button
              onClick={primaryAction.onClick}
              className="btn-primary"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '0 16px',
                height: '36px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {primaryAction.icon && <primaryAction.icon size={15} />}
              {primaryAction.label}
            </button>
          )}

          {secondaryAction && (
            <button
              onClick={secondaryAction.onClick}
              className="btn-secondary"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '0 16px',
                height: '36px',
                fontSize: '13px',
                fontWeight: 500,
                cursor: 'pointer'
              }}
            >
              {secondaryAction.icon && <secondaryAction.icon size={14} />}
              <span>{secondaryAction.label}</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};

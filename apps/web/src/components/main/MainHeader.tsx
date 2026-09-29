import React from 'react';
import { UserSession } from '../../types';
import { Sun, Moon, LogOut, Shield } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

interface MainHeaderProps {
  currentSection: string;
  userSession: UserSession | null;
  isDemoMode: boolean;
  onSignOut: () => void;
  onOpenSettings: () => void;
}

export const MainHeader: React.FC<MainHeaderProps> = ({
  currentSection,
  userSession,
  isDemoMode,
  onSignOut,
  onOpenSettings
}) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="main-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
          AegisTrace
        </span>
        <span style={{ color: 'var(--main-text-tertiary)', fontSize: '13px' }}>/</span>
        <span style={{ fontSize: '13px', color: 'var(--main-text-secondary)', textTransform: 'capitalize' }}>
          {currentSection}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {isDemoMode && (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '3px 8px',
              borderRadius: '4px',
              background: 'var(--main-amber-subtle)',
              border: '1px solid rgba(245, 158, 11, 0.25)',
              color: 'var(--main-amber)',
              fontSize: '11px',
              fontWeight: 600,
              letterSpacing: '0.04em'
            }}
          >
            DEMO DATA
          </div>
        )}

        <button
          onClick={toggleTheme}
          className="main-btn-ghost"
          title="Toggle interface theme"
          aria-label="Toggle interface theme"
        >
          {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        </button>

        {userSession && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', paddingLeft: '8px', borderLeft: '1px solid var(--main-border)' }}>
            <button
              onClick={onOpenSettings}
              className="main-btn-ghost"
              style={{ padding: '4px 8px', fontSize: '12px' }}
              title="Workstation Settings"
            >
              <div
                style={{
                  width: '22px',
                  height: '22px',
                  borderRadius: '50%',
                  background: 'var(--main-surface-elevated)',
                  border: '1px solid var(--main-border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  fontWeight: 600,
                  color: 'var(--main-text-primary)',
                  marginRight: '6px'
                }}
              >
                {userSession.display_name ? userSession.display_name.charAt(0).toUpperCase() : 'A'}
              </div>
              <span style={{ color: 'var(--main-text-primary)', fontWeight: 500 }}>
                {userSession.display_name || userSession.email}
              </span>
            </button>

            <button
              onClick={onSignOut}
              className="main-btn-ghost"
              title="Sign out of workstation"
              aria-label="Sign out of workstation"
              style={{ color: 'var(--main-text-tertiary)' }}
            >
              <LogOut size={15} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

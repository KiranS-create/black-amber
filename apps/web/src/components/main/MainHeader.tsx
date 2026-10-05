import React from 'react';
import { UserSession } from '../../types';
import { Sun, Moon, LogOut } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

interface MainHeaderProps {
  currentSection: string;
  userSession: UserSession | null;
  isDemoMode?: boolean;
  onSignOut: () => void;
  onOpenSettings: () => void;
}

export const MainHeader: React.FC<MainHeaderProps> = ({
  currentSection,
  userSession,
  onSignOut,
  onOpenSettings
}) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="main-header" style={{ height: '48px', padding: '0 20px', borderBottom: '1px solid var(--main-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--main-surface)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', letterSpacing: '-0.01em' }}>
          AegisTrace
        </span>
        <span style={{ color: 'var(--main-text-tertiary)', fontSize: '12px' }}>/</span>
        <span style={{ fontSize: '12.5px', color: 'var(--main-text-secondary)', textTransform: 'capitalize' }}>
          {currentSection}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Subtle Operational Status */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '3px 9px',
            borderRadius: '12px',
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            color: 'var(--main-jade)',
            fontSize: '11px',
            fontWeight: 500
          }}
        >
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10B981', display: 'inline-block' }} />
          <span>Operational</span>
        </div>

        {/* Theme Switcher */}
        <button
          onClick={toggleTheme}
          className="main-btn-ghost"
          title="Toggle theme"
          aria-label="Toggle theme"
          style={{ padding: '6px', color: 'var(--main-text-secondary)' }}
        >
          {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
        </button>

        {/* User Session Profile & Signout */}
        {userSession && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', paddingLeft: '8px', borderLeft: '1px solid var(--main-border)' }}>
            <button
              onClick={onOpenSettings}
              className="main-btn-ghost"
              style={{ padding: '3px 8px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
              title="Settings"
            >
              <div
                style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  background: 'var(--main-surface-elevated)',
                  border: '1px solid var(--main-border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '10px',
                  fontWeight: 600,
                  color: 'var(--main-text-primary)'
                }}
              >
                {userSession.display_name ? userSession.display_name.charAt(0).toUpperCase() : 'A'}
              </div>
              <span style={{ color: 'var(--main-text-primary)', fontWeight: 500, fontSize: '12px' }}>
                {userSession.display_name || userSession.email}
              </span>
            </button>

            <button
              onClick={onSignOut}
              className="main-btn-ghost"
              title="Sign out"
              aria-label="Sign out"
              style={{ padding: '6px', color: 'var(--main-text-tertiary)' }}
            >
              <LogOut size={13} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

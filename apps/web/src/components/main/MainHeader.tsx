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
    <header 
      className="main-header" 
      style={{ 
        height: '52px', 
        padding: '0 24px', 
        borderBottom: '1px solid var(--main-border)', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        background: 'var(--main-surface)',
        backdropFilter: 'blur(28px) saturate(180%)',
        WebkitBackdropFilter: 'blur(28px) saturate(180%)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '13px', fontWeight: 650, color: 'var(--main-text-primary)', letterSpacing: '-0.02em' }}>
          AegisTrace
        </span>
        <span style={{ color: 'var(--main-text-tertiary)', fontSize: '12px', opacity: 0.6 }}>/</span>
        <span style={{ fontSize: '12.5px', color: 'var(--main-text-secondary)', fontWeight: 500, letterSpacing: '-0.01em', textTransform: 'capitalize' }}>
          {currentSection}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Apple Status Capsule */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '3px 10px',
            borderRadius: '9999px',
            background: 'var(--main-jade-subtle)',
            border: '1px solid var(--main-jade)',
            color: 'var(--main-jade)',
            fontSize: '11px',
            fontWeight: 600,
            letterSpacing: '0.02em'
          }}
        >
          <span className="radar-dot" style={{ width: '5px', height: '5px' }} />
          <span>Operational</span>
        </div>

        {/* Theme Switcher - Circular Apple Button */}
        <button
          onClick={toggleTheme}
          className="main-btn-ghost"
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          aria-label="Toggle theme"
          style={{ 
            width: '28px', 
            height: '28px', 
            padding: 0, 
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--main-text-secondary)',
            border: '1px solid var(--main-border)',
            background: 'var(--main-surface-hover)'
          }}
        >
          {theme === 'dark' ? <Sun size={13} /> : <Moon size={13} />}
        </button>

        {/* User Session Profile & Signout Capsule */}
        {userSession && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', paddingLeft: '8px', borderLeft: '1px solid var(--main-border)' }}>
            <button
              onClick={onOpenSettings}
              className="main-btn-ghost"
              style={{ 
                padding: '3px 10px', 
                fontSize: '12px', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px',
                borderRadius: '9999px',
                border: '1px solid var(--main-border)',
                background: 'var(--main-surface)'
              }}
              title="Settings"
            >
              <div
                style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #0071E3, #005bb5)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '10px',
                  fontWeight: 700,
                  color: '#FFFFFF'
                }}
              >
                {userSession.display_name ? userSession.display_name.charAt(0).toUpperCase() : 'A'}
              </div>
              <span style={{ color: 'var(--main-text-primary)', fontWeight: 550, fontSize: '12px', letterSpacing: '-0.01em' }}>
                {userSession.display_name || userSession.email}
              </span>
            </button>

            <button
              onClick={onSignOut}
              className="main-btn-ghost"
              title="Sign out"
              aria-label="Sign out"
              style={{ 
                width: '28px', 
                height: '28px', 
                padding: 0, 
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--main-text-tertiary)' 
              }}
            >
              <LogOut size={13} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

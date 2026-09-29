import React from 'react';
import { 
  ShieldCheck, 
  Search, 
  RotateCcw, 
  Wifi, 
  WifiOff, 
  Sun, 
  Moon, 
  BookOpen,
  UserCheck,
  LogOut
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { UserSession } from '../../types';
import { getExperienceVariant, setExperienceVariant } from '../../variant';

interface TopBarProps {
  isOnline: boolean;
  forceOffline: boolean;
  onToggleForceOffline: (val: boolean) => void;
  onOpenWalkthrough: () => void;
  onResetDemo: () => void;
  onOpenCommandPalette: () => void;
  userSession?: UserSession | null;
  isDemoMode?: boolean;
  onPurgeDemo?: () => void;
  onSignOut?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  isOnline,
  forceOffline,
  onToggleForceOffline,
  onOpenWalkthrough,
  onResetDemo,
  onOpenCommandPalette,
  userSession,
  isDemoMode = false,
  onPurgeDemo,
  onSignOut
}) => {
  const { theme, toggleTheme } = useTheme();
  const activeVariant = getExperienceVariant();

  return (
    <header
      style={{
        height: '52px',
        backgroundColor: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--space-6)',
        position: 'sticky',
        top: 0,
        zIndex: 40
      }}
    >
      {/* Brand Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: 'var(--radius-xs)',
            backgroundColor: 'var(--primary-subtle)',
            border: '1px solid var(--primary-border)',
            color: 'var(--primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}
        >
          <ShieldCheck size={16} />
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span
            style={{
              fontFamily: 'var(--font-family)',
              fontSize: '15px',
              fontWeight: 700,
              color: 'var(--text)',
              letterSpacing: '-0.01em'
            }}
          >
            AegisTrace
          </span>
          <span
            style={{
              fontSize: '11px',
              color: 'var(--text-tertiary)',
              fontWeight: 500
            }}
          >
            Forensic Workstation
          </span>
        </div>
      </div>

      {/* Global Search / Command Palette Trigger (Layer 2 Surface) */}
      <div style={{ flex: 1, maxWidth: '440px', margin: '0 var(--space-6)' }}>
        <button
          onClick={onOpenCommandPalette}
          className="topbar-search-container"
          style={{
            width: '100%',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 10px',
            backgroundColor: 'var(--surface-subtle)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-tertiary)',
            fontSize: 'var(--text-xs)',
            cursor: 'pointer',
            transition: 'border-color var(--transition-fast)'
          }}
          onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--border-strong)')}
          onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Search size={13} style={{ color: 'var(--text-tertiary)' }} />
            <span>Search documents, cases, evidence, or ledger...</span>
          </div>
          <kbd
            style={{
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              padding: '1px 5px',
              borderRadius: 'var(--radius-xs)',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-tertiary)'
            }}
          >
            Ctrl K
          </kbd>
        </button>
      </div>

      {/* System State, Quick Controls & Operator Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Offline Simulation Toggle */}
        <button
          onClick={() => onToggleForceOffline(!forceOffline)}
          title={forceOffline ? 'Switch to live API connection' : 'Switch to standalone offline simulator'}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            height: '28px',
            padding: '0 10px',
            borderRadius: 'var(--radius-xs)',
            backgroundColor: forceOffline ? 'var(--warning-subtle)' : 'var(--success-subtle)',
            border: `1px solid ${forceOffline ? 'var(--warning-border)' : 'var(--success-border)'}`,
            color: forceOffline ? 'var(--warning-text)' : 'var(--success-text)',
            fontSize: '11.5px',
            fontWeight: 500,
            cursor: 'pointer'
          }}
        >
          {forceOffline ? <WifiOff size={12} /> : <Wifi size={12} />}
          <span>{forceOffline ? 'Offline mode' : 'Connected'}</span>
        </button>

        {/* System Architecture Guide */}
        <button
          onClick={onOpenWalkthrough}
          title="Open architecture guide"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            height: '28px',
            padding: '0 10px',
            borderRadius: 'var(--radius-xs)',
            backgroundColor: 'transparent',
            border: '1px solid var(--border)',
            color: 'var(--text-secondary)',
            fontSize: '11.5px',
            fontWeight: 500,
            cursor: 'pointer'
          }}
          onMouseEnter={e => {
            e.currentTarget.style.backgroundColor = 'var(--surface-hover)';
            e.currentTarget.style.color = 'var(--text)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.color = 'var(--text-secondary)';
          }}
        >
          <BookOpen size={12} />
          <span>System guide</span>
        </button>

        {/* Demo Mode Indicator */}
        {isDemoMode && (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '3px 8px',
              backgroundColor: 'rgba(197, 150, 69, 0.15)',
              border: '1px solid rgba(197, 150, 69, 0.4)',
              borderRadius: 'var(--radius-xs)',
              fontSize: '11px',
              fontWeight: 700,
              color: 'var(--warning)',
              letterSpacing: '0.04em'
            }}
          >
            <span>DEMO DATA</span>
            {onPurgeDemo && (
              <button
                onClick={onPurgeDemo}
                title="Purge demonstration data and return to clean state"
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--warning)',
                  cursor: 'pointer',
                  padding: '0 2px',
                  fontSize: '13px',
                  lineHeight: 1,
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                ×
              </button>
            )}
          </div>
        )}

        {/* Experience Variant Switcher Pill */}
        <div 
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            padding: '2px',
            background: 'var(--surface-subtle)',
            border: '1px solid var(--border)',
            borderRadius: '20px',
            marginRight: '6px'
          }}
        >
          <button
            onClick={() => setExperienceVariant('main')}
            title="Switch to the Main Software User Interface"
            style={{
              border: 'none',
              background: activeVariant === 'main' ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
              color: activeVariant === 'main' ? '#0284C7' : 'var(--text-tertiary)',
              fontWeight: activeVariant === 'main' ? 600 : 500,
              fontSize: '11px',
              padding: '3px 9px',
              borderRadius: '16px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              transition: 'all 0.15s ease'
            }}
          >
            <span>✦ Main Workstation</span>
          </button>
          <button
            onClick={() => setExperienceVariant('alternate')}
            title="Active: Alternate Baseline UI"
            style={{
              border: 'none',
              background: activeVariant === 'alternate' ? 'var(--surface)' : 'transparent',
              color: activeVariant === 'alternate' ? 'var(--text)' : 'var(--text-tertiary)',
              fontWeight: activeVariant === 'alternate' ? 600 : 500,
              fontSize: '11px',
              padding: '3px 9px',
              borderRadius: '16px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              boxShadow: activeVariant === 'alternate' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              transition: 'all 0.15s ease'
            }}
          >
            <span>☵ Alternate UI</span>
          </button>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          title="Toggle interface theme"
          style={{
            width: '28px',
            height: '28px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 'var(--radius-xs)',
            backgroundColor: 'transparent',
            border: '1px solid var(--border)',
            color: 'var(--text-tertiary)',
            cursor: 'pointer'
          }}
          onMouseEnter={e => (e.currentTarget.style.color = 'var(--text)')}
          onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-tertiary)')}
        >
          {theme === 'dark' ? <Sun size={13} /> : <Moon size={13} />}
        </button>

        {/* Operator Profile */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            paddingLeft: '6px',
            borderLeft: '1px solid var(--border-subtle)'
          }}
        >
          <div
            style={{
              width: '26px',
              height: '26px',
              borderRadius: 'var(--radius-xs)',
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--text)',
              textTransform: 'uppercase'
            }}
          >
            {userSession?.display_name 
              ? userSession.display_name.substring(0, 2) 
              : userSession?.actor_id ? userSession.actor_id.substring(0, 2) : 'EX'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text)', lineHeight: 1.1 }}>
              {userSession?.display_name || userSession?.email || 'Examiner'}
            </span>
            <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', lineHeight: 1.1, textTransform: 'capitalize' }}>
              {userSession?.role || 'Operator'}
            </span>
          </div>

          {onSignOut && (
            <button
              onClick={onSignOut}
              title="Sign out of workstation"
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-tertiary)',
                cursor: 'pointer',
                padding: '4px',
                marginLeft: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--danger)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-tertiary)')}
            >
              <LogOut size={13} />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

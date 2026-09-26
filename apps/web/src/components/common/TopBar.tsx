import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Search, 
  PlayCircle, 
  RotateCcw, 
  Wifi, 
  WifiOff, 
  Sun, 
  Moon, 
  CheckCircle,
  HelpCircle
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

interface TopBarProps {
  isOnline: boolean;
  forceOffline: boolean;
  onToggleForceOffline: (val: boolean) => void;
  onOpenWalkthrough: () => void;
  onResetDemo: () => void;
  onOpenCommandPalette: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  isOnline,
  forceOffline,
  onToggleForceOffline,
  onOpenWalkthrough,
  onResetDemo,
  onOpenCommandPalette
}) => {
  const { theme, toggleTheme } = useTheme();
  const [profileOpen, setProfileOpen] = useState(false);

  return (
    <header
      style={{
        height: '60px',
        backgroundColor: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--space-6)',
        position: 'sticky',
        top: 0,
        zIndex: 40,
        boxShadow: 'var(--shadow-sm)'
      }}
    >
      {/* Brand & Left Context */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
            textDecoration: 'none',
            color: 'inherit'
          }}
        >
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(37, 99, 235, 0.25)'
            }}
          >
            <ShieldCheck size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span
                style={{
                  fontSize: 'var(--text-lg)',
                  fontWeight: 800,
                  letterSpacing: '-0.02em',
                  color: 'var(--text)',
                  lineHeight: 1.1
                }}
              >
                AegisTrace
              </span>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-xs)',
                  backgroundColor: 'var(--surface-hover)',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border)',
                  lineHeight: 1
                }}
              >
                v2.4 PQC
              </span>
            </div>
            <div
              style={{
                fontSize: '11px',
                color: 'var(--text-tertiary)',
                lineHeight: 1.1,
                marginTop: '1px'
              }}
            >
              Forensic Security Platform
            </div>
          </div>
        </div>
      </div>

      {/* Global Search Bar (Center Trigger) */}
      <div style={{ flex: '1', maxWidth: '440px', margin: '0 var(--space-6)' }}>
        <button
          onClick={onOpenCommandPalette}
          style={{
            width: '100%',
            height: '36px',
            backgroundColor: 'var(--surface-subtle)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md)',
            padding: '0 var(--space-3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            color: 'var(--text-tertiary)',
            fontSize: 'var(--text-xs)',
            transition: 'border-color var(--transition-fast), background var(--transition-fast)'
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-strong)';
            (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-hover)';
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)';
            (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-subtle)';
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Search size={14} style={{ color: 'var(--text-tertiary)' }} />
            <span>Search documents, recipients, or events...</span>
          </div>
          <kbd
            style={{
              padding: '2px 6px',
              fontSize: '10.5px',
              fontFamily: 'var(--font-mono)',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-xs)',
              color: 'var(--text-secondary)'
            }}
          >
            Ctrl K
          </kbd>
        </button>
      </div>

      {/* Right Controls & Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        {/* Connection Status Pill with Toggle */}
        <button
          onClick={() => onToggleForceOffline(!forceOffline)}
          title="Click to toggle between live FastAPI (:8000) and offline demo simulator mode"
          style={{
            height: '32px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '0 10px',
            borderRadius: 'var(--radius-full)',
            backgroundColor: isOnline ? 'var(--success-subtle)' : (forceOffline ? 'var(--warning-subtle)' : 'var(--danger-subtle)'),
            color: isOnline ? 'var(--success-text)' : (forceOffline ? 'var(--warning-text)' : 'var(--danger-text)'),
            border: `1px solid ${isOnline ? 'var(--success-border)' : (forceOffline ? 'var(--warning-border)' : 'var(--danger-border)')}`,
            fontSize: 'var(--text-xs)',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'opacity var(--transition-fast)'
          }}
        >
          {isOnline ? (
            <>
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--success)',
                  display: 'inline-block'
                }}
              />
              <Wifi size={13} />
              <span>LIVE API (:8000)</span>
            </>
          ) : forceOffline ? (
            <>
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--warning)',
                  display: 'inline-block'
                }}
              />
              <WifiOff size={13} />
              <span>OFFLINE SIMULATOR</span>
            </>
          ) : (
            <>
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--danger)',
                  display: 'inline-block'
                }}
              />
              <WifiOff size={13} />
              <span>DISCONNECTED</span>
            </>
          )}
        </button>

        {/* Judge Walkthrough Button */}
        <button
          onClick={onOpenWalkthrough}
          title="Launch the 15-step interactive judge walkthrough"
          style={{
            height: '32px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '0 12px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--primary)',
            color: '#ffffff',
            border: 'none',
            fontSize: 'var(--text-xs)',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'background var(--transition-fast)'
          }}
          onMouseEnter={e => (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary-hover)'}
          onMouseLeave={e => (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary)'}
        >
          <PlayCircle size={14} />
          <span>Judge Walkthrough</span>
        </button>

        {/* Reset State Button */}
        <button
          onClick={onResetDemo}
          title="Reset demo baseline state"
          style={{
            width: '32px',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'transparent',
            border: '1px solid var(--border)',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)'
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-hover)';
            (e.currentTarget as HTMLElement).style.color = 'var(--text)';
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
            (e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)';
          }}
        >
          <RotateCcw size={14} />
        </button>

        {/* Theme Toggle Button (Light/Dark) */}
        <button
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          style={{
            width: '32px',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'transparent',
            border: '1px solid var(--border)',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)'
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-hover)';
            (e.currentTarget as HTMLElement).style.color = 'var(--text)';
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
            (e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)';
          }}
        >
          {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        </button>

        {/* User Profile Avatar */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: 'var(--surface-hover)',
              border: '1px solid var(--border-strong)',
              color: 'var(--text)',
              fontSize: '12px',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
          >
            KA
          </button>

          {profileOpen && (
            <div
              style={{
                position: 'absolute',
                right: 0,
                top: '40px',
                width: '240px',
                backgroundColor: 'var(--surface-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-lg)',
                padding: 'var(--space-3)',
                zIndex: 60
              }}
            >
              <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                <div style={{ fontWeight: 700, fontSize: 'var(--text-sm)', color: 'var(--text)' }}>
                  Kiran Akash
                </div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                  System Administrator • Lead Analyst
                </div>
              </div>
              <div style={{ fontSize: '11.5px', color: 'var(--text-tertiary)', lineHeight: 1.4 }}>
                Session: <code style={{ color: 'var(--primary-text)' }}>SESSION-PQC-768</code>
                <br />
                Node: <code style={{ color: 'var(--text)' }}>sih-node-01 (x86_64)</code>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

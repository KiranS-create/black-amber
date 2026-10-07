import React from 'react';
import { 
  ShieldCheck, 
  PlayCircle, 
  RotateCcw, 
  Wifi, 
  WifiOff, 
  Layers, 
  Users, 
  FileText, 
  Unlock, 
  Database, 
  Search, 
  Zap, 
  Cpu,
  Sun,
  Moon
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { getExperienceVariant, setExperienceVariant } from '../variant';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: any) => void;
  isOnline: boolean;
  forceOffline: boolean;
  setForceOffline: (val: boolean) => void;
  onOpenWalkthrough: () => void;
  onResetDemo: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  isOnline,
  forceOffline,
  setForceOffline,
  onOpenWalkthrough,
  onResetDemo
}) => {
  const { theme, toggleTheme } = useTheme();

  const tabs = [
    { id: 'dashboard', label: '1. Overview', icon: Layers },
    { id: 'recipients', label: '2. PQC Identities', icon: Users },
    { id: 'release', label: '3. Encrypted Release', icon: FileText },
    { id: 'decrypt', label: '4. Decrypt & Sign', icon: Unlock },
    { id: 'ledger', label: '5. Audit Ledger', icon: Database },
    { id: 'leak', label: '6. Leak Attribution', icon: Search },
    { id: 'attack_lab', label: '7. Attack Lab', icon: Zap },
    { id: 'tardos', label: '8. Tardos Matrix', icon: Cpu }
  ];

  return (
    <header
      style={{
        backgroundColor: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        padding: '10px var(--space-6)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        boxShadow: 'var(--shadow-sm)'
      }}
    >
      {/* Top row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          marginBottom: '8px'
        }}
      >
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              padding: '6px',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <ShieldCheck size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: 'var(--text-lg)', fontWeight: 800, color: 'var(--text)', letterSpacing: '-0.02em' }}>
                AegisTrace
              </span>
              <span
                style={{
                  fontSize: '10.5px',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: isOnline ? 'var(--success-subtle)' : (forceOffline ? 'var(--warning-subtle)' : 'var(--danger-subtle)'),
                  color: isOnline ? 'var(--success-text)' : (forceOffline ? 'var(--warning-text)' : 'var(--danger-text)'),
                  border: `1px solid ${isOnline ? 'var(--success-border)' : (forceOffline ? 'var(--warning-border)' : 'var(--danger-border)')}`,
                  fontWeight: 600
                }}
              >
                {isOnline ? 'LIVE BACKEND (:8000)' : (forceOffline ? 'STANDALONE WORKSTATION' : 'STANDALONE LOCAL MODE')}
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '11.5px', color: 'var(--text-secondary)' }}>
              Cryptographic Attribution & Immutable Decryption Provenance Architecture
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {/* Experience Switcher Pill */}
          <div style={{ display: 'inline-flex', alignItems: 'center', padding: '2px', background: 'var(--surface-hover)', border: '1px solid var(--border)', borderRadius: '20px' }}>
            <button
              onClick={() => setExperienceVariant('main')}
              style={{
                border: 'none',
                background: getExperienceVariant() === 'main' ? 'var(--primary)' : 'transparent',
                color: getExperienceVariant() === 'main' ? '#ffffff' : 'var(--text-secondary)',
                fontSize: '11px',
                fontWeight: 600,
                padding: '4px 10px',
                borderRadius: '16px',
                cursor: 'pointer'
              }}
              title="Switch to New Minimal Workstation"
            >
              ✦ Main Workstation
            </button>
            <button
              onClick={() => setExperienceVariant('alternate')}
              style={{
                border: 'none',
                background: getExperienceVariant() === 'alternate' ? 'var(--primary)' : 'transparent',
                color: getExperienceVariant() === 'alternate' ? '#ffffff' : 'var(--text-secondary)',
                fontSize: '11px',
                fontWeight: 600,
                padding: '4px 10px',
                borderRadius: '16px',
                cursor: 'pointer'
              }}
              title="Active: Alternate Baseline UI"
            >
              ☵ Alternate UI
            </button>
          </div>

          {/* Guided Walkthrough Launcher */}
          <button
            onClick={onOpenWalkthrough}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              border: 'none',
              padding: '6px 12px',
              borderRadius: 'var(--radius-md)',
              fontWeight: 600,
              fontSize: 'var(--text-xs)',
              cursor: 'pointer'
            }}
          >
            <PlayCircle size={14} />
            <span>Judge Walkthrough</span>
          </button>

          {/* Connection Status Badge & Toggle */}
          <button
            onClick={() => setForceOffline(!forceOffline)}
            title="Click to toggle between Live Backend and Offline Simulator mode"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: isOnline ? 'var(--success-subtle)' : (forceOffline ? 'var(--warning-subtle)' : 'var(--danger-subtle)'),
              color: isOnline ? 'var(--success-text)' : (forceOffline ? 'var(--warning-text)' : 'var(--danger-text)'),
              border: `1px solid ${isOnline ? 'var(--success-border)' : (forceOffline ? 'var(--warning-border)' : 'var(--danger-border)')}`,
              padding: '6px 10px',
              borderRadius: 'var(--radius-md)',
              fontSize: '11.5px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            {isOnline ? <Wifi size={13} /> : <WifiOff size={13} />}
            <span>{isOnline ? 'LIVE API (:8000)' : (forceOffline ? 'STANDALONE MODE' : 'BACKEND OFFLINE')}</span>
          </button>

          {/* Reset State */}
          <button
            onClick={onResetDemo}
            title="Clear and reset workstation state"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'transparent',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border)',
              padding: '6px 10px',
              borderRadius: 'var(--radius-md)',
              fontSize: '11.5px',
              cursor: 'pointer'
            }}
          >
            <RotateCcw size={13} />
            <span>Reset State</span>
          </button>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '30px',
              height: '30px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'transparent',
              border: '1px solid var(--border)',
              color: 'var(--text-secondary)',
              cursor: 'pointer'
            }}
          >
            {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
          </button>
        </div>
      </div>

      {/* Tabs navigation */}
      <nav style={{ display: 'flex', gap: '4px', overflowX: 'auto', paddingBottom: '2px' }}>
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: 'var(--radius-md)',
                border: 'none',
                backgroundColor: isActive ? 'var(--primary-subtle)' : 'transparent',
                color: isActive ? 'var(--primary-text)' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                fontSize: 'var(--text-xs)',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all var(--transition-fast)'
              }}
            >
              <Icon size={14} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
};

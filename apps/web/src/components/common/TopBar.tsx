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
  LogOut,
  Users,
  Camera,
  Key,
  Eye,
  Sparkles,
  Layers
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
  onOpenCollusionLab?: () => void;
  onOpenAirGapLab?: () => void;
  onOpenDecryptionLab?: () => void;
  onOpenComparatorLab?: () => void;
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
  onOpenCollusionLab,
  onOpenAirGapLab,
  onOpenDecryptionLab,
  onOpenComparatorLab,
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
      <div style={{ flex: 1, maxWidth: '400px', margin: '0 var(--space-4)' }}>
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
            <span>Search artifacts, cases, evidence, or labs...</span>
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

      {/* Quick Interactive Labs Launcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        {onOpenCollusionLab && (
          <button
            onClick={onOpenCollusionLab}
            title="Collusion Resistance Simulator (Tardos Coalition Scoring)"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              height: '26px',
              padding: '0 8px',
              borderRadius: 'var(--radius-xs)',
              backgroundColor: 'rgba(139, 92, 246, 0.12)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              color: '#A78BFA',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <Users size={12} />
            <span>Collusion Lab</span>
          </button>
        )}

        {onOpenAirGapLab && (
          <button
            onClick={onOpenAirGapLab}
            title="Air-Gap Optical Camera Lab (Smartphone Demodulation)"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              height: '26px',
              padding: '0 8px',
              borderRadius: 'var(--radius-xs)',
              backgroundColor: 'rgba(245, 158, 11, 0.12)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              color: '#FBBF24',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <Camera size={12} />
            <span>Air-Gap Cam</span>
          </button>
        )}

        {onOpenDecryptionLab && (
          <button
            onClick={onOpenDecryptionLab}
            title="Recipient Decapsulation Enclave (ML-KEM-768)"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              height: '26px',
              padding: '0 8px',
              borderRadius: 'var(--radius-xs)',
              backgroundColor: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              color: '#38BDF8',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <Key size={12} />
            <span>Decapsulator</span>
          </button>
        )}

        {onOpenComparatorLab && (
          <button
            onClick={onOpenComparatorLab}
            title="Visual Imperceptibility Proof (Spectral Carrier Comparator)"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              height: '26px',
              padding: '0 8px',
              borderRadius: 'var(--radius-xs)',
              backgroundColor: 'rgba(76, 154, 154, 0.12)',
              border: '1px solid rgba(76, 154, 154, 0.3)',
              color: 'var(--primary-text)',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <Eye size={12} />
            <span>Imperceptibility</span>
          </button>
        )}
      </div>

      {/* System State, Quick Controls & Operator Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '8px' }}>
        {/* Operational Status Indicator */}
        <div
          title="Zero-Trust Enclave Pipeline: Verified & Operational"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            height: '28px',
            padding: '0 9px',
            borderRadius: 'var(--radius-xs)',
            backgroundColor: 'var(--success-subtle)',
            border: '1px solid var(--success-border)',
            color: 'var(--success-text)',
            fontSize: '11.5px',
            fontWeight: 600
          }}
        >
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10B981', display: 'inline-block' }} />
          <span>Operational</span>
        </div>

        {/* System Architecture Guide */}
        <button
          onClick={onOpenWalkthrough}
          title="Open architecture guide"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '5px',
            height: '28px',
            padding: '0 9px',
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
          <span>Guide</span>
        </button>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          style={{
            width: '28px',
            height: '28px',
            borderRadius: 'var(--radius-xs)',
            backgroundColor: 'transparent',
            border: '1px solid var(--border)',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer'
          }}
        >
          {theme === 'dark' ? <Sun size={13} /> : <Moon size={13} />}
        </button>

        {/* Operator Profile / Sign Out */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', paddingLeft: '4px', borderLeft: '1px solid var(--border)' }}>
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              backgroundColor: 'var(--primary-subtle)',
              border: '1px solid var(--primary-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '10px',
              fontWeight: 700,
              color: 'var(--primary)'
            }}
          >
            SI
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
                display: 'flex',
                alignItems: 'center'
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

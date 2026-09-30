import React from 'react';
import { UserSession } from '../../types';
import { Sun, Moon, LogOut, Shield, Volume2, VolumeX } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { getExperienceVariant, setExperienceVariant } from '../../variant';
import { audioService } from '../../services/audioService';

interface MainHeaderProps {
  currentSection: string;
  userSession: UserSession | null;
  isDemoMode: boolean;
  onSignOut: () => void;
  onOpenSettings: () => void;
  onOpenSihCompliance?: () => void;
}

export const MainHeader: React.FC<MainHeaderProps> = ({
  currentSection,
  userSession,
  isDemoMode,
  onSignOut,
  onOpenSettings,
  onOpenSihCompliance
}) => {
  const { theme, toggleTheme } = useTheme();
  const [isMuted, setIsMuted] = React.useState<boolean>(audioService.getIsMuted());

  const handleToggleAudio = () => {
    const next = audioService.toggleMute();
    setIsMuted(next);
    if (!next) {
      audioService.playClick();
    }
  };

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

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Experience Switcher Pill */}
        <div className="glass-pill-container">
          <button
            onClick={() => setExperienceVariant('main')}
            className={`glass-pill-btn ${getExperienceVariant() === 'main' ? 'active' : ''}`}
            title="Active: Main Forensic Workstation"
          >
            ✦ Main Workstation
          </button>
          <button
            onClick={() => setExperienceVariant('alternate')}
            className={`glass-pill-btn ${getExperienceVariant() === 'alternate' ? 'active' : ''}`}
            title="Switch to Alternate Baseline UI"
          >
            ☵ Alternate UI
          </button>
        </div>

        {onOpenSihCompliance && (
          <button
            onClick={onOpenSihCompliance}
            className="main-btn-secondary"
            title="View SIH 26237 Problem Statement Implementation Matrix"
            style={{ fontSize: '11px', padding: '4px 9px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
          >
            <Shield size={12} style={{ color: '#60A5FA' }} />
            <span>SIH 26237</span>
          </button>
        )}

        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '5px',
            padding: '2px 8px',
            borderRadius: '4px',
            background: 'var(--main-jade-subtle)',
            border: '1px solid var(--main-jade)',
            color: 'var(--main-jade)',
            fontSize: '11px',
            fontWeight: 600,
            letterSpacing: '0.02em'
          }}
        >
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--main-jade)' }} />
          <span>PROD LIVE</span>
        </div>

        <button
          onClick={handleToggleAudio}
          className="main-btn-ghost"
          title={isMuted ? 'Unmute cyber audio feedback' : 'Mute cyber audio feedback'}
          aria-label={isMuted ? 'Unmute audio' : 'Mute audio'}
          style={{ color: isMuted ? 'var(--main-text-tertiary)' : 'var(--main-petrol)' }}
        >
          {isMuted ? <VolumeX size={15} /> : <Volume2 size={15} />}
        </button>

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

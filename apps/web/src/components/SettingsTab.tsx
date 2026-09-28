import React from 'react';
import { Sliders, ShieldCheck, Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { StatusBadge } from './common/StatusBadge';

export const SettingsTab: React.FC = () => {
  const { themeMode, setTheme } = useTheme();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', maxWidth: '900px' }}>
      {/* Page Header */}
      <div>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600, color: 'var(--text-ivory)', letterSpacing: '-0.01em' }}>
          Forensic Parameters & Configuration
        </h1>
        <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-slate)', maxWidth: '640px' }}>
          Attribution decision thresholds, physical carrier parameters, and workstation display preferences.
        </p>
      </div>

      {/* Policy Card */}
      <div className="workstation-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldCheck size={18} style={{ color: 'var(--petrol)' }} />
          <div>
            <h2 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: 'var(--text-ivory)' }}>
              Fail-Closed Forensic Decision Policy
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: 'var(--text-slate)' }}>
              Attribution thresholds governing multi-channel evidence fusion
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div
            style={{
              padding: '12px 14px',
              borderRadius: '4px',
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ fontWeight: 500, fontSize: '13px', color: 'var(--text-ivory)' }}>
                Tardos Score Accusation Threshold (Z)
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-graphite)' }}>
                Candidates with accusation score below Z are unconditionally excluded from attribution.
              </div>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '14px', color: 'var(--text-ivory)' }}>
              Z = 11.40
            </div>
          </div>

          <div
            style={{
              padding: '12px 14px',
              borderRadius: '4px',
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ fontWeight: 500, fontSize: '13px', color: 'var(--text-ivory)' }}>
                Watermark Signal Confidence Cutoff
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-graphite)' }}>
                Correlation below 0.65 triggers No Signal or Inconclusive rather than false accusation.
              </div>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '14px', color: 'var(--text-ivory)' }}>
              0.650 (65%)
            </div>
          </div>

          <div
            style={{
              padding: '12px 14px',
              borderRadius: '4px',
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ fontWeight: 500, fontSize: '13px', color: 'var(--text-ivory)' }}>
                Non-Repudiation Signature Requirement
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-graphite)' }}>
                ML-DSA-65 signature must verify against recipient public key in ledger event.
              </div>
            </div>
            <StatusBadge label="Mandatory enforced" variant="success" size="sm" />
          </div>
        </div>
      </div>

      {/* Watermark Parameters */}
      <div className="workstation-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sliders size={18} style={{ color: 'var(--petrol)' }} />
          <div>
            <h2 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: 'var(--text-ivory)' }}>
              Carrier & Embedding Parameters
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: 'var(--text-slate)' }}>
              Physical watermarking carrier and geometric synchronization parameters
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          <div style={{ padding: '12px 14px', backgroundColor: 'var(--bg-elevated)', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>Embedding Strength (α)</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 600, color: 'var(--text-ivory)', marginTop: '4px' }}>0.080</div>
            <div style={{ fontSize: '11px', color: 'var(--text-graphite)', marginTop: '2px' }}>PSNR ~ 41.5 dB</div>
          </div>
          <div style={{ padding: '12px 14px', backgroundColor: 'var(--bg-elevated)', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>Sync Method</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 600, color: 'var(--text-ivory)', marginTop: '4px' }}>ArUco 4x4_50</div>
            <div style={{ fontSize: '11px', color: 'var(--text-graphite)', marginTop: '2px' }}>4-corner RANSAC</div>
          </div>
          <div style={{ padding: '12px 14px', backgroundColor: 'var(--bg-elevated)', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>Error Correction</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 600, color: 'var(--text-ivory)', marginTop: '4px' }}>RS(255, 223)</div>
            <div style={{ fontSize: '11px', color: 'var(--text-graphite)', marginTop: '2px' }}>t = 16 bytes</div>
          </div>
        </div>
      </div>

      {/* Theme Preference */}
      <div className="workstation-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: 'var(--text-ivory)' }}>
            Interface Theme
          </h2>
          <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: 'var(--text-slate)' }}>
            Switch between low-light forensic analysis mode and daylight documentation mode.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px' }}>
          <button
            onClick={() => setTheme('dark')}
            style={{
              padding: '14px',
              borderRadius: '4px',
              border: `1px solid ${themeMode === 'dark' ? 'var(--petrol)' : 'var(--border-subtle)'}`,
              backgroundColor: themeMode === 'dark' ? 'rgba(76, 154, 154, 0.08)' : 'var(--bg-elevated)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              transition: 'border-color var(--transition-fast)'
            }}
          >
            <Moon size={18} style={{ color: themeMode === 'dark' ? 'var(--petrol)' : 'var(--text-graphite)' }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 500, fontSize: '13px', color: themeMode === 'dark' ? 'var(--text-ivory)' : 'var(--text-slate)' }}>
                Dark Mode
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>
                Black Amber palette for operations
              </div>
            </div>
          </button>

          <button
            onClick={() => setTheme('light')}
            style={{
              padding: '14px',
              borderRadius: '4px',
              border: `1px solid ${themeMode === 'light' ? 'var(--petrol)' : 'var(--border-subtle)'}`,
              backgroundColor: themeMode === 'light' ? 'rgba(76, 154, 154, 0.08)' : 'var(--bg-elevated)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              transition: 'border-color var(--transition-fast)'
            }}
          >
            <Sun size={18} style={{ color: themeMode === 'light' ? 'var(--petrol)' : 'var(--text-graphite)' }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 500, fontSize: '13px', color: themeMode === 'light' ? 'var(--text-ivory)' : 'var(--text-slate)' }}>
                Light Mode
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>
                Warm ivory daylight palette
              </div>
            </div>
          </button>

          <button
            onClick={() => setTheme('system')}
            style={{
              padding: '14px',
              borderRadius: '4px',
              border: `1px solid ${themeMode === 'system' ? 'var(--petrol)' : 'var(--border-subtle)'}`,
              backgroundColor: themeMode === 'system' ? 'rgba(76, 154, 154, 0.08)' : 'var(--bg-elevated)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              transition: 'border-color var(--transition-fast)'
            }}
          >
            <Monitor size={18} style={{ color: themeMode === 'system' ? 'var(--petrol)' : 'var(--text-graphite)' }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 500, fontSize: '13px', color: themeMode === 'system' ? 'var(--text-ivory)' : 'var(--text-slate)' }}>
                System Preference
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>
                Follow system setting
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

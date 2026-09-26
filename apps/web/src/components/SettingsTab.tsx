import React from 'react';
import { Sliders, Key, ShieldCheck, Sun, Moon, Monitor, Info } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { StatusBadge } from './common/StatusBadge';

export const SettingsTab: React.FC = () => {
  const { themeMode, setTheme } = useTheme();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', maxWidth: '900px' }}>
      {/* Policy Card */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-6)',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: 'var(--space-4)' }}>
          <ShieldCheck size={20} style={{ color: 'var(--primary)' }} />
          <div>
            <h2 style={{ margin: 0, fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)' }}>
              Fail-Closed Forensic Decision Policy
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              Strict attribution thresholds governing multi-channel evidence fusion
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: 'var(--text-base)', color: 'var(--text)' }}>
                Tardos Score Accusation Threshold (Z)
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Candidates with accusation score below Z are unconditionally excluded from attribution.
              </div>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 'var(--text-md)', color: 'var(--primary-text)' }}>
              Z = 11.40
            </div>
          </div>

          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: 'var(--text-base)', color: 'var(--text)' }}>
                Watermark Signal Confidence Cutoff
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Correlation below 0.65 triggers NO_SIGNAL or PARTIAL rather than false positive.
              </div>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 'var(--text-md)', color: 'var(--primary-text)' }}>
              0.650 (65%)
            </div>
          </div>

          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: 'var(--text-base)', color: 'var(--text)' }}>
                Non-Repudiation Signature Requirement
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                ML-DSA-65 signature must verify against recipient public key in ledger event.
              </div>
            </div>
            <StatusBadge label="MANDATORY ENFORCED" variant="success" size="sm" dot />
          </div>
        </div>
      </div>

      {/* Watermark Parameters */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-6)',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: 'var(--space-4)' }}>
          <Sliders size={20} style={{ color: 'var(--primary)' }} />
          <div>
            <h2 style={{ margin: 0, fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)' }}>
              Carrier & Embedding Parameters
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              Physical watermarking carrier and geometric synchronization parameters
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-3)' }}>
          <div style={{ padding: 'var(--space-3)', backgroundColor: 'var(--surface-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>Embedding Strength (α)</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)', marginTop: '2px' }}>0.080</div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>PSNR ~ 41.5 dB</div>
          </div>
          <div style={{ padding: 'var(--space-3)', backgroundColor: 'var(--surface-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>Sync Method</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)', marginTop: '2px' }}>ArUco 4x4_50</div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>4-Corner RANSAC</div>
          </div>
          <div style={{ padding: 'var(--space-3)', backgroundColor: 'var(--surface-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>Error Correction</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)', marginTop: '2px' }}>RS(255, 223)</div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>t = 16 bytes</div>
          </div>
        </div>
      </div>

      {/* Theme Preference */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-6)',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <h2 style={{ margin: '0 0 var(--space-2) 0', fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)' }}>
          Interface Theme
        </h2>
        <p style={{ margin: '0 0 var(--space-4) 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
          Switch between high-contrast dark operations mode and clean light documentation mode.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-3)' }}>
          <button
            onClick={() => setTheme('dark')}
            style={{
              padding: 'var(--space-4)',
              borderRadius: 'var(--radius-md)',
              border: `2px solid ${themeMode === 'dark' ? 'var(--primary)' : 'var(--border)'}`,
              backgroundColor: themeMode === 'dark' ? 'var(--primary-subtle)' : 'var(--surface-subtle)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}
          >
            <Moon size={20} style={{ color: themeMode === 'dark' ? 'var(--primary)' : 'var(--text-secondary)' }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, color: themeMode === 'dark' ? 'var(--primary-text)' : 'var(--text)' }}>
                Dark Mode
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Deep slate for low-light forensic analysis
              </div>
            </div>
          </button>

          <button
            onClick={() => setTheme('light')}
            style={{
              padding: 'var(--space-4)',
              borderRadius: 'var(--radius-md)',
              border: `2px solid ${themeMode === 'light' ? 'var(--primary)' : 'var(--border)'}`,
              backgroundColor: themeMode === 'light' ? 'var(--primary-subtle)' : 'var(--surface-subtle)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}
          >
            <Sun size={20} style={{ color: themeMode === 'light' ? 'var(--primary)' : 'var(--text-secondary)' }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, color: themeMode === 'light' ? 'var(--primary-text)' : 'var(--text)' }}>
                Light Mode
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Warm enterprise daylight palette
              </div>
            </div>
          </button>

          <button
            onClick={() => setTheme('system')}
            style={{
              padding: 'var(--space-4)',
              borderRadius: 'var(--radius-md)',
              border: `2px solid ${themeMode === 'system' ? 'var(--primary)' : 'var(--border)'}`,
              backgroundColor: themeMode === 'system' ? 'var(--primary-subtle)' : 'var(--surface-subtle)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}
          >
            <Monitor size={20} style={{ color: themeMode === 'system' ? 'var(--primary)' : 'var(--text-secondary)' }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, color: themeMode === 'system' ? 'var(--primary-text)' : 'var(--text)' }}>
                System Preference
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Follow OS appearance automatically
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

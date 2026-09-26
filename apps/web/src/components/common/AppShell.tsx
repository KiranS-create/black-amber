import React, { useState, useEffect } from 'react';
import { TopBar } from './TopBar';
import { Sidebar, TabId } from './Sidebar';
import { CommandPalette } from './CommandPalette';

interface AppShellProps {
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;
  isOnline: boolean;
  forceOffline: boolean;
  onToggleForceOffline: (val: boolean) => void;
  onOpenWalkthrough: () => void;
  onResetDemo: () => void;
  onQuickScenario: (scenarioId: string) => void;
  onSimulateTamper: () => void;
  onExportReport?: () => void;
  recipientCount?: number;
  releaseCount?: number;
  ledgerCount?: number;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  activeTab,
  setActiveTab,
  isOnline,
  forceOffline,
  onToggleForceOffline,
  onOpenWalkthrough,
  onResetDemo,
  onQuickScenario,
  onSimulateTamper,
  onExportReport,
  recipientCount = 3,
  releaseCount = 1,
  ledgerCount = 4,
  children
}) => {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  useEffect(() => {
    // Expose global opener for Ctrl+K
    (window as any).__openCommandPalette = () => setCommandPaletteOpen(true);
    return () => {
      delete (window as any).__openCommandPalette;
    };
  }, []);

  const getBreadcrumb = () => {
    switch (activeTab) {
      case 'dashboard':
        return { section: 'Operations', title: 'Overview & Telemetry', desc: 'Real-time cryptographic pipeline status and security architecture' };
      case 'recipients':
        return { section: 'Identity Management', title: 'Recipient Registry', desc: 'Post-quantum public keys (ML-KEM-768, ML-DSA-65) and role assignments' };
      case 'release':
        return { section: 'Cryptographic Distribution', title: 'Encrypted Releases', desc: 'Multi-recipient hybrid envelope encapsulation and traceable distribution' };
      case 'leak':
        return { section: 'Forensics & Audit', title: 'Forensic Attribution Workstation', desc: 'Multi-channel evidence fusion, Tardos matrix scoring, and fail-closed verdict' };
      case 'attack_lab':
        return { section: 'Adversarial Research', title: 'Attack Laboratory', desc: 'Channel degradation benchmarks, print-camera recapture, and robustness proofs' };
      case 'ledger':
        return { section: 'Provenance & Integrity', title: 'Audit Ledger & Hash-Chain', desc: 'Immutable cryptographic provenance chain and real-time tamper verification' };
      case 'tardos':
        return { section: 'Fingerprinting Theory', title: 'Tardos Codeword Matrix', desc: 'Probabilistic fingerprint distribution and symmetric collusion-resistance bounds' };
      case 'decrypt':
        return { section: 'Client Operations', title: 'Decrypt & Provenance Signing', desc: 'Recipient-side ML-KEM decapsulation and non-repudiation signing demonstration' };
      case 'health':
        return { section: 'System Diagnostics', title: 'System Health & Engine Status', desc: 'Cryptographic runtime health, API connectivity, and benchmark verification' };
      case 'settings':
        return { section: 'Configuration', title: 'Settings & Security Parameters', desc: 'Forensic thresholds, watermark carrier parameters, and keyrings' };
      default:
        return { section: 'System', title: 'Forensic Console', desc: 'AegisTrace Core Operations' };
    }
  };

  const breadcrumb = getBreadcrumb();

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--bg)',
        color: 'var(--text)'
      }}
    >
      {/* Top Navigation Bar */}
      <TopBar
        isOnline={isOnline}
        forceOffline={forceOffline}
        onToggleForceOffline={onToggleForceOffline}
        onOpenWalkthrough={onOpenWalkthrough}
        onResetDemo={onResetDemo}
        onOpenCommandPalette={() => setCommandPaletteOpen(true)}
      />

      {/* Main Layout Container (Sidebar + Content) */}
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        {/* Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          recipientCount={recipientCount}
          releaseCount={releaseCount}
          ledgerCount={ledgerCount}
        />

        {/* Content Body Viewport */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            minWidth: 0,
            overflowY: 'auto'
          }}
        >
          {/* Page Sub-Header / Breadcrumb */}
          <div
            style={{
              padding: 'var(--space-4) var(--space-8)',
              borderBottom: '1px solid var(--border)',
              backgroundColor: 'var(--surface-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 'var(--space-3)'
            }}
          >
            <div>
              <div
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: 'var(--text-tertiary)',
                  marginBottom: '2px'
                }}
              >
                AegisTrace / {breadcrumb.section}
              </div>
              <h1
                style={{
                  margin: 0,
                  fontSize: 'var(--text-xl)',
                  fontWeight: 700,
                  color: 'var(--text)',
                  letterSpacing: '-0.02em',
                  lineHeight: 1.2
                }}
              >
                {breadcrumb.title}
              </h1>
              <p
                style={{
                  margin: '3px 0 0 0',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-secondary)'
                }}
              >
                {breadcrumb.desc}
              </p>
            </div>

            {/* Global quick status pills */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  fontSize: '11.5px',
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: 'var(--surface)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <span
                  style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--success)'
                  }}
                />
                <span>Fail-Closed Enforced</span>
              </div>
            </div>
          </div>

          {/* Page Main Content Area */}
          <main
            style={{
              flex: 1,
              padding: 'var(--space-6) var(--space-8)',
              maxWidth: '1500px',
              width: '100%',
              margin: '0 auto',
              boxSizing: 'border-box'
            }}
          >
            {children}
          </main>

          {/* Footer */}
          <footer
            style={{
              padding: 'var(--space-4) var(--space-8)',
              borderTop: '1px solid var(--border)',
              backgroundColor: 'var(--surface)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 'var(--space-3)',
              fontSize: 'var(--text-xs)',
              color: 'var(--text-tertiary)'
            }}
          >
            <div>
              <strong style={{ color: 'var(--text-secondary)' }}>AegisTrace</strong> • Post-Quantum Cryptographic Attribution & Provenance Platform
            </div>
            <div style={{ display: 'flex', gap: '16px', fontFamily: 'var(--font-mono)' }}>
              <span>ML-KEM-768</span>
              <span>•</span>
              <span>ML-DSA-65</span>
              <span>•</span>
              <span>Tardos m=128</span>
              <span>•</span>
              <span>AES-256-GCM</span>
              <span>•</span>
              <span>SHA-256 Ledger</span>
            </div>
          </footer>
        </div>
      </div>

      {/* Command Palette Modal */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        setActiveTab={setActiveTab}
        onQuickScenario={onQuickScenario}
        onOpenWalkthrough={onOpenWalkthrough}
        onResetDemo={onResetDemo}
        isOnline={isOnline}
        forceOffline={forceOffline}
        setForceOffline={onToggleForceOffline}
        onSimulateTamper={onSimulateTamper}
        onExportReport={onExportReport}
      />
    </div>
  );
};

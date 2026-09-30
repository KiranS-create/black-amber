import React, { useState, useEffect } from 'react';
import { TopBar } from './TopBar';
import { Sidebar, TabId } from './Sidebar';
import { CommandPalette } from './CommandPalette';

import { UserSession } from '../../types';

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
  onOpenCollusionLab?: () => void;
  onOpenAirGapLab?: () => void;
  onOpenDecryptionLab?: () => void;
  onOpenComparatorLab?: (recipientName?: string, docName?: string) => void;
  onOpenCertificate?: () => void;
  onOpenCompliance?: () => void;
  documentCount?: number;
  recipientCount?: number;
  releaseCount?: number;
  ledgerCount?: number;
  hasActiveInvestigation?: boolean;
  userSession?: UserSession | null;
  isDemoMode?: boolean;
  onPurgeDemo?: () => void;
  onSignOut?: () => void;
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
  onOpenCollusionLab,
  onOpenAirGapLab,
  onOpenDecryptionLab,
  onOpenComparatorLab,
  onOpenCertificate,
  onOpenCompliance,
  documentCount = 0,
  recipientCount = 0,
  releaseCount = 0,
  ledgerCount = 0,
  hasActiveInvestigation = false,
  userSession,
  isDemoMode = false,
  onPurgeDemo,
  onSignOut,
  children
}) => {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  useEffect(() => {
    (window as any).__openCommandPalette = () => setCommandPaletteOpen(true);

    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);

    return () => {
      delete (window as any).__openCommandPalette;
      window.removeEventListener('keydown', handleGlobalKeyDown);
    };
  }, []);

  return (
    <div
      style={{
        width: '100%',
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
        onOpenCollusionLab={onOpenCollusionLab}
        onOpenAirGapLab={onOpenAirGapLab}
        onOpenDecryptionLab={onOpenDecryptionLab}
        onOpenComparatorLab={onOpenComparatorLab ? () => onOpenComparatorLab() : undefined}
        userSession={userSession}
        isDemoMode={isDemoMode}
        onPurgeDemo={onPurgeDemo}
        onSignOut={onSignOut}
      />

      {/* Main Layout Container (Sidebar + Content) */}
      <div style={{ display: 'flex', flex: 1, minHeight: 0, width: '100%' }}>
        {/* Left Sidebar Navigation Rail */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          documentCount={documentCount}
          recipientCount={recipientCount}
          releaseCount={releaseCount}
          ledgerCount={ledgerCount}
          hasActiveInvestigation={hasActiveInvestigation}
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
          {/* Page Main Content Area */}
          <main
            className="page-main-container"
            style={{
              flex: 1,
              padding: 'var(--space-6) var(--space-8)',
              maxWidth: '1520px',
              width: '100%',
              margin: '0 auto',
              boxSizing: 'border-box'
            }}
          >
            {children}
          </main>
        </div>
      </div>

      {/* Command Palette Overlay (Layer 3) */}
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
        onOpenCollusionLab={onOpenCollusionLab}
        onOpenAirGapLab={onOpenAirGapLab}
        onOpenDecryptionLab={onOpenDecryptionLab}
        onOpenComparatorLab={onOpenComparatorLab ? () => onOpenComparatorLab() : undefined}
        onOpenCertificate={onOpenCertificate}
        onOpenCompliance={onOpenCompliance}
      />
    </div>
  );
};

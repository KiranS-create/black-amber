import React, { useState, useEffect } from 'react';
import { 
  PublicRecipient, 
  DocumentRelease, 
  EvidenceEvent, 
  AttributionResult, 
  LedgerVerificationResult,
  DocumentMetadata,
  LeakMetadata,
  AttackTelemetryInput
} from './types';
import { apiService } from './services/api';
import { ThemeProvider } from './context/ThemeContext';
import { motion, AnimatePresence } from 'framer-motion';
import { AppShell } from './components/common/AppShell';
import { TabId } from './components/common/Sidebar';
import { DashboardTab } from './components/DashboardTab';
import { RecipientsTab } from './components/RecipientsTab';
import { ReleaseTab } from './components/ReleaseTab';
import { DecryptionTab } from './components/DecryptionTab';
import { LedgerTab } from './components/LedgerTab';
import { LeakAnalysisTab } from './components/LeakAnalysisTab';
import { AttackLabTab } from './components/AttackLabTab';
import { TardosVisualizer } from './components/TardosVisualizer';
import { SystemHealthTab } from './components/SystemHealthTab';
import { SettingsTab } from './components/SettingsTab';
import { JudgeWalkthroughModal } from './components/JudgeWalkthroughModal';
import { ForensicReportModal } from './components/ForensicReportModal';
import { computeMockAttribution } from './services/mockData';

export function AppContent() {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');

  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [recipients, setRecipients] = useState<PublicRecipient[]>([]);
  const [releases, setReleases] = useState<DocumentRelease[]>([]);
  const [ledgerEvents, setLedgerEvents] = useState<EvidenceEvent[]>([]);
  const [ledgerStatus, setLedgerStatus] = useState<LedgerVerificationResult | null>(null);
  const [leakResult, setLeakResult] = useState<AttributionResult | null>(null);

  const [isOnline, setIsOnline] = useState<boolean>(false);
  const [forceOffline, setForceOffline] = useState<boolean>(false);
  const [walkthroughOpen, setWalkthroughOpen] = useState<boolean>(false);
  const [reportModalOpen, setReportModalOpen] = useState<boolean>(false);

  // Initial load
  useEffect(() => {
    const init = async () => {
      const health = await apiService.checkHealth();
      if (!health.online) {
        setForceOffline(true);
        apiService.setForceOffline(true);
      }
      await refreshAllData();
      setLeakResult(computeMockAttribution('clean_bob'));
    };
    init();

    const interval = setInterval(async () => {
      if (!apiService.isForceOffline()) {
        const health = await apiService.checkHealth();
        setIsOnline(health.online);
      }
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  const refreshAllData = async () => {
    try {
      const health = await apiService.checkHealth();
      setIsOnline(health.online);

      const [docList, recList, relList, evList, legStatus] = await Promise.all([
        apiService.getDocuments(),
        apiService.getRecipients(),
        apiService.getReleases(),
        apiService.getLedgerEvents(),
        apiService.verifyLedger()
      ]);

      setDocuments(docList);
      setRecipients(recList);
      setReleases(relList);
      setLedgerEvents(evList);
      setLedgerStatus(legStatus);
    } catch (err: any) {
      console.warn('Live refresh encountered error, setting offline demo mode:', err);
      setForceOffline(true);
      apiService.setForceOffline(true);
      setIsOnline(false);
      const [docList, recList, relList, evList, legStatus] = await Promise.all([
        apiService.getDocuments(),
        apiService.getRecipients(),
        apiService.getReleases(),
        apiService.getLedgerEvents(),
        apiService.verifyLedger()
      ]);
      setDocuments(docList);
      setRecipients(recList);
      setReleases(relList);
      setLedgerEvents(evList);
      setLedgerStatus(legStatus);
    }
  };

  const handleToggleForceOffline = async (val: boolean) => {
    setForceOffline(val);
    apiService.setForceOffline(val);
    await refreshAllData();
  };

  const handleUploadDocument = async (file: File, name?: string) => {
    const doc = await apiService.uploadDocument(file, name);
    await refreshAllData();
    return doc;
  };

  const handleEnrollRecipient = async (name: string, id?: string) => {
    await apiService.enrollRecipient(name, id);
    await refreshAllData();
  };

  const handleCreateRelease = async (
    docName: string, 
    docBase64: string, 
    recipientIds: string[],
    docId?: string,
    tardosEnabled?: boolean
  ) => {
    await apiService.createRelease(docName, docBase64, recipientIds, docId, tardosEnabled);
    await refreshAllData();
  };

  const handleDecrypt = async (releaseId: string, recipientId: string) => {
    const res = await apiService.decryptPackage(releaseId, recipientId);
    await refreshAllData();
    return res;
  };

  const handleUploadLeakFile = async (file: File, suspectedReleaseId?: string): Promise<LeakMetadata> => {
    const leakMeta = await apiService.uploadLeak(file, suspectedReleaseId);
    return leakMeta;
  };

  const handleAnalyzeLeak = async (
    scenarioIdOrBase64: string, 
    releaseId?: string,
    telemetry?: AttackTelemetryInput
  ) => {
    const res = await apiService.analyzeLeak(scenarioIdOrBase64, releaseId, telemetry);
    setLeakResult(res);
  };

  const handleVerifyLedger = async () => {
    const status = await apiService.verifyLedger();
    setLedgerStatus(status);
  };

  const handleSimulateTamper = (blockIndex: number) => {
    apiService.simulateTamperBlock(blockIndex);
    refreshAllData();
  };

  const handleResetTamper = () => {
    apiService.resetLedgerTamper();
    refreshAllData();
  };

  const handleResetAll = () => {
    apiService.resetAllToDefault();
    setLeakResult(computeMockAttribution('clean_bob'));
    refreshAllData();
  };

  const handleQuickScenario = async (scenarioId: string) => {
    await handleAnalyzeLeak(scenarioId);
    setActiveTab('leak');
  };

  return (
    <AppShell
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      isOnline={isOnline}
      forceOffline={forceOffline}
      onToggleForceOffline={handleToggleForceOffline}
      onOpenWalkthrough={() => setWalkthroughOpen(true)}
      onResetDemo={handleResetAll}
      onQuickScenario={handleQuickScenario}
      onSimulateTamper={() => handleSimulateTamper(1)}
      onExportReport={() => setReportModalOpen(true)}
      recipientCount={recipients.length}
      releaseCount={releases.length}
      ledgerCount={ledgerStatus?.total_events ?? ledgerEvents.length}
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.15, ease: 'easeOut' }}
          style={{ width: '100%' }}
        >
          {activeTab === 'dashboard' && (
            <DashboardTab
              documents={documents}
              recipients={recipients}
              releases={releases}
              ledgerStatus={ledgerStatus}
              isOnline={isOnline}
              setActiveTab={setActiveTab}
              onQuickScenario={handleQuickScenario}
            />
          )}

          {activeTab === 'recipients' && (
            <RecipientsTab
              recipients={recipients}
              onEnroll={handleEnrollRecipient}
            />
          )}

          {activeTab === 'release' && (
            <ReleaseTab
              documents={documents}
              recipients={recipients}
              releases={releases}
              onCreateRelease={handleCreateRelease}
              onUploadDocument={handleUploadDocument}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'decrypt' && (
            <DecryptionTab
              recipients={recipients}
              releases={releases}
              onDecrypt={handleDecrypt}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'ledger' && (
            <LedgerTab
              events={ledgerEvents}
              ledgerStatus={ledgerStatus}
              isOnline={isOnline}
              onVerifyLedger={handleVerifyLedger}
              onSimulateTamper={handleSimulateTamper}
              onResetTamper={handleResetTamper}
            />
          )}

          {activeTab === 'leak' && (
            <LeakAnalysisTab
              leakResult={leakResult}
              onAnalyzeLeak={handleAnalyzeLeak}
              onUploadLeakFile={handleUploadLeakFile}
              onOpenReportModal={() => setReportModalOpen(true)}
            />
          )}

          {activeTab === 'attack_lab' && (
            <AttackLabTab />
          )}

          {activeTab === 'tardos' && (
            <TardosVisualizer />
          )}

          {activeTab === 'health' && (
            <SystemHealthTab isOnline={isOnline} onRefresh={refreshAllData} />
          )}

          {activeTab === 'settings' && (
            <SettingsTab />
          )}
        </motion.div>
      </AnimatePresence>

      {/* Guided Judge Walkthrough Modal */}
      <JudgeWalkthroughModal
        isOpen={walkthroughOpen}
        onClose={() => setWalkthroughOpen(false)}
        setActiveTab={setActiveTab}
        onTriggerDecryption={async () => {
          if (releases[0]) {
            await handleDecrypt(releases[0].release_id, 'bob');
          }
        }}
        onTriggerLeakAnalysis={async (scenarioId) => {
          await handleAnalyzeLeak(scenarioId);
        }}
        onTriggerLedgerTamper={() => {
          handleSimulateTamper(1);
        }}
      />

      {/* Forensic Report Export Modal */}
      <ForensicReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        leakResult={leakResult}
        ledgerEvents={ledgerEvents}
      />
    </AppShell>
  );
}

export function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

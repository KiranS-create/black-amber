import React, { useState, useEffect } from 'react';
import { 
  PublicRecipient, 
  DocumentRelease, 
  EvidenceEvent, 
  AttributionResult, 
  LedgerVerificationResult,
  DocumentMetadata,
  LeakMetadata,
  AttackTelemetryInput,
  DirectoryIdentity,
  DirectoryGroup,
  UserSession,
  EvidenceRecord,
  InvestigationRecord
} from './types';
import { apiService } from './services/api';
import { ThemeProvider } from './context/ThemeContext';
import { motion, AnimatePresence } from 'framer-motion';
import { AppShell } from './components/common/AppShell';
import { TabId } from './components/common/Sidebar';
import { LoginScreen } from './components/LoginScreen';
import { SignUpScreen } from './components/SignUpScreen';
import { VerifyTab } from './components/VerifyTab';
import { OverviewTab } from './components/OverviewTab';
import { DocumentsTab } from './components/DocumentsTab';
import { ReleaseTab } from './components/ReleaseTab';
import { InvestigationsTab } from './components/InvestigationsTab';
import { DirectoryTab } from './components/DirectoryTab';
import { RecipientsTab } from './components/RecipientsTab';
import { GroupsTab } from './components/GroupsTab';
import { EvidenceTab } from './components/EvidenceTab';
import { ProvenanceTab } from './components/ProvenanceTab';
import { LedgerTab } from './components/LedgerTab';
import { AttackLabTab } from './components/AttackLabTab';
import { SystemHealthTab } from './components/SystemHealthTab';
import { IntegrationsTab } from './components/IntegrationsTab';
import { SettingsTab } from './components/SettingsTab';
import { ProductGuideModal } from './components/ProductGuideModal';
import { ForensicReportModal } from './components/ForensicReportModal';
import { MainCollusionLabModal } from './components/main/MainCollusionLabModal';
import { MainAirGapCameraModal } from './components/main/MainAirGapCameraModal';
import { MainRecipientDecryptionModal } from './components/main/MainRecipientDecryptionModal';
import { MainVisualComparatorModal } from './components/main/MainVisualComparatorModal';
import { MainSection65BCertificateModal } from './components/main/MainSection65BCertificateModal';
import { MainSihComplianceModal } from './components/main/MainSihComplianceModal';
import { JudgeRehearsalModal } from './components/JudgeRehearsalModal';
import { useLenis } from './hooks/useLenis';
import { getExperienceVariant } from './variant';
import { MainApp } from './components/main/MainApp';
import './styles/main-experience.css';

export function AppContent() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  const [userSession, setUserSession] = useState<UserSession | null>(() => apiService.getCurrentUser());
  const [isDemoMode, setIsDemoMode] = useState<boolean>(() => apiService.isDemoMode());
  const [isSignUpMode, setIsSignUpMode] = useState<boolean>(false);
  const [isVerifyStandalone, setIsVerifyStandalone] = useState<boolean>(false);

  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [recipients, setRecipients] = useState<PublicRecipient[]>([]);
  const [releases, setReleases] = useState<DocumentRelease[]>([]);
  const [ledgerEvents, setLedgerEvents] = useState<EvidenceEvent[]>([]);
  const [ledgerStatus, setLedgerStatus] = useState<LedgerVerificationResult | null>(null);
  const [leakResult, setLeakResult] = useState<AttributionResult | null>(null);
  const [directoryIdentities, setDirectoryIdentities] = useState<DirectoryIdentity[]>([]);
  const [directoryGroups, setDirectoryGroups] = useState<DirectoryGroup[]>([]);
  const [evidenceRecords, setEvidenceRecords] = useState<EvidenceRecord[]>([]);
  const [investigations, setInvestigations] = useState<InvestigationRecord[]>([]);

  const [isOnline, setIsOnline] = useState<boolean>(false);
  const [forceOffline, setForceOffline] = useState<boolean>(false);
  const [guideOpen, setGuideOpen] = useState<boolean>(false);
  const [reportModalOpen, setReportModalOpen] = useState<boolean>(false);
  const [collusionLabOpen, setCollusionLabOpen] = useState<boolean>(false);
  const [airGapLabOpen, setAirGapLabOpen] = useState<boolean>(false);
  const [decryptionLabOpen, setDecryptionLabOpen] = useState<boolean>(false);
  const [comparatorLabOpen, setComparatorLabOpen] = useState<boolean>(false);
  const [certificateLabOpen, setCertificateLabOpen] = useState<boolean>(false);
  const [complianceLabOpen, setComplianceLabOpen] = useState<boolean>(false);
  const [rehearsalModalOpen, setRehearsalModalOpen] = useState<boolean>(false);
  const [certificateContext, setCertificateContext] = useState<any>(null);
  const [comparatorContext, setComparatorContext] = useState<{ docName: string; recipientName: string }>({
    docName: 'National_Defense_Protocol_2026.pdf',
    recipientName: 'Marcus Vance'
  });

  const handleOpenCertificate = (context?: any) => {
    setCertificateContext(context || null);
    setCertificateLabOpen(true);
  };

  // Initial load
  useEffect(() => {
    const init = async () => {
      const health = await apiService.checkHealth();
      setIsOnline(health.online);
      await refreshAllData();
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

      const [docList, recList, relList, evList, legStatus, dirList, grpList, evRecList, invList] = await Promise.all([
        apiService.getDocuments(),
        apiService.getRecipients(),
        apiService.getReleases(),
        apiService.getLedgerEvents(),
        apiService.verifyLedger(),
        apiService.searchDirectory(''),
        apiService.getDirectoryGroups(),
        apiService.getEvidenceRecords(),
        apiService.getHistoricalInvestigations()
      ]);

      setDocuments(docList);
      setRecipients(recList);
      setReleases(relList);
      setLedgerEvents(evList);
      setLedgerStatus(legStatus);
      setDirectoryIdentities(dirList);
      setDirectoryGroups(grpList);
      setEvidenceRecords(evRecList);
      setInvestigations(invList);
      setIsDemoMode(apiService.isDemoMode());
    } catch (err: any) {
      console.warn('Live refresh encountered error, falling back to local view:', err);
      setIsOnline(false);
      const [docList, recList, relList, evList, legStatus, dirList, grpList, evRecList, invList] = await Promise.all([
        apiService.getDocuments(),
        apiService.getRecipients(),
        apiService.getReleases(),
        apiService.getLedgerEvents(),
        apiService.verifyLedger(),
        apiService.searchDirectory(''),
        apiService.getDirectoryGroups(),
        apiService.getEvidenceRecords(),
        apiService.getHistoricalInvestigations()
      ]);
      setDocuments(docList);
      setRecipients(recList);
      setReleases(relList);
      setLedgerEvents(evList);
      setLedgerStatus(legStatus);
      setDirectoryIdentities(dirList);
      setDirectoryGroups(grpList);
      setEvidenceRecords(evRecList);
      setInvestigations(invList);
      setIsDemoMode(apiService.isDemoMode());
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

  const handleEnrollFromDirectory = async (identityId: string, role?: string) => {
    await apiService.enrollFromDirectory(identityId, role);
    await refreshAllData();
  };

  const handleRevokeRecipient = async (recipientId: string) => {
    await apiService.revokeRecipient(recipientId);
    await refreshAllData();
  };

  const handleCreateRelease = async (
    docName: string, 
    docBase64: string, 
    recipientIds: string[],
    docId?: string,
    tardosEnabled?: boolean,
    targets?: Array<{ target_type: 'INDIVIDUAL' | 'GROUP', target_id: string }>
  ) => {
    const rel = await apiService.createRelease(docName, docBase64, recipientIds, docId, tardosEnabled, targets);
    await refreshAllData();
    return rel;
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

  const handleSignOut = async () => {
    await apiService.logout();
    setUserSession(null);
  };

  const handleLoadDemoData = () => {
    apiService.loadDemoData();
    setIsDemoMode(true);
    refreshAllData();
  };

  const handlePurgeDemoData = () => {
    apiService.purgeDemoData();
    setIsDemoMode(false);
    setLeakResult(null);
    refreshAllData();
  };

  const handleQuickScenario = async (scenarioId: string) => {
    await handleAnalyzeLeak(scenarioId);
    setActiveTab('investigations');
  };

  if (isVerifyStandalone) {
    return (
      <VerifyTab
        isStandalone={true}
        onBackToApp={() => setIsVerifyStandalone(false)}
      />
    );
  }

  if (!userSession) {
    if (isSignUpMode) {
      return (
        <SignUpScreen
          onSwitchToSignIn={() => setIsSignUpMode(false)}
          onOpenVerifyStandalone={() => setIsVerifyStandalone(true)}
        />
      );
    }
    return (
      <LoginScreen
        onLoginSuccess={(session) => {
          setUserSession(session);
          refreshAllData();
        }}
        onSwitchToSignUp={() => setIsSignUpMode(true)}
        onOpenVerifyStandalone={() => setIsVerifyStandalone(true)}
      />
    );
  }

  return (
    <>
      <AppShell
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isOnline={isOnline}
        forceOffline={forceOffline}
        onToggleForceOffline={handleToggleForceOffline}
        onOpenWalkthrough={() => setGuideOpen(true)}
        onResetDemo={handleLoadDemoData}
        onQuickScenario={handleQuickScenario}
        onSimulateTamper={() => handleSimulateTamper(1)}
        onExportReport={() => setReportModalOpen(true)}
        onOpenCollusionLab={() => setCollusionLabOpen(true)}
        onOpenAirGapLab={() => setAirGapLabOpen(true)}
        onOpenDecryptionLab={() => setDecryptionLabOpen(true)}
        onOpenComparatorLab={(recipientName, docName) => {
          setComparatorContext({
            recipientName: recipientName || 'Marcus Vance',
            docName: docName || documents[0]?.document_name || 'National_Defense_Protocol_2026.pdf'
          });
          setComparatorLabOpen(true);
        }}
        onOpenRehearsal={() => setRehearsalModalOpen(true)}
        onOpenCertificate={handleOpenCertificate}
        onOpenCompliance={() => setComplianceLabOpen(true)}
        documentCount={documents.length}
        recipientCount={recipients.length}
        releaseCount={releases.length}
        ledgerCount={ledgerStatus?.total_events ?? ledgerEvents.length}
        hasActiveInvestigation={leakResult !== null}
        userSession={userSession}
        isDemoMode={isDemoMode}
        onPurgeDemo={handlePurgeDemoData}
        onSignOut={handleSignOut}
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
            {/* OPERATIONS */}
            {activeTab === 'overview' && (
              <OverviewTab
                documents={documents}
                recipients={recipients}
                releases={releases}
                ledgerStatus={ledgerStatus}
                investigations={investigations}
                evidenceRecords={evidenceRecords}
                isOnline={isOnline}
                isDemoMode={isDemoMode}
                setActiveTab={setActiveTab}
                onQuickScenario={handleQuickScenario}
                onLoadDemo={handleLoadDemoData}
                onPurgeDemo={handlePurgeDemoData}
                onOpenCollusionLab={() => setCollusionLabOpen(true)}
                onOpenAirGapLab={() => setAirGapLabOpen(true)}
                onOpenDecryptionLab={() => setDecryptionLabOpen(true)}
                onOpenComparatorLab={(recipientName, docName) => {
                  setComparatorContext({
                    recipientName: recipientName || 'Marcus Vance',
                    docName: docName || documents[0]?.document_name || 'National_Defense_Protocol_2026.pdf'
                  });
                  setComparatorLabOpen(true);
                }}
                onOpenCertificate={handleOpenCertificate}
                onOpenCompliance={() => setComplianceLabOpen(true)}
              />
            )}

            {activeTab === 'documents' && (
              <DocumentsTab
                documents={documents}
                releases={releases}
                onUploadDocument={handleUploadDocument}
                setActiveTab={setActiveTab}
              />
            )}

            {activeTab === 'releases' && (
              <ReleaseTab
                documents={documents}
                recipients={recipients}
                releases={releases}
                onCreateRelease={handleCreateRelease}
                onUploadDocument={handleUploadDocument}
                setActiveTab={setActiveTab}
              />
            )}

            {activeTab === 'investigations' && (
              <InvestigationsTab
                leakResult={leakResult}
                onAnalyzeLeak={handleAnalyzeLeak}
                onUploadLeakFile={handleUploadLeakFile}
                onOpenReportModal={() => setReportModalOpen(true)}
                onOpenCertificate={handleOpenCertificate}
                onExecuteQuarantine={async (suspectName, terminalId, reason) => {
                  await apiService.executeSovereignQuarantine(suspectName, terminalId, reason);
                  const [events, recs] = await Promise.all([
                    apiService.getLedgerEvents(),
                    apiService.getRecipients()
                  ]);
                  setLedgerEvents(events);
                  setRecipients(recs);
                }}
              />
            )}

            {/* IDENTITY */}
            {activeTab === 'directory' && (
              <DirectoryTab
                identities={directoryIdentities}
                recipients={recipients}
                onEnrollFromDirectory={handleEnrollFromDirectory}
                onRevokeRecipient={handleRevokeRecipient}
                setActiveTab={setActiveTab}
              />
            )}

            {activeTab === 'recipients' && (
              <RecipientsTab
                recipients={recipients}
                onEnroll={handleEnrollRecipient}
                onEnrollFromDirectory={handleEnrollFromDirectory}
                onRevokeRecipient={handleRevokeRecipient}
              />
            )}

            {activeTab === 'groups' && (
              <GroupsTab
                groups={directoryGroups}
                identities={directoryIdentities}
                recipients={recipients}
                setActiveTab={setActiveTab}
              />
            )}

            {/* EVIDENCE */}
            {activeTab === 'evidence' && (
              <EvidenceTab
                records={evidenceRecords}
                setActiveTab={setActiveTab}
                onOpenCertificate={handleOpenCertificate}
              />
            )}

            {/* VERIFICATION */}
            {activeTab === 'verify' && (
              <VerifyTab
                isStandalone={false}
                onBackToApp={() => setActiveTab('overview')}
              />
            )}

            {activeTab === 'provenance' && (
              <ProvenanceTab
                releases={releases}
                leakResult={leakResult}
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

            {/* SECURITY */}
            {activeTab === 'security_testing' && (
              <AttackLabTab />
            )}

            {activeTab === 'health' && (
              <SystemHealthTab isOnline={isOnline} onRefresh={refreshAllData} />
            )}

            {activeTab === 'integrations' && (
              <IntegrationsTab
                setActiveTab={setActiveTab}
              />
            )}

            {/* ADMIN */}
            {activeTab === 'settings' && (
              <SettingsTab />
            )}
          </motion.div>
        </AnimatePresence>

        {/* Enterprise System Architecture Guide Modal */}
        <ProductGuideModal
          isOpen={guideOpen}
          onClose={() => setGuideOpen(false)}
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

        {/* Interactive Collusion Resistance Simulator Modal */}
        <MainCollusionLabModal
          isOpen={collusionLabOpen}
          onClose={() => setCollusionLabOpen(false)}
        />

        {/* Interactive Air-Gap Optical Camera Lab Modal */}
        <MainAirGapCameraModal
          isOpen={airGapLabOpen}
          onClose={() => setAirGapLabOpen(false)}
          onAttributionComplete={async (suspect) => {
            await handleAnalyzeLeak('photo_bob');
            setActiveTab('investigations');
          }}
          onOpenCertificate={() => {
            setAirGapLabOpen(false);
            setCertificateLabOpen(true);
          }}
        />

        {/* Interactive Recipient Decapsulation Enclave Modal */}
        <MainRecipientDecryptionModal
          isOpen={decryptionLabOpen}
          onClose={() => setDecryptionLabOpen(false)}
          releases={releases}
          recipients={recipients}
          onOpenComparator={(recName, docName) => {
            setComparatorContext({
              recipientName: recName || 'Marcus Vance',
              docName: docName || documents[0]?.document_name || 'National_Defense_Protocol_2026.pdf'
            });
            setComparatorLabOpen(true);
          }}
          onInvestigateLeak={async (scenarioId) => {
            await handleAnalyzeLeak(scenarioId);
            setActiveTab('investigations');
          }}
          onRefresh={refreshAllData}
        />

        {/* Interactive Proof of Visual Imperceptibility Modal */}
        <MainVisualComparatorModal
          isOpen={comparatorLabOpen}
          onClose={() => setComparatorLabOpen(false)}
          documentName={comparatorContext.docName}
          recipientName={comparatorContext.recipientName}
        />

        {/* Live 2-Device Demonstration Stunt Modal */}
        <JudgeRehearsalModal
          isOpen={rehearsalModalOpen}
          onClose={() => setRehearsalModalOpen(false)}
          onOpenDocket={(ctx) => handleOpenCertificate(ctx)}
        />

        {/* Section 65B Certificate & Court Docket Modal */}
        <MainSection65BCertificateModal
          isOpen={certificateLabOpen}
          onClose={() => setCertificateLabOpen(false)}
          result={leakResult}
          candidateName={certificateContext?.candidateName || leakResult?.candidate?.name || comparatorContext.recipientName}
          terminalId={certificateContext?.terminalId || 'Terminal #W-842911'}
          suspectRank={certificateContext?.suspectRank || 'Commander (Naval Operations)'}
          secretCodeHex={certificateContext?.secretCodeHex || '0x7E9A-C401-88F3-902B-0CDA07-9AF2'}
          merkleLeaf={certificateContext?.merkleLeaf || 'Block #842,911 (ML-DSA-65 Valid Signature)'}
          confidence={certificateContext?.confidence || '99.98% (BCH-Verified, 0 Bit Errors)'}
          bchStatus={certificateContext?.bchStatus || '0 Bit Errors (BCH t=3 Corrected)'}
          routeHop={certificateContext?.routeHop}
          documentName={certificateContext?.documentName || documents[0]?.document_name || comparatorContext.docName}
          sabhaCountersigned={certificateContext?.sabhaCountersigned ?? true}
        />

        {/* SIH Problem Statement 26237 Compliance Matrix Modal */}
        <MainSihComplianceModal
          isOpen={complianceLabOpen}
          onClose={() => setComplianceLabOpen(false)}
        />
      </AppShell>
    </>
  );
}

export function App() {
  const variant = getExperienceVariant();

  if (variant === 'main') {
    return (
      <ThemeProvider>
        <MainApp />
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

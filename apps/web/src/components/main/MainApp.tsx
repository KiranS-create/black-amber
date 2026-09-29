import React, { useState, useEffect } from 'react';
import { 
  PublicRecipient, 
  DocumentRelease, 
  EvidenceEvent, 
  AttributionResult, 
  DocumentMetadata, 
  UserSession, 
  EvidenceRecord, 
  InvestigationRecord 
} from '../../types';
import { apiService } from '../../services/api';
import { MainSidebar, MainTabId } from './MainSidebar';
import { MainHeader } from './MainHeader';
import { MainOverview } from './MainOverview';
import { MainDocuments } from './MainDocuments';
import { MainInvestigations } from './MainInvestigations';
import { MainEvidence } from './MainEvidence';
import { MainSettingsModal } from './MainSettingsModal';
import { MainLogin } from './MainLogin';
import { VerifyTab } from '../VerifyTab';
import '../../styles/main-experience.css';

export function MainApp() {
  const [activeTab, setActiveTab] = useState<MainTabId>('overview');
  const [userSession, setUserSession] = useState<UserSession | null>(() => apiService.getCurrentUser());
  const [isDemoMode, setIsDemoMode] = useState<boolean>(() => apiService.isDemoMode());
  const [isVerifyStandalone, setIsVerifyStandalone] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [recipients, setRecipients] = useState<PublicRecipient[]>([]);
  const [releases, setReleases] = useState<DocumentRelease[]>([]);
  const [ledgerEvents, setLedgerEvents] = useState<EvidenceEvent[]>([]);
  const [evidenceRecords, setEvidenceRecords] = useState<EvidenceRecord[]>([]);
  const [investigations, setInvestigations] = useState<InvestigationRecord[]>([]);
  const [leakResult, setLeakResult] = useState<AttributionResult | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(true);

  // Initial Data Fetch
  useEffect(() => {
    const init = async () => {
      try {
        const health = await apiService.checkHealth();
        setIsOnline(health.online);
        await refreshData();
      } catch (err) {
        console.error('Initial health check failed:', err);
      }
    };
    init();

    const interval = setInterval(async () => {
      try {
        const health = await apiService.checkHealth();
        setIsOnline(health.online);
      } catch {
        setIsOnline(false);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const refreshData = async () => {
    try {
      const [docs, recs, rels, events, records, invs] = await Promise.all([
        apiService.getDocuments(),
        apiService.getRecipients(),
        apiService.getReleases(),
        apiService.getLedgerEvents(),
        apiService.getEvidenceRecords(),
        apiService.getHistoricalInvestigations()
      ]);
      setDocuments(docs);
      setRecipients(recs);
      setReleases(rels);
      setLedgerEvents(events);
      setEvidenceRecords(records);
      setInvestigations(invs);
    } catch (err) {
      console.warn('Data refresh warning (using local caches if offline):', err);
    }
  };

  // Handlers
  const handleUploadDocument = async (file: File) => {
    await apiService.uploadDocument(file);
    await refreshData();
  };

  const handleProtectAndRelease = async (documentId: string, recipientIds: string[]) => {
    const doc = documents.find(d => d.document_id === documentId);
    const docName = doc?.document_name || 'Protected_Document.pdf';
    await apiService.createRelease(docName, 'U0lIMjYyMzc=', recipientIds, documentId, true);
    await refreshData();
  };

  const handleIngestLeakAndAnalyze = async (file: File, releaseId?: string) => {
    const leak = await apiService.uploadLeak(file, releaseId);
    const result = await apiService.analyzeLeak(leak.leak_id, releaseId);
    setLeakResult(result);
    await refreshData();
    setActiveTab('investigations');
  };

  const handleSignOut = () => {
    apiService.logout();
    setUserSession(null);
  };

  // 1. Standalone Offline Verifier Mode
  if (isVerifyStandalone) {
    return (
      <div className="main-experience" style={{ minHeight: '100vh', background: 'var(--main-bg)', padding: '24px' }}>
        <div style={{ maxWidth: '960px', margin: '0 auto' }}>
          <button
            onClick={() => setIsVerifyStandalone(false)}
            className="main-btn-secondary"
            style={{ marginBottom: '16px' }}
          >
            ← Back to Workstation
          </button>
          <VerifyTab onBackToApp={() => setIsVerifyStandalone(false)} isStandalone={true} />
        </div>
      </div>
    );
  }

  // 2. Unauthenticated Login Screen
  if (!userSession) {
    return (
      <MainLogin
        onLoginSuccess={(session) => {
          setUserSession(session);
          refreshData();
        }}
        onOpenVerifyStandalone={() => setIsVerifyStandalone(true)}
        onOpenSignUp={() => {
          alert('Self-registration is disabled in this production deployment. Please use demo credentials (admin/admin).');
        }}
      />
    );
  }

  // 3. Authenticated Workstation Shell
  return (
    <div className="main-experience">
      <div style={{ display: 'flex', flex: 1, minHeight: '100vh' }}>
        {/* Slim 4-Item Sidebar */}
        <MainSidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          documentCount={documents.length}
          hasActiveInvestigation={investigations.length > 0}
          onOpenSettings={() => setIsSettingsOpen(true)}
        />

        {/* Primary Workspace */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowX: 'hidden' }}>
          <MainHeader
            currentSection={activeTab}
            userSession={userSession}
            isDemoMode={isDemoMode}
            onSignOut={handleSignOut}
            onOpenSettings={() => setIsSettingsOpen(true)}
          />

          <main style={{ flex: 1, overflowY: 'auto' }}>
            {activeTab === 'overview' && (
              <MainOverview
                documents={documents}
                recipients={recipients}
                investigations={investigations}
                ledgerEvents={ledgerEvents}
                isOnline={isOnline}
                onNavigate={setActiveTab}
              />
            )}

            {activeTab === 'documents' && (
              <MainDocuments
                documents={documents}
                recipients={recipients}
                onUpload={handleUploadDocument}
                onProtectAndRelease={handleProtectAndRelease}
              />
            )}

            {activeTab === 'investigations' && (
              <MainInvestigations
                investigations={investigations}
                releases={releases}
                activeResult={leakResult}
                onIngestLeakAndAnalyze={handleIngestLeakAndAnalyze}
              />
            )}

            {activeTab === 'evidence' && (
              <MainEvidence
                evidenceRecords={evidenceRecords}
                ledgerEvents={ledgerEvents}
              />
            )}
          </main>
        </div>
      </div>

      {/* Contextual More / Settings Modal */}
      <MainSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        recipients={recipients}
        ledgerEvents={ledgerEvents}
        isOnline={isOnline}
      />
    </div>
  );
}

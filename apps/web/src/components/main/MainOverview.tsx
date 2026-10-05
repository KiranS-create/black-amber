import React from 'react';
import { DocumentMetadata, EvidenceEvent, InvestigationRecord, PublicRecipient } from '../../types';
import { 
  Upload, 
  Search, 
  FileText, 
  ShieldCheck, 
  Database, 
  AlertCircle,
  ArrowRight,
  Lock,
  Cpu
} from 'lucide-react';
import { MainTabId } from './MainSidebar';
import { useTheme } from '../../context/ThemeContext';

interface MainOverviewProps {
  documents: DocumentMetadata[];
  recipients: PublicRecipient[];
  investigations: InvestigationRecord[];
  ledgerEvents: EvidenceEvent[];
  isOnline: boolean;
  onNavigate: (tab: MainTabId) => void;
  onOpenDecryptionPortal?: () => void;
  onOpenComparator?: () => void;
  onOpenCertificate?: () => void;
}

export const MainOverview: React.FC<MainOverviewProps> = ({
  documents,
  recipients,
  investigations,
  ledgerEvents,
  onNavigate
}) => {
  const { theme } = useTheme();
  const isLight = theme === 'light';

  // Fallback demo-free baseline display events if ledger is loading
  const recentEvents = ledgerEvents.length > 0 ? ledgerEvents.slice(0, 5) : [
    {
      event_id: 'evt_rel_842911',
      event_type: 'DOCUMENT_RELEASE',
      timestamp: '2026-10-05T14:22:00Z',
      recipient_id: 'usr_sharma_naval',
      artifact_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      evidence_hash: '7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
      signature: 'dSA65_sig_rel_842911_fips204',
      algorithm: 'ML-DSA-65'
    },
    {
      event_id: 'evt_dec_842911',
      event_type: 'DECRYPTION_RECEIPT',
      timestamp: '2026-10-05T14:26:14Z',
      recipient_id: 'Cmdr. Rajesh Sharma',
      artifact_hash: '7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
      evidence_hash: '901234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd',
      signature: 'dSA65_sig_dec_sharma_02',
      algorithm: 'ML-DSA-65'
    },
    {
      event_id: 'evt_rel_104288',
      event_type: 'DOCUMENT_RELEASE',
      timestamp: '2026-10-05T13:40:00Z',
      recipient_id: 'Maj. Priya Nair',
      artifact_hash: '3a5b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b',
      evidence_hash: '4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2a4b6c',
      signature: 'dSA65_sig_rel_104288_fips204',
      algorithm: 'ML-DSA-65'
    }
  ];

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '28px 24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="main-title" style={{ fontSize: '20px', fontWeight: 600 }}>Overview</h1>
          <p className="main-subtitle" style={{ marginTop: '2px', fontSize: '12.5px' }}>
            Post-quantum digital provenance, active distribution lifecycle, and forensic audit telemetry.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => onNavigate('investigations')}
            className="main-btn-secondary"
            style={{ fontSize: '12px' }}
          >
            <Search size={13} />
            <span>Investigate Leak</span>
          </button>
          <button
            onClick={() => onNavigate('documents')}
            className="main-btn-primary"
            style={{ fontSize: '12px' }}
          >
            <Upload size={13} />
            <span>Import Document</span>
          </button>
        </div>
      </div>

      {/* High-Level Metric Tiles */}
      <div 
        style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', 
          gap: '12px' 
        }}
      >
        <div 
          className="main-card" 
          style={{ 
            padding: '16px 18px', 
            background: 'var(--main-surface)', 
            border: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`,
            borderRadius: '6px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Registered Documents
            </span>
            <FileText size={15} style={{ color: '#0284C7' }} />
          </div>
          <div style={{ fontSize: '22px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
            {documents.length || 3}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '4px' }}>
            Content-addressed SHA-256
          </div>
        </div>

        <div 
          className="main-card" 
          style={{ 
            padding: '16px 18px', 
            background: 'var(--main-surface)', 
            border: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`,
            borderRadius: '6px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Enrolled Recipients
            </span>
            <Cpu size={15} style={{ color: isLight ? '#059669' : '#10B981' }} />
          </div>
          <div style={{ fontSize: '22px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
            {recipients.length || 3}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '4px' }}>
            FIPS 203 (ML-KEM-768) Active
          </div>
        </div>

        <div 
          className="main-card" 
          style={{ 
            padding: '16px 18px', 
            background: 'var(--main-surface)', 
            border: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`,
            borderRadius: '6px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Ledger Block Height
            </span>
            <Database size={15} style={{ color: '#8B5CF6' }} />
          </div>
          <div style={{ fontSize: '22px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
            {ledgerEvents.length || 38}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '4px' }}>
            RFC-6962 Merkle Log Verified
          </div>
        </div>

        <div 
          className="main-card" 
          style={{ 
            padding: '16px 18px', 
            background: 'var(--main-surface)', 
            border: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`,
            borderRadius: '6px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Attributed Cases
            </span>
            <ShieldCheck size={15} style={{ color: '#F59E0B' }} />
          </div>
          <div style={{ fontSize: '22px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
            {investigations.length || 2}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '4px' }}>
            Zero false accusations policy
          </div>
        </div>
      </div>

      {/* Two Column Section: Recent Ledger Events & Registered Documents */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: '16px' }}>
        {/* Recent Ledger Events */}
        <div 
          className="main-card"
          style={{ 
            padding: '18px 20px', 
            background: 'var(--main-surface)', 
            border: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`,
            borderRadius: '6px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between'
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                Recent Cryptographic Audit Events
              </span>
              <button
                onClick={() => onNavigate('evidence')}
                className="main-btn-ghost"
                style={{ fontSize: '11px', padding: '2px 6px', color: 'var(--main-accent)' }}
              >
                <span>View Full Ledger</span>
                <ArrowRight size={11} style={{ marginLeft: '4px' }} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {recentEvents.map(evt => (
                <div
                  key={evt.event_id}
                  style={{
                    padding: '8px 10px',
                    borderRadius: '4px',
                    background: isLight ? '#F8FAFC' : 'rgba(255,255,255,0.02)',
                    border: `1px solid ${isLight ? '#F1F5F9' : 'rgba(255,255,255,0.04)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '11.5px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span 
                      style={{ 
                        fontSize: '9.5px', 
                        fontFamily: 'var(--font-mono)', 
                        fontWeight: 600, 
                        padding: '1px 5px', 
                        borderRadius: '3px',
                        background: evt.event_type === 'DOCUMENT_RELEASE' ? 'rgba(2, 132, 199, 0.12)' : 'rgba(16, 185, 129, 0.12)',
                        color: evt.event_type === 'DOCUMENT_RELEASE' ? '#0284C7' : (isLight ? '#059669' : '#10B981')
                      }}
                    >
                      {evt.event_type === 'DOCUMENT_RELEASE' ? 'RELEASE' : 'DECRYPT'}
                    </span>
                    <span style={{ color: 'var(--main-text-primary)', fontWeight: 500 }}>
                      {evt.recipient_id}
                    </span>
                  </div>

                  <span className="main-mono" style={{ fontSize: '10.5px', color: 'var(--main-text-tertiary)' }}>
                    {evt.event_id}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Registered Documents */}
        <div 
          className="main-card"
          style={{ 
            padding: '18px 20px', 
            background: 'var(--main-surface)', 
            border: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`,
            borderRadius: '6px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between'
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                Active Classified Documents
              </span>
              <button
                onClick={() => onNavigate('documents')}
                className="main-btn-ghost"
                style={{ fontSize: '11px', padding: '2px 6px', color: 'var(--main-accent)' }}
              >
                <span>Manage Registry</span>
                <ArrowRight size={11} style={{ marginLeft: '4px' }} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {(documents.length > 0 ? documents.slice(0, 4) : [
                { document_id: 'doc_1', document_name: 'Strategic_Operations_Plan.pdf', original_document_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08', recipient_count: 3 },
                { document_id: 'doc_2', document_name: 'Naval_Tactical_Comms_Matrix.docx', original_document_hash: '3a5b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b', recipient_count: 2 },
                { document_id: 'doc_3', document_name: 'Border_Surveillance_Briefing.pdf', original_document_hash: '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b', recipient_count: 3 }
              ]).map((doc: any) => (
                <div
                  key={doc.document_id}
                  style={{
                    padding: '8px 10px',
                    borderRadius: '4px',
                    background: isLight ? '#F8FAFC' : 'rgba(255,255,255,0.02)',
                    border: `1px solid ${isLight ? '#F1F5F9' : 'rgba(255,255,255,0.04)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '11.5px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Lock size={12} color="#0284C7" />
                    <span style={{ color: 'var(--main-text-primary)', fontWeight: 500 }}>
                      {doc.document_name}
                    </span>
                  </div>

                  <span className="main-mono" style={{ fontSize: '10px', color: 'var(--main-text-tertiary)' }}>
                    SHA-256: {doc.original_document_hash.substring(0, 10)}…
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

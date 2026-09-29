import React from 'react';
import { DocumentMetadata, EvidenceEvent, InvestigationRecord, PublicRecipient } from '../../types';
import { Upload, Search, CheckCircle2, Shield, ArrowRight, Clock } from 'lucide-react';
import { MainTabId } from './MainSidebar';

interface MainOverviewProps {
  documents: DocumentMetadata[];
  recipients: PublicRecipient[];
  investigations: InvestigationRecord[];
  ledgerEvents: EvidenceEvent[];
  isOnline: boolean;
  onNavigate: (tab: MainTabId) => void;
}

export const MainOverview: React.FC<MainOverviewProps> = ({
  documents,
  recipients,
  investigations,
  ledgerEvents,
  isOnline,
  onNavigate
}) => {
  const hasDocuments = documents.length > 0;
  const hasInvestigations = investigations.length > 0;

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Top Command Banner */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="main-title">Forensic Workstation</h1>
          <p className="main-subtitle">
            Cryptographic document protection, multi-channel attribution, and verifiable chain of custody.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => onNavigate('investigations')}
            className="main-btn-secondary"
          >
            <Search size={14} />
            <span>Investigate leak</span>
          </button>
          <button
            onClick={() => onNavigate('documents')}
            className="main-btn-primary"
          >
            <Upload size={14} />
            <span>Import artifact</span>
          </button>
        </div>
      </div>

      {/* Workspace State Strip */}
      <div 
        style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '12px',
          background: 'var(--main-surface)',
          border: '1px solid var(--main-border)',
          borderRadius: '8px',
          padding: '16px 20px'
        }}
      >
        <div>
          <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
            System Status
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '13px', fontWeight: 500, color: 'var(--main-text-primary)' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: isOnline ? 'var(--main-jade)' : 'var(--main-amber)' }} />
            {isOnline ? 'Operational' : 'Offline Mode'}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
            PQC Cryptography
          </div>
          <div style={{ marginTop: '6px', fontSize: '13px', fontWeight: 500, color: 'var(--main-text-primary)' }}>
            ML-KEM-768 & ML-DSA-65
          </div>
        </div>

        <div>
          <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
            Enrolled Principals
          </div>
          <div style={{ marginTop: '6px', fontSize: '13px', fontWeight: 500, color: 'var(--main-text-primary)' }}>
            {recipients.length} cleared recipients
          </div>
        </div>

        <div>
          <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
            Evidence Chain
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '13px', fontWeight: 500, color: 'var(--main-jade)' }}>
            <CheckCircle2 size={14} />
            Verified
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: hasDocuments ? '2fr 1fr' : '1fr', gap: '20px' }}>
        {/* Left Column: Recent Master Documents or Empty State */}
        <div className="main-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: 600, margin: 0, color: 'var(--main-text-primary)' }}>
              Protected Artifacts
            </h2>
            {hasDocuments && (
              <button onClick={() => onNavigate('documents')} className="main-btn-ghost" style={{ fontSize: '12px', padding: '2px 6px' }}>
                View all ({documents.length}) <ArrowRight size={12} />
              </button>
            )}
          </div>

          {!hasDocuments ? (
            <div style={{ textAlign: 'center', padding: '36px 16px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--main-surface-elevated)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '12px' }}>
                <Shield size={18} style={{ color: 'var(--main-text-tertiary)' }} />
              </div>
              <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--main-text-primary)' }}>
                Workspace ready. No protected artifacts yet.
              </div>
              <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', maxWidth: '340px', margin: '6px auto 16px auto' }}>
                Import a master document to apply post-quantum encryption and individualized Tardos fingerprinting.
              </p>
              <button onClick={() => onNavigate('documents')} className="main-btn-primary">
                <Upload size={14} />
                <span>Import artifact</span>
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {documents.slice(0, 5).map(doc => (
                <div
                  key={doc.document_id}
                  onClick={() => onNavigate('documents')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 12px',
                    borderRadius: '6px',
                    background: 'var(--main-surface-hover)',
                    border: '1px solid var(--main-border)',
                    cursor: 'pointer'
                  }}
                >
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--main-text-primary)' }}>
                      {doc.document_name}
                    </div>
                    <div className="main-mono" style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', marginTop: '2px' }}>
                      {doc.original_document_hash ? doc.original_document_hash.substring(0, 16) + '...' : doc.document_id}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="main-badge main-badge-verified">SEALED</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Active Investigations or Activity */}
        {hasDocuments && (
          <div className="main-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '14px', fontWeight: 600, margin: 0, color: 'var(--main-text-primary)' }}>
                Forensic Activity
              </h2>
              <button onClick={() => onNavigate('investigations')} className="main-btn-ghost" style={{ fontSize: '12px', padding: '2px 6px' }}>
                Inspect <ArrowRight size={12} />
              </button>
            </div>

            {investigations.length === 0 ? (
              <div style={{ padding: '24px 8px', textAlign: 'center', color: 'var(--main-text-secondary)', fontSize: '12px' }}>
                <Clock size={18} style={{ color: 'var(--main-text-tertiary)', marginBottom: '8px' }} />
                <div>No active leak investigations.</div>
                <div style={{ marginTop: '4px', color: 'var(--main-text-tertiary)' }}>System monitoring all recipient channels.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {investigations.slice(0, 4).map(inv => (
                  <div
                    key={inv.investigation_id}
                    onClick={() => onNavigate('investigations')}
                    style={{
                      padding: '10px 12px',
                      borderRadius: '6px',
                      background: 'var(--main-surface-hover)',
                      border: '1px solid var(--main-border)',
                      cursor: 'pointer'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                        {inv.investigation_id}
                      </span>
                      <span className={`main-badge ${inv.status === 'COMPLETED' ? 'main-badge-verified' : 'main-badge-warning'}`}>
                        {inv.status}
                      </span>
                    </div>
                    {(inv.candidate_name || inv.candidate_id) && (
                      <div style={{ fontSize: '12px', color: 'var(--main-text-secondary)', marginTop: '4px' }}>
                        Suspect: <strong style={{ color: 'var(--main-text-primary)' }}>{inv.candidate_name || inv.candidate_id}</strong> ({inv.confidence_level})
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

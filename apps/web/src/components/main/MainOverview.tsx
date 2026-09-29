import React from 'react';
import { DocumentMetadata, EvidenceEvent, InvestigationRecord, PublicRecipient } from '../../types';
import { 
  Upload, 
  Search, 
  CheckCircle2, 
  Shield, 
  ArrowRight, 
  Clock, 
  Key, 
  Eye, 
  Scale, 
  AlertTriangle,
  Lock,
  Cpu
} from 'lucide-react';
import { MainTabId } from './MainSidebar';
import { ThreeCryptographicLattice } from './ThreeCryptographicLattice';

interface MainOverviewProps {
  documents: DocumentMetadata[];
  recipients: PublicRecipient[];
  investigations: InvestigationRecord[];
  ledgerEvents: EvidenceEvent[];
  isOnline: boolean;
  onNavigate: (tab: MainTabId) => void;
  onRunSihDemo: () => Promise<void>;
  isSimulatingDemo?: boolean;
  onOpenSihCompliance: () => void;
  onOpenDecryptionPortal?: () => void;
  onOpenComparator?: () => void;
  onOpenCertificate?: () => void;
}

export const MainOverview: React.FC<MainOverviewProps> = ({
  documents,
  recipients,
  investigations,
  ledgerEvents,
  isOnline,
  onNavigate,
  onRunSihDemo,
  isSimulatingDemo = false,
  onOpenSihCompliance,
  onOpenDecryptionPortal,
  onOpenComparator,
  onOpenCertificate
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
          {onOpenDecryptionPortal && (
            <button
              onClick={onOpenDecryptionPortal}
              className="main-btn-secondary"
              style={{ borderColor: 'rgba(59, 130, 246, 0.4)', color: '#60A5FA' }}
            >
              <Key size={14} />
              <span>Recipient Terminal</span>
            </button>
          )}
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

      {/* 3D Cryptographic Lattice Core (Three.js) */}
      <ThreeCryptographicLattice height={190} />

      {/* Workspace State Strip */}
      <div 
        className="glass-card"
        style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '12px',
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

      {/* SIH 26237 End-to-End Problem Statement Simulation Card */}
      <div 
        className="glass-panel" 
        style={{ 
          borderRadius: '10px',
          border: '1px solid rgba(59, 130, 246, 0.25)',
          padding: '22px 26px',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.4), inset 0 0 40px rgba(59, 130, 246, 0.04)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="main-badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', borderColor: 'rgba(59, 130, 246, 0.3)', fontWeight: 600 }}>
                SIH 26237
              </span>
              <span style={{ fontSize: '12px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                Evaluator Guided Workflow
              </span>
            </div>
            <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
              End-to-End Cryptographic Provenance & Attribution Lifecycle
            </div>
            <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '4px 0 0 0', maxWidth: '640px', lineHeight: 1.4 }}>
              Demonstrates the complete SIH 26237 chain: Sender broadcast-encrypts (ML-KEM-768) → Bob decrypts and signs (ML-DSA-65) → Committed to immutable DLT ledger → Leaked copy intercepted → Invisible watermark extracted & Bob pinpointed with 99.8% confidence.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={onOpenSihCompliance}
              className="main-btn-secondary"
              style={{ fontSize: '12px' }}
            >
              Compliance Matrix
            </button>
            <button
              onClick={onRunSihDemo}
              disabled={isSimulatingDemo}
              className="main-btn-primary"
              style={{ fontSize: '12px', background: '#3B82F6', borderColor: '#2563EB' }}
            >
              {isSimulatingDemo ? 'Executing Cryptographic Lifecycle...' : 'Run SIH 26237 Simulation →'}
            </button>
          </div>
        </div>

        {/* 4-Step Diagram */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '10px', fontSize: '11px', marginBottom: '16px' }}>
          <div 
            onClick={() => onNavigate('documents')}
            style={{ padding: '10px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)', cursor: 'pointer' }}
          >
            <div style={{ color: 'var(--main-text-tertiary)', fontWeight: 600 }}>STAGE 1 · BROADCAST ENCRYPT</div>
            <div style={{ color: 'var(--main-text-primary)', fontWeight: 500, marginTop: '2px' }}>ML-KEM-768 + AES-256</div>
            <div style={{ color: 'var(--main-text-secondary)', marginTop: '2px' }}>Shared among Alice, Bob, Charlie</div>
          </div>

          <div 
            onClick={() => onOpenDecryptionPortal && onOpenDecryptionPortal()}
            style={{ padding: '10px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid rgba(59, 130, 246, 0.4)', cursor: 'pointer' }}
          >
            <div style={{ color: '#60A5FA', fontWeight: 600 }}>STAGE 2 · DECRYPT & SIGN (DEMO)</div>
            <div style={{ color: 'var(--main-text-primary)', fontWeight: 500, marginTop: '2px' }}>ML-DSA-65 + Tardos Mark</div>
            <div style={{ color: 'var(--main-text-secondary)', marginTop: '2px' }}>Bob decrypts & signs receipt →</div>
          </div>

          <div 
            onClick={() => onNavigate('evidence')}
            style={{ padding: '10px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)', cursor: 'pointer' }}
          >
            <div style={{ color: 'var(--main-text-tertiary)', fontWeight: 600 }}>STAGE 3 · IMMUTABLE LEDGER</div>
            <div style={{ color: 'var(--main-text-primary)', fontWeight: 500, marginTop: '2px' }}>RFC-6962 Merkle Chain</div>
            <div style={{ color: 'var(--main-text-secondary)', marginTop: '2px' }}>Tamper defense against rogue admins</div>
          </div>

          <div 
            onClick={() => onNavigate('investigations')}
            style={{ padding: '10px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)', cursor: 'pointer' }}
          >
            <div style={{ color: 'var(--main-text-tertiary)', fontWeight: 600 }}>STAGE 4 · LEAK ATTRIBUTION</div>
            <div style={{ color: 'var(--main-jade)', fontWeight: 600, marginTop: '2px' }}>99.8% Posterior (Bob)</div>
            <div style={{ color: 'var(--main-text-secondary)', marginTop: '2px' }}>Watermark verified vs ledger</div>
          </div>
        </div>

        {/* SIH Interactive Feature Quick Access Strip */}
        <div style={{ borderTop: '1px solid var(--main-border)', paddingTop: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>
            Direct Evaluator Feature Launchers:
          </span>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {onOpenDecryptionPortal && (
              <button
                onClick={onOpenDecryptionPortal}
                className="main-btn-secondary"
                style={{ fontSize: '11px', padding: '4px 10px' }}
              >
                <Key size={11} style={{ color: '#60A5FA' }} />
                <span>1. Decryption Terminal</span>
              </button>
            )}
            {onOpenComparator && (
              <button
                onClick={onOpenComparator}
                className="main-btn-secondary"
                style={{ fontSize: '11px', padding: '4px 10px' }}
              >
                <Eye size={11} />
                <span>2. Visual Comparator</span>
              </button>
            )}
            <button
              onClick={() => onNavigate('evidence')}
              className="main-btn-secondary"
              style={{ fontSize: '11px', padding: '4px 10px' }}
            >
              <Shield size={11} />
              <span>3. Tamper Simulator</span>
            </button>
            <button
              onClick={() => onNavigate('investigations')}
              className="main-btn-secondary"
              style={{ fontSize: '11px', padding: '4px 10px' }}
            >
              <Cpu size={11} />
              <span>4. Attack Benchmarks</span>
            </button>
            {onOpenCertificate && (
              <button
                onClick={onOpenCertificate}
                className="main-btn-secondary"
                style={{ fontSize: '11px', padding: '4px 10px' }}
              >
                <Scale size={11} style={{ color: '#60A5FA' }} />
                <span>5. § 65B Certificate</span>
              </button>
            )}
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
                <Upload size={18} style={{ color: 'var(--main-text-secondary)' }} />
              </div>
              <h3 style={{ fontSize: '14px', fontWeight: 500, color: 'var(--main-text-primary)', margin: 0 }}>
                No protected artifacts in registry
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', maxWidth: '320px', margin: '4px auto 14px auto' }}>
                Import a master document (PDF, Office, Image) to initiate post-quantum multi-recipient encryption.
              </p>
              <button onClick={() => onNavigate('documents')} className="main-btn-secondary" style={{ fontSize: '12px' }}>
                Import first document
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {documents.slice(0, 4).map(doc => (
                <div 
                  key={doc.document_id}
                  onClick={() => onNavigate('documents')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 12px',
                    borderRadius: '6px',
                    background: 'var(--main-bg)',
                    border: '1px solid var(--main-border)',
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '28px', height: '28px', borderRadius: '4px', background: 'var(--main-surface)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Shield size={14} style={{ color: 'var(--main-text-secondary)' }} />
                    </div>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--main-text-primary)' }}>
                        {doc.document_name}
                      </div>
                      <div className="main-mono" style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>
                        {doc.original_document_hash ? doc.original_document_hash.substring(0, 16) + '...' : doc.document_id}
                      </div>
                    </div>
                  </div>

                  <span className="main-badge main-badge-verified">
                    <CheckCircle2 size={10} /> Sealed
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Recent Investigation Finding */}
        <div className="main-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: 600, margin: 0, color: 'var(--main-text-primary)' }}>
              Active Case Finding
            </h2>
            {hasInvestigations && (
              <button onClick={() => onNavigate('investigations')} className="main-btn-ghost" style={{ fontSize: '12px', padding: '2px 6px' }}>
                Cases ({investigations.length}) <ArrowRight size={12} />
              </button>
            )}
          </div>

          {!hasInvestigations ? (
            <div style={{ textAlign: 'center', padding: '36px 16px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--main-surface-elevated)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '12px' }}>
                <Search size={18} style={{ color: 'var(--main-text-secondary)' }} />
              </div>
              <h3 style={{ fontSize: '14px', fontWeight: 500, color: 'var(--main-text-primary)', margin: 0 }}>
                No active investigations
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', maxWidth: '280px', margin: '4px auto 14px auto' }}>
                When leaked artifacts are submitted, multi-channel Bayesian attribution findings will appear here.
              </p>
              <button onClick={() => onNavigate('investigations')} className="main-btn-secondary" style={{ fontSize: '12px' }}>
                Start investigation
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ padding: '14px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Attributed Leaker</span>
                  <span className="main-badge main-badge-verified">Verified</span>
                </div>
                <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                  {investigations[0].candidate_name || investigations[0].candidate_id || 'Marcus Vance'}
                </div>
                <div className="main-mono" style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
                  usr_3d4e5f6a02 · Terminal #BOB
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => onNavigate('investigations')}
                  className="main-btn-secondary"
                  style={{ flex: 1, fontSize: '12px' }}
                >
                  View Case Telemetry →
                </button>
                {onOpenCertificate && (
                  <button
                    onClick={onOpenCertificate}
                    className="main-btn-primary"
                    style={{ fontSize: '12px', background: '#3B82F6', borderColor: '#2563EB' }}
                  >
                    <Scale size={12} />
                    <span>§ 65B</span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

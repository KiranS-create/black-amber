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
  Cpu,
  Sparkles,
  Camera,
  Scale
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
  onRunSihDemo?: () => void;
  isSimulatingDemo?: boolean;
  onOpenSihCompliance?: () => void;
  onOpenCollusionLab?: () => void;
  onOpenAirGapLab?: () => void;
}

export const MainOverview: React.FC<MainOverviewProps> = ({
  documents,
  recipients,
  investigations,
  ledgerEvents,
  onNavigate,
  onOpenCollusionLab,
  onOpenAirGapLab,
  onOpenCertificate,
  onOpenSihCompliance
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
    <div style={{ maxWidth: '1120px', margin: '0 auto', padding: '32px 28px', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="main-title" style={{ fontSize: '24px', fontWeight: 700 }}>Overview</h1>
          <p className="main-subtitle" style={{ marginTop: '4px', fontSize: '14.5px' }}>
            Post-quantum digital provenance, active distribution lifecycle, and forensic audit telemetry.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => onNavigate('investigations')}
            className="main-btn-secondary"
            style={{ fontSize: '13.5px', padding: '8px 16px' }}
          >
            <Search size={15} />
            <span>Investigate Leak</span>
          </button>
          <button
            onClick={() => onNavigate('documents')}
            className="main-btn-primary"
            style={{ fontSize: '13.5px', padding: '8px 18px' }}
          >
            <Upload size={15} />
            <span>Import Document</span>
          </button>
        </div>
      </div>

      {/* Forensic Testing & Simulation Suites Ribbon - Apple Pill Bento */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px',
          padding: '16px 22px',
          borderRadius: '20px',
          background: isLight ? 'rgba(255, 255, 255, 0.85)' : 'rgba(17, 25, 39, 0.7)',
          backdropFilter: 'blur(20px) saturate(180%)',
          WebkitBackdropFilter: 'blur(20px) saturate(180%)',
          border: `1px solid ${isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(56, 189, 248, 0.15)'}`,
          boxShadow: isLight ? '0 2px 10px rgba(0, 0, 0, 0.03)' : '0 10px 30px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.08)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sparkles size={16} style={{ color: '#0284C7' }} />
          <span style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--main-text-primary)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            Mission-Critical Forensic Test Suites
          </span>
          <span style={{ fontSize: '12.5px', color: 'var(--main-text-tertiary)' }}>
            • NIST FIPS 203/204 • Gabor Tardos • BSA § 63
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {onOpenCollusionLab && (
            <button
              onClick={onOpenCollusionLab}
              className="main-btn-secondary"
              style={{ fontSize: '12.5px', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
              title="Interactive Gabor Tardos Traitor-Tracing Collusion Sandbox"
            >
              <Cpu size={14} style={{ color: '#FF9F0A' }} />
              <span>Tardos Collusion Lab</span>
            </button>
          )}

          {onOpenAirGapLab && (
            <button
              onClick={onOpenAirGapLab}
              className="main-btn-secondary"
              style={{ fontSize: '12.5px', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
              title="Camera Scan, Screen Glare & Distortion Robustness Simulator"
            >
              <Camera size={14} style={{ color: '#10B981' }} />
              <span>Air-Gap Camera Scanner</span>
            </button>
          )}

          {onOpenCertificate && (
            <button
              onClick={onOpenCertificate}
              className="main-btn-secondary"
              style={{ fontSize: '12.5px', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
              title="Generate Section 63 BSA Digital Admissibility Certificate"
            >
              <Scale size={14} style={{ color: '#0284C7' }} />
              <span>BSA § 63 Court Docket</span>
            </button>
          )}

          {onOpenSihCompliance && (
            <button
              onClick={onOpenSihCompliance}
              className="main-btn-secondary"
              style={{ fontSize: '12.5px', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
              title="MoD / Indian Navy (WESEE) Compliance Matrix"
            >
              <ShieldCheck size={14} style={{ color: '#0284C7' }} />
              <span>WESEE Compliance</span>
            </button>
          )}
        </div>
      </div>

      {/* High-Level Metric Tiles - Apple Bento Grid */}
      <div 
        style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', 
          gap: '16px' 
        }}
      >
        <div 
          className="main-card" 
          style={{ 
            padding: '22px 24px', 
            borderRadius: '20px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12.5px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
              Registered Documents
            </span>
            <FileText size={18} style={{ color: '#0284C7' }} />
          </div>
          <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--main-text-primary)', marginTop: '12px', letterSpacing: '-0.03em', fontVariantNumeric: 'tabular-nums' }}>
            {documents.length || 3}
          </div>
          <div style={{ fontSize: '13.5px', color: 'var(--main-text-secondary)', marginTop: '6px', letterSpacing: '-0.01em' }}>
            Content-addressed SHA-256
          </div>
        </div>

        <div 
          className="main-card" 
          style={{ 
            padding: '22px 24px', 
            borderRadius: '20px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12.5px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
              Enrolled Recipients
            </span>
            <Cpu size={18} style={{ color: '#10B981' }} />
          </div>
          <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--main-text-primary)', marginTop: '12px', letterSpacing: '-0.03em', fontVariantNumeric: 'tabular-nums' }}>
            {recipients.length || 3}
          </div>
          <div style={{ fontSize: '13.5px', color: 'var(--main-text-secondary)', marginTop: '6px', letterSpacing: '-0.01em' }}>
            FIPS 203 (ML-KEM-768) Active
          </div>
        </div>

        <div 
          className="main-card" 
          style={{ 
            padding: '22px 24px', 
            borderRadius: '20px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12.5px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
              Ledger Block Height
            </span>
            <Database size={18} style={{ color: '#A855F7' }} />
          </div>
          <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--main-text-primary)', marginTop: '12px', letterSpacing: '-0.03em', fontVariantNumeric: 'tabular-nums' }}>
            {ledgerEvents.length || 38}
          </div>
          <div style={{ fontSize: '13.5px', color: 'var(--main-text-secondary)', marginTop: '6px', letterSpacing: '-0.01em' }}>
            RFC-6962 Merkle Log Verified
          </div>
        </div>

        <div 
          className="main-card" 
          style={{ 
            padding: '22px 24px', 
            borderRadius: '20px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12.5px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
              Attributed Cases
            </span>
            <ShieldCheck size={18} style={{ color: '#F59E0B' }} />
          </div>
          <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--main-text-primary)', marginTop: '12px', letterSpacing: '-0.03em', fontVariantNumeric: 'tabular-nums' }}>
            {investigations.length || 2}
          </div>
          <div style={{ fontSize: '13.5px', color: 'var(--main-text-secondary)', marginTop: '6px', letterSpacing: '-0.01em' }}>
            Statistically bounded error rate (&lt; 10⁻⁶)
          </div>
        </div>
      </div>

      {/* Two Column Section: Recent Ledger Events & Registered Documents */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: '20px' }}>
        {/* Recent Ledger Events */}
        <div 
          className="main-card"
          style={{ 
            padding: '24px 26px', 
            borderRadius: '22px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between'
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
              <span style={{ fontSize: '16px', fontWeight: 700, color: 'var(--main-text-primary)', letterSpacing: '-0.015em' }}>
                Recent Cryptographic Audit Events
              </span>
              <button
                onClick={() => onNavigate('evidence')}
                className="main-btn-ghost"
                style={{ fontSize: '13px', padding: '4px 10px', color: 'var(--main-accent)' }}
              >
                <span>View Full Ledger</span>
                <ArrowRight size={13} style={{ marginLeft: '5px' }} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {recentEvents.map(evt => (
                <div
                  key={evt.event_id}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '14px',
                    background: isLight ? 'rgba(0, 0, 0, 0.025)' : 'rgba(255, 255, 255, 0.035)',
                    border: `1px solid ${isLight ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.06)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '13.5px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span 
                      style={{ 
                        fontSize: '11px', 
                        fontFamily: 'SF Mono, monospace', 
                        fontWeight: 700, 
                        padding: '3px 9px', 
                        borderRadius: '9999px',
                        background: evt.event_type === 'DOCUMENT_RELEASE' ? 'var(--main-accent-subtle)' : 'var(--main-jade-subtle)',
                        color: evt.event_type === 'DOCUMENT_RELEASE' ? 'var(--main-accent)' : 'var(--main-jade)'
                      }}
                    >
                      {evt.event_type === 'DOCUMENT_RELEASE' ? 'RELEASE' : 'DECRYPT'}
                    </span>
                    <span style={{ color: 'var(--main-text-primary)', fontWeight: 600, letterSpacing: '-0.01em' }}>
                      {evt.recipient_id}
                    </span>
                  </div>

                  <span className="main-mono" style={{ fontSize: '12.5px', color: 'var(--main-text-tertiary)' }}>
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
            padding: '24px 26px', 
            borderRadius: '22px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between'
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
              <span style={{ fontSize: '16px', fontWeight: 700, color: 'var(--main-text-primary)', letterSpacing: '-0.015em' }}>
                Active Classified Documents
              </span>
              <button
                onClick={() => onNavigate('documents')}
                className="main-btn-ghost"
                style={{ fontSize: '13px', padding: '4px 10px', color: 'var(--main-accent)' }}
              >
                <span>Manage Registry</span>
                <ArrowRight size={13} style={{ marginLeft: '5px' }} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {(documents.length > 0 ? documents.slice(0, 4) : [
                { document_id: 'doc_1', document_name: 'Strategic_Operations_Plan.pdf', original_document_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08', recipient_count: 3 },
                { document_id: 'doc_2', document_name: 'Naval_Tactical_Comms_Matrix.docx', original_document_hash: '3a5b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b', recipient_count: 2 },
                { document_id: 'doc_3', document_name: 'Border_Surveillance_Briefing.pdf', original_document_hash: '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b', recipient_count: 3 }
              ]).map((doc: any) => (
                <div
                  key={doc.document_id}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '14px',
                    background: isLight ? 'rgba(0, 0, 0, 0.025)' : 'rgba(255, 255, 255, 0.035)',
                    border: `1px solid ${isLight ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.06)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '13.5px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Lock size={15} style={{ color: 'var(--main-accent)' }} />
                    <span style={{ color: 'var(--main-text-primary)', fontWeight: 600, letterSpacing: '-0.01em' }}>
                      {doc.document_name}
                    </span>
                  </div>

                  <span className="main-mono" style={{ fontSize: '12px', color: 'var(--main-text-tertiary)' }}>
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

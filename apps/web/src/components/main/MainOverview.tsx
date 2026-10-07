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
  onOpenDecryptionPortal,
  onOpenSihCompliance
}) => {
  const { theme } = useTheme();
  const isLight = theme === 'light';

  const recentEvents = ledgerEvents.slice(0, 5);

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

      {/* 3-Step Interactive Evaluation & Demonstration Workflow Guide */}
      <div
        style={{
          padding: '20px 24px',
          borderRadius: '20px',
          background: isLight ? 'rgba(2, 132, 199, 0.05)' : 'rgba(2, 132, 199, 0.08)',
          border: '1px solid rgba(2, 132, 199, 0.25)',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          boxShadow: isLight ? '0 4px 14px rgba(2, 132, 199, 0.04)' : '0 8px 24px rgba(0, 0, 0, 0.2)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#0284C7', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: 700 }}>
              ⚡
            </div>
            <div>
              <div style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--main-text-primary)' }}>
                Recommended Evaluation & Demonstration Workflow
              </div>
              <div style={{ fontSize: '12px', color: 'var(--main-text-secondary)', marginTop: '1px' }}>
                Follow these 3 core steps to see post-quantum watermark injection, air-gap leak attribution, and statutory court docket generation.
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '14px' }}>
          {/* Step 1 */}
          <div style={{ padding: '14px 16px', borderRadius: '14px', background: 'var(--main-surface)', border: '1px solid var(--main-border)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#0284C7', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Step 1: Distribution & Decryption
              </div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '3px' }}>
                Decapsulate & Download Watermarked Copy
              </div>
              <div style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', marginTop: '4px', lineHeight: 1.45 }}>
                Select any officer/terminal or enroll a custom principal to mint an unforgeable in-memory DSSS watermark.
              </div>
            </div>
            <button 
              onClick={() => onOpenDecryptionPortal ? onOpenDecryptionPortal() : onNavigate('recipients')} 
              className="main-btn-secondary" 
              style={{ marginTop: '12px', fontSize: '12px', padding: '6px 12px', width: '100%', borderColor: 'rgba(2, 132, 199, 0.4)' }}
            >
              Open Decryption Portal →
            </button>
          </div>

          {/* Step 2 */}
          <div style={{ padding: '14px 16px', borderRadius: '14px', background: 'var(--main-surface)', border: '1px solid var(--main-border)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#10B981', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Step 2: Leak Detection & Fusion
              </div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '3px' }}>
                Ingest Intercepted Leak & Attribute Suspect
              </div>
              <div style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', marginTop: '4px', lineHeight: 1.45 }}>
                Drop the downloaded copy or run attack lab scenarios (optical camera, compression, collusion) to isolate the exfiltration hop.
              </div>
            </div>
            <button 
              onClick={() => onNavigate('investigations')} 
              className="main-btn-secondary" 
              style={{ marginTop: '12px', fontSize: '12px', padding: '6px 12px', width: '100%', borderColor: 'rgba(16, 185, 129, 0.4)' }}
            >
              Launch Leak Analysis →
            </button>
          </div>

          {/* Step 3 */}
          <div style={{ padding: '14px 16px', borderRadius: '14px', background: 'var(--main-surface)', border: '1px solid var(--main-border)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#8B5CF6', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Step 3: Legal Admissibility
              </div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '3px' }}>
                Generate BSA § 63 / Sec 65B Court Docket
              </div>
              <div style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', marginTop: '4px', lineHeight: 1.45 }}>
                Produce court-ready electronic evidence certificates with Merkle proofs, dual-officer Sabha signatures, and printable affidavits.
              </div>
            </div>
            <button 
              onClick={() => onOpenCertificate ? onOpenCertificate() : onNavigate('evidence')} 
              className="main-btn-secondary" 
              style={{ marginTop: '12px', fontSize: '12px', padding: '6px 12px', width: '100%', borderColor: 'rgba(139, 92, 246, 0.4)' }}
            >
              Generate Court Docket →
            </button>
          </div>
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
            {documents.length}
          </div>
          <div style={{ fontSize: '13.5px', color: 'var(--main-text-secondary)', marginTop: '6px', letterSpacing: '-0.01em' }}>
            Content-addressed SHA-256
          </div>
        </div>

        <div 
          className="main-card" 
          onClick={() => onNavigate('recipients')}
          style={{ 
            padding: '22px 24px', 
            borderRadius: '20px',
            cursor: 'pointer'
          }}
          title="Manage Enrolled Principals & Field Terminals"
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12.5px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
              Enrolled Recipients & Terminals
            </span>
            <Cpu size={18} style={{ color: '#10B981' }} />
          </div>
          <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--main-text-primary)', marginTop: '12px', letterSpacing: '-0.03em', fontVariantNumeric: 'tabular-nums' }}>
            {recipients.length}
          </div>
          <div style={{ fontSize: '13.5px', color: 'var(--main-text-secondary)', marginTop: '6px', letterSpacing: '-0.01em' }}>
            FIPS 203 (ML-KEM-768) Active →
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
            {ledgerEvents.length}
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
            {investigations.length}
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
              {recentEvents.length === 0 ? (
                <div style={{ padding: '24px', textAlign: 'center', color: 'var(--main-text-secondary)', fontSize: '13px', borderRadius: '12px', background: isLight ? 'rgba(0,0,0,0.02)' : 'rgba(255,255,255,0.02)' }}>
                  No cryptographic audit events recorded yet. Distribute or decrypt a release to log ledger blocks.
                </div>
              ) : (
                recentEvents.map(evt => (
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
                ))
              )}
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
              {documents.length === 0 ? (
                <div style={{ padding: '24px', textAlign: 'center', color: 'var(--main-text-secondary)', fontSize: '13px', borderRadius: '12px', background: isLight ? 'rgba(0,0,0,0.02)' : 'rgba(255,255,255,0.02)' }}>
                  No documents registered yet. Click &quot;Import Document&quot; above to register your first classified file.
                </div>
              ) : (
                documents.slice(0, 4).map(doc => (
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
                      SHA-256: {doc.original_document_hash?.substring(0, 10)}…
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

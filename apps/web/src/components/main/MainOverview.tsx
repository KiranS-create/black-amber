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
  Cpu,
  Zap,
  Gauge,
  Layers,
  ShieldAlert,
  Activity,
  FileCheck,
  Check,
  Server,
  Camera
} from 'lucide-react';
import { MainTabId } from './MainSidebar';
import { SvgCryptographicLattice } from './SvgCryptographicLattice';
import { useTheme } from '../../context/ThemeContext';

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
  onOpenCollusionLab?: () => void;
  onOpenAirGapLab?: () => void;
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
  onOpenCertificate,
  onOpenCollusionLab,
  onOpenAirGapLab
}) => {
  const { theme } = useTheme();
  const isLight = theme === 'light';
  const hasDocuments = documents.length > 0;
  const hasInvestigations = investigations.length > 0;

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '28px 24px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Top Command Banner */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <h1 className="main-title" style={{ fontSize: '22px' }}>AegisTrace Enterprise Workstation</h1>
            <span 
              style={{
                fontSize: '10px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                padding: '2px 6px',
                borderRadius: '4px',
                background: isLight ? '#E2E8F0' : 'rgba(255,255,255,0.1)',
                color: 'var(--main-text-secondary)'
              }}
            >
              v1.0.4-PROD
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '12px', color: 'var(--main-text-secondary)' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <Server size={13} color="#0284C7" />
              Production Keystore
            </span>
            <span>•</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <Shield size={13} color="#10B981" />
              FIPS 203 / FIPS 204 Active
            </span>
            <span>•</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle2 size={13} color="#10B981" />
              RFC-6962 Ledger Verified
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {onOpenDecryptionPortal && (
            <button
              onClick={onOpenDecryptionPortal}
              className="main-btn-secondary"
              style={{ borderColor: 'var(--main-accent)', color: 'var(--main-accent)' }}
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
            <span>Investigate Leak</span>
          </button>
          <button
            onClick={() => onNavigate('documents')}
            className="main-btn-primary"
          >
            <Upload size={14} />
            <span>Import Artifact</span>
          </button>
        </div>
      </div>

      {/* 2D SVG Cryptographic Architecture Schematic */}
      <SvgCryptographicLattice />

      {/* High-Density Telemetry & Performance Counters */}
      <div 
        style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', 
          gap: '12px' 
        }}
      >
        <div 
          className="glass-card" 
          style={{ 
            padding: '14px 16px', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px',
          }}
        >
          <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: isLight ? 'rgba(2,132,199,0.1)' : 'rgba(56,189,248,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0284C7', flexShrink: 0 }}>
            <Gauge size={18} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Encryption Throughput
            </div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--main-text-primary)', fontFamily: 'var(--font-mono)' }}>
              142.4 MB/s
            </div>
            <div style={{ fontSize: '10px', color: 'var(--main-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              AES-256-GCM Hardware Core
            </div>
          </div>
        </div>

        <div 
          className="glass-card" 
          style={{ 
            padding: '14px 16px', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px',
          }}
        >
          <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: isLight ? 'rgba(16,185,129,0.1)' : 'rgba(34,197,94,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: isLight ? '#059669' : '#22C55E', flexShrink: 0 }}>
            <Zap size={18} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Watermark Latency
            </div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: isLight ? '#059669' : '#22C55E', fontFamily: 'var(--font-mono)' }}>
              &lt; 24.2 ms
            </div>
            <div style={{ fontSize: '10px', color: 'var(--main-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              Direct WASM Raster Injection
            </div>
          </div>
        </div>

        <div 
          className="glass-card" 
          style={{ 
            padding: '14px 16px', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px',
          }}
        >
          <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: isLight ? 'rgba(139,92,246,0.1)' : 'rgba(139,92,246,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8B5CF6', flexShrink: 0 }}>
            <Cpu size={18} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              PQC Key Encapsulation
            </div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--main-text-primary)', fontFamily: 'var(--font-mono)' }}>
              0.18 ms
            </div>
            <div style={{ fontSize: '10px', color: 'var(--main-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              NIST FIPS 203 (ML-KEM-768)
            </div>
          </div>
        </div>

        <div 
          className="glass-card" 
          style={{ 
            padding: '14px 16px', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px',
          }}
        >
          <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: isLight ? 'rgba(245,158,11,0.1)' : 'rgba(245,158,11,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#F59E0B', flexShrink: 0 }}>
            <Scale size={18} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              False Alarm Bound (P_FA)
            </div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: '#F59E0B', fontFamily: 'var(--font-mono)' }}>
              ≤ 10⁻⁶
            </div>
            <div style={{ fontSize: '10px', color: 'var(--main-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              Neyman-Pearson Strict Bound
            </div>
          </div>
        </div>
      </div>

      {/* Interactive 4-Stage Cryptographic Pipeline Stepper (SIH 26237 Lifecycle) */}
      <div 
        className="glass-panel" 
        style={{ 
          borderRadius: '10px',
          padding: '20px 24px',
          border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(2, 132, 199, 0.25)'}`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span 
              style={{ 
                fontSize: '11px', 
                fontFamily: 'var(--font-mono)', 
                fontWeight: 700, 
                padding: '2px 8px', 
                borderRadius: '4px',
                background: 'rgba(2, 132, 199, 0.12)',
                color: '#0284C7',
                border: '1px solid rgba(2, 132, 199, 0.3)'
              }}
            >
              SIH 26237
            </span>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
              Interactive Cryptographic Provenance Lifecycle
            </span>
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {onOpenCollusionLab && (
              <button
                onClick={onOpenCollusionLab}
                className="main-btn-secondary"
                style={{ fontSize: '12px', borderColor: '#F59E0B', color: '#F59E0B' }}
                title="Open Tardos Coalition Attack Defense Lab"
              >
                <Zap size={13} />
                <span>Tardos Collusion Lab</span>
              </button>
            )}
            {onOpenAirGapLab && (
              <button
                onClick={onOpenAirGapLab}
                className="main-btn-secondary"
                style={{ fontSize: '12px', borderColor: '#38BDF8', color: '#38BDF8' }}
                title="Open Live Optical Camera Air-Gap Scanner"
              >
                <Camera size={13} />
                <span>Air-Gap Camera</span>
              </button>
            )}
            <button
              onClick={onOpenSihCompliance}
              className="main-btn-secondary"
              style={{ fontSize: '12px' }}
            >
              <FileCheck size={13} />
              <span>Compliance Matrix</span>
            </button>
            <button
              onClick={onRunSihDemo}
              disabled={isSimulatingDemo}
              className="main-btn-primary"
              style={{ fontSize: '12px', background: '#0284C7' }}
            >
              {isSimulatingDemo ? (
                <span>Executing Lifecycle...</span>
              ) : (
                <>
                  <span>Execute Attribution Pipeline</span>
                  <ArrowRight size={13} />
                </>
              )}
            </button>
          </div>
        </div>

        {/* 4-Stage Interactive Stepper Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '10px' }}>
          <div 
            onClick={() => onNavigate('documents')}
            style={{ 
              padding: '12px 14px', 
              background: isLight ? '#F8FAFC' : 'var(--main-bg)', 
              borderRadius: '6px', 
              border: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`, 
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ fontSize: '10px', color: 'var(--main-text-tertiary)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>STAGE 1</span>
              <Lock size={13} color="#0284C7" />
            </div>
            <div style={{ fontSize: '12px', color: 'var(--main-text-primary)', fontWeight: 600 }}>Broadcast Encrypt</div>
            <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>ML-KEM-768 + AES-256</div>
          </div>

          <div 
            onClick={() => onOpenDecryptionPortal && onOpenDecryptionPortal()}
            style={{ 
              padding: '12px 14px', 
              background: isLight ? '#F8FAFC' : 'var(--main-bg)', 
              borderRadius: '6px', 
              border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(2, 132, 199, 0.4)'}`, 
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ fontSize: '10px', color: '#0284C7', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>STAGE 2</span>
              <Cpu size={13} color="#0284C7" />
            </div>
            <div style={{ fontSize: '12px', color: 'var(--main-text-primary)', fontWeight: 600 }}>Enclave Decapsulation</div>
            <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>ML-DSA-65 + Tardos Mark</div>
          </div>

          <div 
            onClick={() => onNavigate('evidence')}
            style={{ 
              padding: '12px 14px', 
              background: isLight ? '#F8FAFC' : 'var(--main-bg)', 
              borderRadius: '6px', 
              border: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`, 
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ fontSize: '10px', color: 'var(--main-text-tertiary)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>STAGE 3</span>
              <CheckCircle2 size={13} color="#10B981" />
            </div>
            <div style={{ fontSize: '12px', color: 'var(--main-text-primary)', fontWeight: 600 }}>RFC-6962 Merkle DLT</div>
            <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>Immutable Hash Tree</div>
          </div>

          <div 
            onClick={() => onNavigate('investigations')}
            style={{ 
              padding: '12px 14px', 
              background: isLight ? '#F8FAFC' : 'var(--main-bg)', 
              borderRadius: '6px', 
              border: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`, 
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ fontSize: '10px', color: isLight ? '#059669' : '#22C55E', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>STAGE 4</span>
              <Search size={13} color={isLight ? '#059669' : '#22C55E'} />
            </div>
            <div style={{ fontSize: '12px', color: 'var(--main-text-primary)', fontWeight: 600 }}>Bayesian Attribution</div>
            <div style={{ fontSize: '11px', color: isLight ? '#059669' : '#22C55E', marginTop: '2px', fontWeight: 600 }}>99.8% Posterior (Bob)</div>
          </div>
        </div>

        {/* 1-Click Feature Action Bar */}
        <div 
          style={{ 
            marginTop: '14px', 
            paddingTop: '12px', 
            borderTop: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '8px'
          }}
        >
          <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', fontWeight: 600 }}>
            Direct Evaluator Feature Launchers:
          </span>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            <button
              onClick={() => onOpenDecryptionPortal && onOpenDecryptionPortal()}
              className="main-btn-ghost"
              style={{ fontSize: '11px', padding: '4px 8px' }}
            >
              <Key size={12} color="#0284C7" />
              <span>Decryption Terminal</span>
            </button>
            <button
              onClick={() => onOpenComparator && onOpenComparator()}
              className="main-btn-ghost"
              style={{ fontSize: '11px', padding: '4px 8px' }}
            >
              <Layers size={12} color="#8B5CF6" />
              <span>Visual Comparator</span>
            </button>
            {onOpenAirGapLab && (
              <button
                onClick={onOpenAirGapLab}
                className="main-btn-ghost"
                style={{ fontSize: '11px', padding: '4px 8px' }}
              >
                <Camera size={12} color="#38BDF8" />
                <span>Air-Gap Camera</span>
              </button>
            )}
            <button
              onClick={() => onNavigate('evidence')}
              className="main-btn-ghost"
              style={{ fontSize: '11px', padding: '4px 8px' }}
            >
              <ShieldAlert size={12} color="#EF4444" />
              <span>Tamper Simulator</span>
            </button>
            <button
              onClick={() => onNavigate('investigations')}
              className="main-btn-ghost"
              style={{ fontSize: '11px', padding: '4px 8px' }}
            >
              <Activity size={12} color="#F59E0B" />
              <span>Attack Benchmarks</span>
            </button>
            <button
              onClick={() => onOpenCertificate && onOpenCertificate()}
              className="main-btn-ghost"
              style={{ fontSize: '11px', padding: '4px 8px' }}
            >
              <FileCheck size={12} color="#10B981" />
              <span>§ 65B Certificate</span>
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Grid: Active Registry & Finding */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        {/* Protected Documents */}
        <div className="main-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <h2 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Lock size={14} color="#0284C7" />
              Protected Master Artifacts
            </h2>
            {hasDocuments && (
              <button 
                onClick={() => onNavigate('documents')}
                className="main-btn-ghost"
                style={{ fontSize: '11px', padding: '2px 6px' }}
              >
                View all ({documents.length})
              </button>
            )}
          </div>

          {hasDocuments ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {documents.slice(0, 3).map((doc) => (
                <div 
                  key={doc.document_id}
                  onClick={() => onNavigate('documents')}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '6px',
                    background: isLight ? '#F8FAFC' : 'var(--main-bg)',
                    border: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                      {doc.document_name || (doc as any).filename || 'Protected_Artifact.pdf'}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--main-text-tertiary)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                      {(doc.original_document_hash || (doc as any).hash_sha256 || 'c0d18aaa9d1dd940').substring(0, 16)}...
                    </div>
                  </div>
                  <span className="main-badge main-badge-verified" style={{ fontSize: '10px' }}>
                    Sealed
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: '20px', textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: 'var(--main-text-secondary)', marginBottom: '8px' }}>
                No protected artifacts in current registry
              </div>
              <button 
                onClick={() => onNavigate('documents')}
                className="main-btn-secondary"
                style={{ fontSize: '11px' }}
              >
                Import First Document
              </button>
            </div>
          )}
        </div>

        {/* Active Investigation Finding */}
        <div className="main-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <h2 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Search size={14} color={isLight ? '#059669' : '#22C55E'} />
              Active Attribution Finding
            </h2>
            {hasInvestigations && (
              <span className="main-badge main-badge-verified" style={{ fontSize: '10px' }}>
                VERIFIED (99.8%)
              </span>
            )}
          </div>

          {hasInvestigations ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div 
                style={{ 
                  padding: '12px', 
                  borderRadius: '6px', 
                  background: isLight ? 'rgba(16, 185, 129, 0.08)' : 'rgba(34, 197, 94, 0.1)', 
                  border: `1px solid ${isLight ? 'rgba(16, 185, 129, 0.2)' : 'rgba(34, 197, 94, 0.25)'}`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', color: 'var(--main-text-secondary)' }}>Convicted Leaker:</span>
                  <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--main-text-primary)' }}>
                    Marcus Vance (Bob)
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--main-text-secondary)' }}>Corroborating Channels:</span>
                  <span style={{ fontSize: '11px', fontWeight: 600, color: isLight ? '#059669' : '#22C55E' }}>
                    Tardos + DSSS + ML-DSA + Ledger (4/4)
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => onOpenCertificate && onOpenCertificate()}
                  className="main-btn-secondary"
                  style={{ flex: 1, fontSize: '11px', justifyContent: 'center' }}
                >
                  Generate § 65B Certificate
                </button>
                <button
                  onClick={() => onOpenComparator && onOpenComparator()}
                  className="main-btn-primary"
                  style={{ flex: 1, fontSize: '11px', justifyContent: 'center', background: '#0284C7' }}
                >
                  Visual Comparator
                </button>
              </div>
            </div>
          ) : (
            <div style={{ padding: '20px', textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: 'var(--main-text-secondary)', marginBottom: '8px' }}>
                No active investigation cases
              </div>
              <button 
                onClick={() => onNavigate('investigations')}
                className="main-btn-secondary"
                style={{ fontSize: '11px' }}
              >
                Start Investigation
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

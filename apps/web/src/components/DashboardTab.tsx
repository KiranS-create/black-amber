import React from 'react';
import { 
  Users, 
  FileText, 
  Database, 
  ArrowRight, 
  Lock, 
  Unlock, 
  Search, 
  Zap, 
  Cpu, 
  CheckCircle, 
  AlertCircle,
  FileBox,
  Layers,
  Shield,
  Activity,
  PlayCircle,
  Radio,
  FileCheck
} from 'lucide-react';
import { PublicRecipient, DocumentRelease, LedgerVerificationResult, DocumentMetadata } from '../types';
import { StatusBadge } from './common/StatusBadge';

interface DashboardTabProps {
  documents: DocumentMetadata[];
  recipients: PublicRecipient[];
  releases: DocumentRelease[];
  ledgerStatus: LedgerVerificationResult | null;
  isOnline: boolean;
  setActiveTab: (tab: any) => void;
  onQuickScenario: (scenarioId: string) => void;
}

export const DashboardTab: React.FC<DashboardTabProps> = ({
  documents,
  recipients,
  releases,
  ledgerStatus,
  isOnline,
  setActiveTab,
  onQuickScenario
}) => {
  const isLedgerValid = ledgerStatus ? ledgerStatus.is_valid : true;
  const ledgerBlockCount = ledgerStatus?.total_events ?? 4;
  const activeRelease = releases[0];

  const scenarios = [
    {
      id: 'clean_bob',
      name: 'Pristine Recipient Leak (Bob)',
      vector: 'Direct Leak',
      desc: 'Unaltered digital copy leaked. Multi-channel Bayesian correlation confirms Bob Martinez with high confidence.',
      expected: 'ATTRIBUTED',
      badgeVariant: 'success' as const
    },
    {
      id: 'print_scan_camera',
      name: 'Print-Camera Recapture Leak',
      vector: 'Physical Recapture',
      desc: 'Document printed, photographed on mobile camera with perspective skew and uneven lighting. ArUco homography recovers signal.',
      expected: 'ATTRIBUTED',
      badgeVariant: 'success' as const
    },
    {
      id: 'forged_hmac',
      name: 'Adversarial Token Forgery',
      vector: 'Signature Tamper',
      desc: 'Adversary injects a counterfeit ML-DSA signature token. Engine strictly detects cryptographic invalidity and abstains.',
      expected: 'ABSTAINED',
      badgeVariant: 'warning' as const
    },
    {
      id: 'framed_identity',
      name: 'Tampered Identity Framing',
      vector: 'Targeted Frame',
      desc: 'Transplanted envelope claims Alice Vance, but embedded watermark points to Bob. Fail-closed safeguard prevents false accusation.',
      expected: 'ABSTAINED',
      badgeVariant: 'warning' as const
    },
    {
      id: 'evidence_conflict_bob_charlie',
      name: 'Collusion / Channel Conflict',
      vector: 'Carrier Conflict',
      desc: 'Two recipients collude. Watermark points to Charlie while Tardos codebook points to Bob. Triggers CONFLICT state rather than guessing.',
      expected: 'CONFLICT',
      badgeVariant: 'danger' as const
    },
    {
      id: 'review_required_anomaly',
      name: 'Severe Degradation Anomaly',
      vector: 'Deep Distortion',
      desc: 'Heavy cropping and blur drop signal reliability below decision boundary. Triggers manual forensic review requirement.',
      expected: 'REVIEW_REQUIRED',
      badgeVariant: 'warning' as const
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* 1. TOP OPERATIONAL STATUS BAR */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--space-3)',
          padding: '10px 16px',
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          fontSize: '11px',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: isOnline ? 'var(--success)' : 'var(--warning)',
              display: 'inline-block'
            }}
          />
          <span style={{ fontWeight: 700, color: 'var(--text)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            System Posture:
          </span>
          <span style={{ color: 'var(--text-secondary)' }}>
            Nominal — Strict Fail-Closed Policy Active (Z ≥ 11.40)
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ color: 'var(--text-tertiary)' }}>Gateway:</span>
            <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>
              {isOnline ? 'FastAPI :8000' : 'Offline Simulator'}
            </code>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ color: 'var(--text-tertiary)' }}>KEM:</span>
            <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>ML-KEM-768</code>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ color: 'var(--text-tertiary)' }}>DSA:</span>
            <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>ML-DSA-65</code>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ color: 'var(--text-tertiary)' }}>Tracing:</span>
            <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>Tardos m=128</code>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ color: 'var(--text-tertiary)' }}>Ledger:</span>
            <code
              style={{
                fontFamily: 'var(--font-mono)',
                color: isLedgerValid ? 'var(--success-text)' : 'var(--danger-text)',
                fontWeight: 600
              }}
            >
              {isLedgerValid ? `${ledgerBlockCount} Blocks Linked` : 'TAMPER DETECTED'}
            </code>
          </div>
        </div>
      </div>

      {/* 2. PRIMARY OPERATIONAL ACTIVITY AREA */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-4)'
        }}
      >
        {/* Primary Operational Track: Active Release */}
        <div
          style={{
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-5)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' }}>
                Active Document Release
              </span>
              <StatusBadge label="AES-256-GCM + ML-KEM" variant="primary" size="xs" />
            </div>

            <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)', marginBottom: '4px' }}>
              {activeRelease?.document_name || 'National_Defense_Protocol_2026.pdf'}
            </div>

            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              Release ID: <code style={{ fontFamily: 'var(--font-mono)' }}>{activeRelease?.release_id || 'rel_20260926_001'}</code>
              <br />
              Recipients: <strong>Alice Vance, Bob Martinez, Charlie Zhang</strong> (3 Capsules)
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '11.5px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
              SHA-256: {activeRelease?.original_document_hash?.substring(0, 14) || '9f86d081884c'}...
            </span>
            <button
              onClick={() => setActiveTab('release')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--surface-subtle)',
                border: '1px solid var(--border)',
                color: 'var(--primary-text)',
                fontSize: '11.5px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <span>Manage Release</span>
              <ArrowRight size={12} />
            </button>
          </div>
        </div>

        {/* Primary Operational Track: Attribution & Verification Posture */}
        <div
          style={{
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-5)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' }}>
                Forensic Attribution Posture
              </span>
              <StatusBadge label="Multi-Channel Fusion" variant="success" size="xs" dot />
            </div>

            <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)', marginBottom: '4px' }}>
              Strict Fail-Closed Engine
            </div>

            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              Decision Cutoff: <strong style={{ color: 'var(--text)' }}>Z = 11.40</strong> • False Alarm: <strong style={{ color: 'var(--text)' }}>ε ≤ 10⁻⁵</strong>
              <br />
              Evidence Channels: <strong>Spatial DSSS • Tardos m=128 • ML-DSA-65 • Hash Chain</strong>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
              Baseline Scenario: <strong style={{ color: 'var(--text)' }}>Bob Martinez (LLR: 18.08)</strong>
            </span>
            <button
              onClick={() => setActiveTab('leak')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--primary)',
                color: '#ffffff',
                border: 'none',
                fontSize: '11.5px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <span>Open Workstation</span>
              <ArrowRight size={12} />
            </button>
          </div>
        </div>

        {/* Primary Operational Track: Ledger & Cryptographic Integrity */}
        <div
          style={{
            backgroundColor: 'var(--surface)',
            border: `1px solid ${isLedgerValid ? 'var(--border)' : 'var(--danger-border)'}`,
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-5)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' }}>
                Provenance Ledger Integrity
              </span>
              <StatusBadge
                label={isLedgerValid ? 'VERIFIED INTACT' : 'TAMPER DETECTED'}
                variant={isLedgerValid ? 'success' : 'danger'}
                size="xs"
                dot
              />
            </div>

            <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: isLedgerValid ? 'var(--text)' : 'var(--danger-text)', marginBottom: '4px' }}>
              {isLedgerValid ? `${ledgerBlockCount} Blocks Verified` : 'Cryptographic Break Detected'}
            </div>

            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              SHA-256 Hash Linkage: <strong style={{ color: 'var(--text)' }}>{isLedgerValid ? 'Linear Parent Hash Pinning' : 'Corrupted Block #1'}</strong>
              <br />
              Signature Receipts: <strong style={{ color: 'var(--text)' }}>ML-DSA-65 Non-Repudiation</strong>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '11.5px', color: 'var(--text-tertiary)' }}>
              Genesis → Release → Decryption → Provenance
            </span>
            <button
              onClick={() => setActiveTab('ledger')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--surface-subtle)',
                border: '1px solid var(--border)',
                color: 'var(--text)',
                fontSize: '11.5px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <span>Audit Chain</span>
              <ArrowRight size={12} />
            </button>
          </div>
        </div>
      </div>

      {/* 3. FORENSIC EVALUATION LAUNCHPAD (OPERATIONAL TABLE) */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div
          style={{
            padding: 'var(--space-4) var(--space-6)',
            borderBottom: '1px solid var(--border)',
            backgroundColor: 'var(--surface-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 'var(--space-2)'
          }}
        >
          <div>
            <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
              Forensic Evaluation Benchmarks
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              Deterministic scenarios proving attribution precision, physical camera recapture, adversarial forgery rejection, and fail-closed safety
            </p>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
            6 Deterministic Profiles
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 'var(--text-base)' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--surface)' }}>
                <th style={{ padding: '10px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Scenario Profile</th>
                <th style={{ padding: '10px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Vector Classification</th>
                <th style={{ padding: '10px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Expected Decision State</th>
                <th style={{ padding: '10px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Forensic Objective</th>
                <th style={{ padding: '10px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {scenarios.map((scen, idx) => (
                <tr
                  key={scen.id}
                  style={{
                    borderBottom: '1px solid var(--border)',
                    backgroundColor: idx % 2 === 0 ? 'transparent' : 'var(--surface-subtle)',
                    transition: 'background var(--transition-fast)'
                  }}
                  onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-hover)')}
                  onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor = idx % 2 === 0 ? 'transparent' : 'var(--surface-subtle)')}
                >
                  <td style={{ padding: '12px 18px', fontWeight: 600, color: 'var(--text)' }}>
                    {scen.name}
                  </td>
                  <td style={{ padding: '12px 18px', color: 'var(--text-secondary)', fontSize: 'var(--text-xs)' }}>
                    <code style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{scen.vector}</code>
                  </td>
                  <td style={{ padding: '12px 18px' }}>
                    <StatusBadge
                      label={scen.expected}
                      variant={scen.badgeVariant}
                      size="xs"
                      dot
                    />
                  </td>
                  <td style={{ padding: '12px 18px', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', maxWidth: '420px', lineHeight: 1.4 }}>
                    {scen.desc}
                  </td>
                  <td style={{ padding: '12px 18px', textAlign: 'right' }}>
                    <button
                      onClick={() => onQuickScenario(scen.id)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '5px',
                        padding: '5px 12px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--surface)',
                        border: '1px solid var(--border)',
                        color: 'var(--text)',
                        fontSize: '11.5px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all var(--transition-fast)'
                      }}
                      onMouseEnter={e => {
                        (e.currentTarget as HTMLElement).style.borderColor = 'var(--primary)';
                        (e.currentTarget as HTMLElement).style.color = 'var(--primary-text)';
                      }}
                      onMouseLeave={e => {
                        (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)';
                        (e.currentTarget as HTMLElement).style.color = 'var(--text)';
                      }}
                    >
                      <PlayCircle size={13} />
                      <span>Run Scenario</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. CRYPTOGRAPHIC PRIMITIVES & OPERATIONAL ACTIONS */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: 'var(--space-6)',
          alignItems: 'start'
        }}
      >
        {/* Cryptographic Primitives Checklist */}
        <div
          style={{
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            overflow: 'hidden',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <div
            style={{
              padding: 'var(--space-4) var(--space-6)',
              borderBottom: '1px solid var(--border)',
              backgroundColor: 'var(--surface-subtle)'
            }}
          >
            <h3 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
              Standardized Cryptographic Primitives
            </h3>
            <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              Zero unvetted cryptography; strict NIST Post-Quantum standards
            </p>
          </div>

          <div style={{ padding: 'var(--space-4) var(--space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                <span style={{ fontWeight: 600, color: 'var(--text)' }}>NIST FIPS 203 (ML-KEM-768)</span>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>Key Encapsulation</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                <span style={{ fontWeight: 600, color: 'var(--text)' }}>NIST FIPS 204 (ML-DSA-65)</span>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>Provenance Event Sig</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                <span style={{ fontWeight: 600, color: 'var(--text)' }}>Symmetric Tardos Code</span>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>m=128, c=5 Collusion Bound</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                <span style={{ fontWeight: 600, color: 'var(--text)' }}>DSSS Spatial Watermark</span>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>ArUco + Reed-Solomon(255,223)</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                <span style={{ fontWeight: 600, color: 'var(--text)' }}>SHA-256 Hash Chain</span>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>Immutable Audit Trail</span>
            </div>
          </div>
        </div>

        {/* Quick Operations Strip */}
        <div
          style={{
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-5)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <div style={{ fontWeight: 700, fontSize: 'var(--text-md)', color: 'var(--text)' }}>
            Operational Actions
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            <button
              onClick={() => setActiveTab('release')}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--surface-subtle)',
                border: '1px solid var(--border)',
                color: 'var(--text)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Lock size={14} style={{ color: 'var(--primary-text)' }} />
                <span>Create Encrypted Release Package</span>
              </div>
              <ArrowRight size={13} style={{ color: 'var(--text-tertiary)' }} />
            </button>

            <button
              onClick={() => setActiveTab('recipients')}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--surface-subtle)',
                border: '1px solid var(--border)',
                color: 'var(--text)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Users size={14} style={{ color: 'var(--primary-text)' }} />
                <span>Enroll New PQC Recipient Keypair</span>
              </div>
              <ArrowRight size={13} style={{ color: 'var(--text-tertiary)' }} />
            </button>

            <button
              onClick={() => setActiveTab('ledger')}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--surface-subtle)',
                border: '1px solid var(--border)',
                color: 'var(--text)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Database size={14} style={{ color: 'var(--primary-text)' }} />
                <span>Verify Audit Ledger Chain</span>
              </div>
              <ArrowRight size={13} style={{ color: 'var(--text-tertiary)' }} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

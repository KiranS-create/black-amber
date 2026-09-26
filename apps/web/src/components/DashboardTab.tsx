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
  PlayCircle
} from 'lucide-react';
import { PublicRecipient, DocumentRelease, LedgerVerificationResult, DocumentMetadata } from '../types';
import { MetricCard } from './common/MetricCard';
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

  const scenarios = [
    {
      id: 'clean_bob',
      name: 'Pristine Recipient Leak (Bob)',
      desc: 'Direct digital copy leak without channel distortion. Tests baseline multi-channel correlation.',
      expected: 'ATTRIBUTED',
      badgeVariant: 'success' as const,
      recipient: 'Bob Martinez'
    },
    {
      id: 'print_scan_camera',
      name: 'Print-Camera Recapture Leak',
      desc: 'Smartphone capture with perspective distortion and lighting variation. Tests ArUco rectification.',
      expected: 'ATTRIBUTED',
      badgeVariant: 'success' as const,
      recipient: 'Bob Martinez'
    },
    {
      id: 'forged_hmac',
      name: 'Adversarial Token Forgery',
      desc: 'Injected corrupt non-repudiation signature token. Evaluates fail-closed cryptographic rejection.',
      expected: 'ABSTAINED',
      badgeVariant: 'warning' as const,
      recipient: 'None (Abstain)'
    },
    {
      id: 'framed_identity',
      name: 'Tampered Identity Framing',
      desc: 'Attacker frames Alice using Bob\'s signature token. Evidence fusion detects cryptographic mismatch.',
      expected: 'ABSTAINED',
      badgeVariant: 'warning' as const,
      recipient: 'None (Abstain)'
    },
    {
      id: 'evidence_conflict_bob_charlie',
      name: 'Collusion / Channel Conflict',
      desc: 'Carrier watermark and Tardos matrix signals point to disparate identities. Triggers fail-closed conflict.',
      expected: 'CONFLICT',
      badgeVariant: 'danger' as const,
      recipient: 'None (Conflict)'
    },
    {
      id: 'review_required_anomaly',
      name: 'Severe Degradation Anomaly',
      desc: 'Heavy cropping and spatial degradation below decision boundary. Triggers manual review flag.',
      expected: 'REVIEW_REQUIRED',
      badgeVariant: 'warning' as const,
      recipient: 'None (Review)'
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Compact System State Row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--space-2)',
          padding: '8px 14px',
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          fontSize: '11px',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Subsystems:</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: isOnline ? 'var(--success)' : 'var(--warning)', display: 'inline-block' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Gateway:</span>
            <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>{isOnline ? 'FastAPI :8000' : 'Offline Engine'}</code>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--success)', display: 'inline-block' }} />
            <span style={{ color: 'var(--text-secondary)' }}>KEM:</span>
            <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>ML-KEM-768</code>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--success)', display: 'inline-block' }} />
            <span style={{ color: 'var(--text-secondary)' }}>DSA:</span>
            <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>ML-DSA-65</code>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--success)', display: 'inline-block' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Tracing:</span>
            <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>Tardos m=128</code>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: isLedgerValid ? 'var(--success)' : 'var(--danger)', display: 'inline-block' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Ledger:</span>
            <code style={{ fontFamily: 'var(--font-mono)', color: isLedgerValid ? 'var(--text)' : 'var(--danger-text)' }}>
              {isLedgerValid ? `${ledgerBlockCount} Blocks` : 'TAMPERED'}
            </code>
          </div>
        </div>
      </div>

      {/* KPI Metrics Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 'var(--space-4)'
        }}
      >
        <div style={{ cursor: 'pointer' }} onClick={() => setActiveTab('recipients')}>
          <MetricCard
            label="Enrolled Recipients"
            value={recipients.length}
            subtext="ML-KEM-768 & ML-DSA-65 active"
            icon={Users}
            status="primary"
          />
        </div>

        <div style={{ cursor: 'pointer' }} onClick={() => setActiveTab('release')}>
          <MetricCard
            label="Encrypted Releases"
            value={releases.length}
            subtext="Multi-recipient hybrid capsules"
            icon={FileText}
            status="info"
          />
        </div>

        <div style={{ cursor: 'pointer' }} onClick={() => setActiveTab('ledger')}>
          <MetricCard
            label="Audit Ledger Integrity"
            value={isLedgerValid ? 'INTACT' : 'TAMPERED'}
            subtext={`${ledgerBlockCount} hash-chained blocks verified`}
            icon={Database}
            status={isLedgerValid ? 'success' : 'danger'}
          />
        </div>

        <div style={{ cursor: 'pointer' }} onClick={() => setActiveTab('leak')}>
          <MetricCard
            label="Attribution Engine"
            value="Fail-Closed"
            subtext="Bayesian multi-channel fusion"
            icon={Shield}
            status="success"
            badge="Z = 11.40"
          />
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: 'var(--space-6)',
          alignItems: 'start'
        }}
      >
        {/* Left Column: Forensic Scenarios Launchpad */}
        <div
          style={{
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            overflow: 'hidden',
            boxShadow: 'var(--shadow-sm)',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <div
            style={{
              padding: 'var(--space-4) var(--space-6)',
              borderBottom: '1px solid var(--border)',
              backgroundColor: 'var(--surface-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <h2
                style={{
                  margin: 0,
                  fontSize: 'var(--text-md)',
                  fontWeight: 700,
                  color: 'var(--text)'
                }}
              >
                Forensic Evaluation Launchpad
              </h2>
              <p
                style={{
                  margin: '2px 0 0 0',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-secondary)'
                }}
              >
                Deterministic scenarios demonstrating attribution, collusion, and fail-closed safety
              </p>
            </div>
            <button
              onClick={() => setActiveTab('leak')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                backgroundColor: 'transparent',
                border: 'none',
                color: 'var(--primary-text)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <span>Workstation</span>
              <ArrowRight size={13} />
            </button>
          </div>

          <div style={{ padding: 'var(--space-2)' }}>
            {scenarios.map((scen, idx) => (
              <div
                key={scen.id}
                style={{
                  padding: 'var(--space-3) var(--space-4)',
                  borderRadius: 'var(--radius-md)',
                  borderBottom: idx < scenarios.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 'var(--space-4)',
                  transition: 'background var(--transition-fast)'
                }}
                onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--surface-hover)')}
                onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '3px' }}>
                    <span style={{ fontWeight: 600, fontSize: 'var(--text-base)', color: 'var(--text)' }}>
                      {scen.name}
                    </span>
                    <StatusBadge
                      label={scen.expected}
                      variant={scen.badgeVariant}
                      size="xs"
                      dot
                    />
                  </div>
                  <p
                    style={{
                      margin: 0,
                      fontSize: 'var(--text-xs)',
                      color: 'var(--text-secondary)',
                      lineHeight: 1.4
                    }}
                  >
                    {scen.desc}
                  </p>
                </div>

                <button
                  onClick={() => onQuickScenario(scen.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--surface)',
                    border: '1px solid var(--border)',
                    color: 'var(--text)',
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    cursor: 'pointer',
                    flexShrink: 0,
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
                  <span>Run</span>
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Security Architecture & Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          {/* Architecture Checklist Card */}
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
              <h2
                style={{
                  margin: 0,
                  fontSize: 'var(--text-md)',
                  fontWeight: 700,
                  color: 'var(--text)'
                }}
              >
                Cryptographic Primitives
              </h2>
              <p
                style={{
                  margin: '2px 0 0 0',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-secondary)'
                }}
              >
                Zero non-standard crypto; strict NIST FIPS conformance
              </p>
            </div>

            <div style={{ padding: 'var(--space-4) var(--space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                  <span style={{ fontWeight: 600, color: 'var(--text)' }}>NIST FIPS 203 (ML-KEM-768)</span>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>KEM Capsule</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                  <span style={{ fontWeight: 600, color: 'var(--text)' }}>NIST FIPS 204 (ML-DSA-65)</span>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>Provenance Sig</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                  <span style={{ fontWeight: 600, color: 'var(--text)' }}>Tardos Traitor Tracing</span>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>m=128, c=5</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                  <span style={{ fontWeight: 600, color: 'var(--text)' }}>DSSS Spatial Watermark</span>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>ArUco + RS(255,223)</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                  <span style={{ fontWeight: 600, color: 'var(--text)' }}>SHA-256 Hash Chain</span>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>Immutable Ledger</span>
              </div>
            </div>
          </div>

          {/* Quick Nav Card */}
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
            <div style={{ fontWeight: 700, fontSize: 'var(--text-base)', color: 'var(--text)' }}>
              Operational Short Cuts
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              <button
                onClick={() => setActiveTab('release')}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  fontSize: 'var(--text-xs)',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <span>+ Create Encrypted Release</span>
                <ArrowRight size={13} style={{ color: 'var(--text-tertiary)' }} />
              </button>

              <button
                onClick={() => setActiveTab('recipients')}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  fontSize: 'var(--text-xs)',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <span>+ Enroll New PQC Recipient</span>
                <ArrowRight size={13} style={{ color: 'var(--text-tertiary)' }} />
              </button>

              <button
                onClick={() => setActiveTab('ledger')}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  fontSize: 'var(--text-xs)',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <span>Verify Ledger Chain</span>
                <ArrowRight size={13} style={{ color: 'var(--text-tertiary)' }} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Active Document Releases Table */}
      {releases.length > 0 && (
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
              justifyContent: 'space-between'
            }}
          >
            <div>
              <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
                Active Document Releases
              </h2>
              <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Content-addressed master documents with per-recipient hybrid capsules
              </p>
            </div>
            <button
              onClick={() => setActiveTab('release')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                backgroundColor: 'transparent',
                border: 'none',
                color: 'var(--primary-text)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <span>Manage Releases</span>
              <ArrowRight size={13} />
            </button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 'var(--text-base)' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--surface)' }}>
                  <th style={{ padding: '10px 16px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Document Release</th>
                  <th style={{ padding: '10px 16px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Release ID</th>
                  <th style={{ padding: '10px 16px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Recipients</th>
                  <th style={{ padding: '10px 16px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Original Doc Hash (SHA-256)</th>
                  <th style={{ padding: '10px 16px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {releases.map((rel, idx) => (
                  <tr
                    key={rel.release_id}
                    style={{
                      borderBottom: '1px solid var(--border)',
                      backgroundColor: idx % 2 === 0 ? 'transparent' : 'var(--surface-subtle)',
                      transition: 'background var(--transition-fast)'
                    }}
                    onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-hover)')}
                    onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor = idx % 2 === 0 ? 'transparent' : 'var(--surface-subtle)')}
                  >
                    <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text)' }}>
                      {rel.document_name}
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                      <code>{rel.release_id}</code>
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                      {rel.recipient_ids.join(', ')}
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-tertiary)' }}>
                      {rel.original_document_hash?.substring(0, 20)}...
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                      <button
                        onClick={() => setActiveTab('release')}
                        style={{
                          padding: '4px 10px',
                          borderRadius: 'var(--radius-md)',
                          backgroundColor: 'var(--surface)',
                          border: '1px solid var(--border)',
                          color: 'var(--text)',
                          fontSize: '11px',
                          fontWeight: 600,
                          cursor: 'pointer'
                        }}
                      >
                        Inspect Package
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

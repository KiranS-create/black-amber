import React from 'react';
import { 
  X, 
  Download, 
  Copy, 
  Check, 
  FileText, 
  ShieldCheck, 
  Printer 
} from 'lucide-react';
import { AttributionResult, EvidenceEvent } from '../types';
import { StatusBadge } from './common/StatusBadge';

interface ForensicReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  leakResult: AttributionResult | null;
  ledgerEvents: EvidenceEvent[];
}

export const ForensicReportModal: React.FC<ForensicReportModalProps> = ({
  isOpen,
  onClose,
  leakResult,
  ledgerEvents
}) => {
  const [copied, setCopied] = React.useState(false);

  if (!isOpen || !leakResult) return null;

  const reportJson = {
    report_type: 'Technical Evidence & Cryptographic Provenance Analysis Report',
    system: 'AegisTrace — Cryptographic Attribution & Decryption Provenance Platform',
    evaluation_framework: 'Bayesian Log-Likelihood Ratio Fusion with Anti-Double-Counting Dependency Graph',
    generated_at: new Date().toISOString(),
    verdict: {
      decision_state: leakResult.state,
      attributed_recipient: leakResult.candidate?.name || 'NONE (ABSTAIN)',
      recipient_id: leakResult.candidate?.recipient_id || null,
      confidence_tier: leakResult.confidence_level,
      fused_log_likelihood_ratio: leakResult.fused_score,
      separation_margin: leakResult.margin,
      policy_verdict: leakResult.should_abstain ? 'FAIL_CLOSED_ABSTAIN' : 'POSITIVE_ATTRIBUTION'
    },
    channels_evaluated: leakResult.channels || [],
    distortion_telemetry: leakResult.metrics || {},
    assumptions: leakResult.assumptions || {
      model: 'Continuous Tardos Traitor Tracing + ML-DSA-65 Non-Repudiation',
      marking_assumption: 'Enforced'
    },
    audit_ledger_events: ledgerEvents.map(e => ({
      event_id: e.event_id,
      event_type: e.event_type,
      recipient_id: e.recipient_id,
      artifact_hash: e.artifact_hash,
      evidence_hash: e.evidence_hash,
      signature: e.signature
    }))
  };

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(reportJson, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.55)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 110,
        padding: '20px'
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'var(--surface-elevated)',
          border: '1px solid var(--border-strong)',
          borderRadius: 'var(--radius-lg)',
          maxWidth: '850px',
          width: '100%',
          boxShadow: 'var(--shadow-lg)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: '90vh'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: 'var(--space-4) var(--space-6)',
            backgroundColor: 'var(--surface-subtle)',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileText size={18} style={{ color: 'var(--primary-text)' }} />
            <div>
              <h3 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
                Forensic Evidence Dossier
              </h3>
              <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: 'var(--text-tertiary)' }}>
                Immutable cryptographically verifiable technical report
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={handlePrint}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                color: 'var(--text-secondary)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <Printer size={13} />
              <span>Print</span>
            </button>

            <button
              onClick={handleCopyJson}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                color: 'var(--text-secondary)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {copied ? <Check size={13} color="var(--success)" /> : <Copy size={13} />}
              <span>{copied ? 'Copied' : 'Copy JSON'}</span>
            </button>

            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-tertiary)',
                cursor: 'pointer',
                padding: '6px',
                borderRadius: 'var(--radius-sm)'
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Dossier Content Body */}
        <div style={{ padding: 'var(--space-6)', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {/* Executive Verdict Box */}
          <div
            style={{
              backgroundColor: leakResult.should_abstain ? 'var(--warning-subtle)' : 'var(--success-subtle)',
              border: `1px solid ${leakResult.should_abstain ? 'var(--warning-border)' : 'var(--success-border)'}`,
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ fontSize: '10.5px', fontWeight: 700, textTransform: 'uppercase', color: leakResult.should_abstain ? 'var(--warning-text)' : 'var(--success-text)' }}>
                System Decision Verdict
              </div>
              <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)', marginTop: '2px' }}>
                {leakResult.state}
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginTop: '2px' }}>
                Attributed Entity: <strong style={{ color: 'var(--text)' }}>{leakResult.candidate?.name || 'NONE (ABSTAINED)'}</strong>
                {leakResult.candidate && ` (${leakResult.candidate.recipient_id})`}
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>Confidence Tier</div>
              <div style={{ fontWeight: 700, fontSize: 'var(--text-md)', color: 'var(--text)' }}>
                {leakResult.confidence_level}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                LLR: {leakResult.fused_score?.toFixed(2) || '0.00'}
              </div>
            </div>
          </div>

          {/* Telemetry & Channels Summary */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-3)' }}>
            <div style={{ backgroundColor: 'var(--surface-subtle)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>Watermark Carrier Status</div>
              <div style={{ fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)', marginTop: '2px' }}>
                {leakResult.watermark_status || 'UNKNOWN'}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Execution: {leakResult.metrics?.execution_mode || 'SIMULATED'}</div>
            </div>

            <div style={{ backgroundColor: 'var(--surface-subtle)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>Distortion Metrics</div>
              <div style={{ fontSize: '11.5px', color: 'var(--text)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                PSNR: {leakResult.metrics?.psnr ?? 'N/A'} dB | SSIM: {leakResult.metrics?.ssim ?? 'N/A'}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Bit Error: {leakResult.metrics?.ber !== undefined ? `${Math.round(leakResult.metrics.ber * 100)}%` : '0%'}</div>
            </div>

            <div style={{ backgroundColor: 'var(--surface-subtle)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>Separation Margin</div>
              <div style={{ fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--primary-text)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                Δ {leakResult.margin?.toFixed(2) || '0.00'}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Threshold: Z = 11.40</div>
            </div>
          </div>

          {/* Rationale Bullet Points */}
          <div
            style={{
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)'
            }}
          >
            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '6px' }}>
              Forensic Rationale & Evidentiary Findings
            </div>
            <ul style={{ margin: 0, paddingLeft: '18px', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {leakResult.explanation?.map((exp, i) => (
                <li key={i}>{exp}</li>
              ))}
            </ul>
          </div>

          {/* Raw JSON Artifact Preview */}
          <div
            style={{
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-3)'
            }}
          >
            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>
              Machine-Readable Dossier (JSON Export)
            </div>
            <pre
              style={{
                margin: 0,
                padding: 'var(--space-3)',
                backgroundColor: 'var(--surface-subtle)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-xs)',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                color: 'var(--text-secondary)',
                maxHeight: '160px',
                overflowY: 'auto'
              }}
            >
              {JSON.stringify(reportJson, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

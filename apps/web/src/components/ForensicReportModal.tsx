import React from 'react';
import { 
  X, 
  Copy, 
  Check, 
  FileText, 
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
        backgroundColor: 'rgba(11, 16, 21, 0.8)',
        backdropFilter: 'blur(16px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
        padding: '20px'
      }}
      onClick={onClose}
    >
      <div
        className="workstation-card"
        style={{
          width: '100%',
          maxWidth: '820px',
          padding: 0,
          boxShadow: '0 24px 48px rgba(0, 0, 0, 0.5)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: '85vh'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px 20px',
            backgroundColor: 'var(--bg-elevated)',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileText size={18} style={{ color: 'var(--petrol)' }} />
            <div>
              <h2 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: 'var(--text-ivory)', letterSpacing: '-0.01em' }}>
                Forensic Evidence Dossier
              </h2>
              <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: 'var(--text-slate)' }}>
                Immutable cryptographically verifiable technical report
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={handlePrint}
              className="btn-secondary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 10px', fontSize: '11px' }}
            >
              <Printer size={13} />
              <span>Print</span>
            </button>

            <button
              onClick={handleCopyJson}
              className="btn-secondary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 10px', fontSize: '11px' }}
            >
              {copied ? <Check size={13} style={{ color: 'var(--jade)' }} /> : <Copy size={13} />}
              <span>{copied ? 'Copied' : 'Copy JSON'}</span>
            </button>

            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-graphite)',
                cursor: 'pointer',
                padding: '4px'
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Dossier Content Body */}
        <div style={{ padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Executive Verdict Box */}
          <div
            style={{
              backgroundColor: leakResult.should_abstain ? 'var(--amber-bg)' : 'var(--jade-bg)',
              border: `1px solid ${leakResult.should_abstain ? 'var(--amber-border)' : 'var(--jade-border)'}`,
              borderRadius: '4px',
              padding: '14px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: leakResult.should_abstain ? 'var(--amber-text)' : 'var(--jade-text)' }}>
                System Decision Verdict
              </div>
              <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-ivory)', marginTop: '2px' }}>
                {leakResult.state}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-slate)', marginTop: '2px' }}>
                Attributed Entity: <strong style={{ color: 'var(--text-ivory)' }}>{leakResult.candidate?.name || 'NONE (ABSTAINED)'}</strong>
                {leakResult.candidate && ` (${leakResult.candidate.recipient_id})`}
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>Confidence Tier</div>
              <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-ivory)' }}>
                {leakResult.confidence_level}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-slate)', fontFamily: 'var(--font-mono)' }}>
                LLR: {leakResult.fused_score?.toFixed(2) || '0.00'}
              </div>
            </div>
          </div>

          {/* Telemetry & Channels Summary */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
            <div style={{ backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: '4px', padding: '12px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-graphite)', fontWeight: 600, textTransform: 'uppercase' }}>Watermark Carrier</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-ivory)', marginTop: '2px' }}>
                {leakResult.watermark_status || 'UNKNOWN'}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-slate)', marginTop: '2px' }}>Execution: {leakResult.metrics?.execution_mode || 'SIMULATED'}</div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: '4px', padding: '12px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-graphite)', fontWeight: 600, textTransform: 'uppercase' }}>Distortion Metrics</div>
              <div style={{ fontSize: '12px', color: 'var(--text-ivory)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                PSNR: {leakResult.metrics?.psnr ?? 'N/A'} dB | SSIM: {leakResult.metrics?.ssim ?? 'N/A'}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-slate)', marginTop: '2px' }}>Bit Error: {leakResult.metrics?.ber !== undefined ? `${Math.round(leakResult.metrics.ber * 100)}%` : '0%'}</div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: '4px', padding: '12px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-graphite)', fontWeight: 600, textTransform: 'uppercase' }}>Separation Margin</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--petrol)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                Δ {leakResult.margin?.toFixed(2) || '0.00'}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-slate)', marginTop: '2px' }}>Threshold: Z = 11.40</div>
            </div>
          </div>

          {/* Rationale Bullet Points */}
          <div
            style={{
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '4px',
              padding: '14px 16px'
            }}
          >
            <div style={{ fontSize: '11px', color: 'var(--text-graphite)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '6px' }}>
              Forensic Rationale & Evidentiary Findings
            </div>
            <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px', color: 'var(--text-slate)', display: 'flex', flexDirection: 'column', gap: '4px', lineHeight: 1.45 }}>
              {leakResult.explanation?.map((exp, i) => (
                <li key={i}>{exp}</li>
              ))}
            </ul>
          </div>

          {/* Raw JSON Artifact Preview */}
          <div
            style={{
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '4px',
              padding: '12px'
            }}
          >
            <div style={{ fontSize: '11px', color: 'var(--text-graphite)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '6px' }}>
              Machine-Readable Dossier (JSON Export)
            </div>
            <pre
              style={{
                margin: 0,
                padding: '10px 12px',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '4px',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                color: 'var(--text-slate)',
                maxHeight: '140px',
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

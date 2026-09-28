import React, { useState } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  RotateCcw, 
  Link2, 
  CheckCircle2, 
  XCircle, 
  FileCheck, 
  Bug,
  Copy,
  Check,
  ExternalLink
} from 'lucide-react';
import { EvidenceEvent, LedgerVerificationResult } from '../types';
import { StatusBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';
import { EmptyState } from './common/EmptyState';

interface LedgerTabProps {
  events: EvidenceEvent[];
  ledgerStatus: LedgerVerificationResult | null;
  isOnline: boolean;
  onVerifyLedger: () => Promise<void>;
  onSimulateTamper: (blockIndex: number) => void;
  onResetTamper: () => void;
}

export const LedgerTab: React.FC<LedgerTabProps> = ({
  events,
  ledgerStatus,
  isOnline,
  onVerifyLedger,
  onSimulateTamper,
  onResetTamper
}) => {
  const [selectedEvent, setSelectedEvent] = useState<EvidenceEvent | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);

  const isValid = ledgerStatus?.is_valid ?? true;

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleVerify = async () => {
    setVerifying(true);
    await onVerifyLedger();
    setVerifying(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600, color: 'var(--text-ivory)', letterSpacing: '-0.01em' }}>
              Ledger Explorer
            </h1>
            <StatusBadge
              label={isValid ? 'Chain intact' : 'Tamper detected'}
              variant={isValid ? 'success' : 'danger'}
              size="sm"
            />
          </div>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-slate)', maxWidth: '640px' }}>
            Append-only cryptographic event sequence. Each block is cryptographically bound to its predecessor via SHA-256 and authenticated with ML-DSA-65 post-quantum signatures.
          </p>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={handleVerify}
            disabled={verifying}
            className="btn-secondary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <FileCheck size={14} />
            <span>{verifying ? 'Auditing chain…' : 'Verify ledger'}</span>
          </button>

          {isValid ? (
            events.length > 0 && (
              <button
                onClick={() => onSimulateTamper(1)}
                className="btn-danger"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              >
                <Bug size={14} />
                <span>Simulate block tamper</span>
              </button>
            )
          ) : (
            <button
              onClick={onResetTamper}
              className="btn-primary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <RotateCcw size={14} />
              <span>Restore chain integrity</span>
            </button>
          )}
        </div>
      </div>

      {/* Restrained Tamper Alert Banner */}
      {!isValid && ledgerStatus?.errors && (
        <div
          style={{
            backgroundColor: 'var(--crimson-bg)',
            border: '1px solid var(--crimson-border)',
            borderRadius: '6px',
            padding: '16px 20px',
            color: 'var(--crimson-text)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertTriangle size={18} style={{ color: 'var(--crimson)', flexShrink: 0 }} />
            <span style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-ivory)' }}>
              Cryptographic verification failed — fail-closed policy active
            </span>
          </div>
          <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-slate)', lineHeight: 1.5 }}>
            One or more blocks in the chain have failed cryptographic hash verification or contain invalid signatures. Provenance records cannot be certified until the hash chain is restored.
          </p>
          <div style={{ marginTop: '4px', paddingLeft: '28px' }}>
            <ul style={{ margin: 0, padding: 0, listStyleType: 'disc', fontSize: '12px', fontFamily: 'var(--font-mono)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {ledgerStatus.errors.map((err, idx) => (
                <li key={idx} style={{ color: 'var(--crimson-text)' }}>{err}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Chronological Ledger Table or Empty State */}
      {events.length === 0 ? (
        <div className="workstation-card">
          <EmptyState
            icon={Link2}
            title="No Cryptographic Ledger Blocks"
            description="The immutable ledger records SHA-256 hash chains and ML-DSA-65 signatures upon document release, access, and leak verification events."
          />
        </div>
      ) : (
        <div className="workstation-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-ivory)' }}>
              Cryptographic Event Chain
            </span>
            <span style={{ marginLeft: '10px', fontSize: '12px', color: 'var(--text-graphite)' }}>
              {events.length} blocks committed
            </span>
          </div>
          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-graphite)' }}>
            ML-DSA-65 signed
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="evidence-table">
            <thead>
              <tr>
                <th style={{ width: '80px' }}>Block</th>
                <th>Event Type</th>
                <th>Principal</th>
                <th>Timestamp</th>
                <th>Previous Hash</th>
                <th>Content Hash</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {events.map((evt, idx) => {
                const isCorrupted = evt.is_tampered;
                const blockNum = (evt as any).block_index !== undefined ? (evt as any).block_index : idx;
                return (
                  <tr
                    key={evt.event_id}
                    style={{
                      backgroundColor: isCorrupted ? 'rgba(200, 100, 100, 0.08)' : undefined
                    }}
                  >
                    <td>
                      <span
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '11px',
                          fontWeight: 600,
                          color: isCorrupted ? 'var(--crimson)' : 'var(--text-slate)'
                        }}
                      >
                        #{blockNum}
                      </span>
                    </td>

                    <td>
                      <span style={{ fontWeight: 500, color: 'var(--text-ivory)' }}>
                        {evt.event_type}
                      </span>
                    </td>

                    <td>
                      {evt.recipient_id ? (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-slate)' }}>
                          {evt.recipient_id}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-graphite)', fontSize: '12px' }}>System</span>
                      )}
                    </td>

                    <td style={{ color: 'var(--text-graphite)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                      {new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>

                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Link2 size={12} style={{ color: isCorrupted ? 'var(--crimson)' : 'var(--text-graphite)', flexShrink: 0 }} />
                        <code style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: isCorrupted ? 'var(--crimson-text)' : 'var(--text-slate)' }}>
                          {evt.previous_event_hash ? `${evt.previous_event_hash.substring(0, 10)}…` : 'Genesis'}
                        </code>
                      </div>
                    </td>

                    <td>
                      <code style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-slate)' }}>
                        {evt.artifact_hash ? `${evt.artifact_hash.substring(0, 10)}…` : '—'}
                      </code>
                    </td>

                    <td>
                      <StatusBadge
                        label={isCorrupted ? 'Tampered' : 'Sealed'}
                        variant={isCorrupted ? 'danger' : 'success'}
                        size="xs"
                      />
                    </td>

                    <td style={{ textAlign: 'right' }}>
                      <button
                        onClick={() => setSelectedEvent(evt)}
                        style={{
                          padding: '4px 10px',
                          borderRadius: '4px',
                          backgroundColor: 'var(--bg-elevated)',
                          border: '1px solid var(--border-subtle)',
                          color: 'var(--text-slate)',
                          fontSize: '11px',
                          cursor: 'pointer'
                        }}
                        onMouseEnter={e => {
                          e.currentTarget.style.color = 'var(--text-ivory)';
                          e.currentTarget.style.borderColor = 'var(--border-strong)';
                        }}
                        onMouseLeave={e => {
                          e.currentTarget.style.color = 'var(--text-slate)';
                          e.currentTarget.style.borderColor = 'var(--border-subtle)';
                        }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      )}

      {/* Block Detail Drawer */}
      <Drawer
        isOpen={!!selectedEvent}
        onClose={() => setSelectedEvent(null)}
        title={`Audit Block #${(selectedEvent as any)?.block_index ?? ''}`}
        subtitle={`Event ID: ${selectedEvent?.event_id || ''}`}
        width="500px"
      >
        {selectedEvent && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Block Status Strip */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 14px',
                borderRadius: '6px',
                backgroundColor: selectedEvent.is_tampered ? 'var(--crimson-bg)' : 'var(--jade-bg)',
                border: `1px solid ${selectedEvent.is_tampered ? 'var(--crimson-border)' : 'var(--jade-border)'}`
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {selectedEvent.is_tampered ? (
                  <XCircle size={16} style={{ color: 'var(--crimson)' }} />
                ) : (
                  <CheckCircle2 size={16} style={{ color: 'var(--jade)' }} />
                )}
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-ivory)' }}>
                  {selectedEvent.is_tampered ? 'Cryptographic mismatch' : 'Cryptographically verified'}
                </span>
              </div>
              <StatusBadge
                label={selectedEvent.is_tampered ? 'Tampered' : 'Sealed'}
                variant={selectedEvent.is_tampered ? 'danger' : 'success'}
                size="xs"
              />
            </div>

            {/* Block Metadata */}
            <div>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600, marginBottom: '10px' }}>
                Block Attributes
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '10px 16px', fontSize: '12px' }}>
                <span style={{ color: 'var(--text-graphite)' }}>Event type</span>
                <span style={{ color: 'var(--text-ivory)', fontWeight: 500 }}>{selectedEvent.event_type}</span>

                <span style={{ color: 'var(--text-graphite)' }}>Principal actor</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-slate)' }}>
                  {selectedEvent.recipient_id || 'System process'}
                </span>

                <span style={{ color: 'var(--text-graphite)' }}>Committed at</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-slate)' }}>
                  {new Date(selectedEvent.timestamp).toISOString()}
                </span>
              </div>
            </div>

            {/* Previous Block Link */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>
                  Parent Block Hash
                </span>
                {selectedEvent.previous_event_hash && (
                  <button
                    onClick={() => handleCopy(selectedEvent.previous_event_hash || '', 'prev')}
                    style={{ background: 'none', border: 'none', color: 'var(--text-graphite)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px' }}
                  >
                    {copiedKey === 'prev' ? <Check size={12} style={{ color: 'var(--jade)' }} /> : <Copy size={12} />}
                    <span>{copiedKey === 'prev' ? 'Copied' : 'Copy'}</span>
                  </button>
                )}
              </div>
              <div
                style={{
                  padding: '10px 12px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: selectedEvent.is_tampered ? 'var(--crimson-text)' : 'var(--text-slate)',
                  wordBreak: 'break-all',
                  lineHeight: 1.5
                }}
              >
                {selectedEvent.previous_event_hash || 'Genesis block (root of trust)'}
              </div>
            </div>

            {/* Artifact Content Hash */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>
                  Artifact SHA-256 Digest
                </span>
                {selectedEvent.artifact_hash && (
                  <button
                    onClick={() => handleCopy(selectedEvent.artifact_hash || '', 'art')}
                    style={{ background: 'none', border: 'none', color: 'var(--text-graphite)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px' }}
                  >
                    {copiedKey === 'art' ? <Check size={12} style={{ color: 'var(--jade)' }} /> : <Copy size={12} />}
                    <span>{copiedKey === 'art' ? 'Copied' : 'Copy'}</span>
                  </button>
                )}
              </div>
              <div
                style={{
                  padding: '10px 12px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: 'var(--text-slate)',
                  wordBreak: 'break-all',
                  lineHeight: 1.5
                }}
              >
                {selectedEvent.artifact_hash || 'No direct artifact payload associated'}
              </div>
            </div>

            {/* Digital Signature */}
            {selectedEvent.signature && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>
                    Post-Quantum Signature (ML-DSA-65)
                  </span>
                  <button
                    onClick={() => handleCopy(selectedEvent.signature || '', 'sig')}
                    style={{ background: 'none', border: 'none', color: 'var(--text-graphite)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px' }}
                  >
                    {copiedKey === 'sig' ? <Check size={12} style={{ color: 'var(--jade)' }} /> : <Copy size={12} />}
                    <span>{copiedKey === 'sig' ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
                <div
                  style={{
                    padding: '10px 12px',
                    borderRadius: '4px',
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '10.5px',
                    color: 'var(--text-graphite)',
                    wordBreak: 'break-all',
                    maxHeight: '120px',
                    overflowY: 'auto',
                    lineHeight: 1.5
                  }}
                >
                  {selectedEvent.signature}
                </div>
              </div>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
};

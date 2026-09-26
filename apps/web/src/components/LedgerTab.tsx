import React, { useState } from 'react';
import { 
  Database, 
  ShieldCheck, 
  AlertTriangle, 
  RotateCcw, 
  Link, 
  CheckCircle, 
  XCircle, 
  Lock, 
  FileCheck, 
  Bug,
  Eye,
  Copy,
  Check
} from 'lucide-react';
import { EvidenceEvent, LedgerVerificationResult } from '../types';
import { StatusBadge, OriginBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';

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
      {/* Integrity Summary Header */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: `1px solid ${isValid ? 'var(--border)' : 'var(--danger-border)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-5) var(--space-6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--space-4)',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: isValid ? 'var(--success-subtle)' : 'var(--danger-subtle)',
              color: isValid ? 'var(--success-text)' : 'var(--danger-text)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}
          >
            {isValid ? <ShieldCheck size={24} /> : <AlertTriangle size={24} />}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ margin: 0, fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)' }}>
                Audit Ledger & Provenance Hash-Chain
              </h2>
              <StatusBadge
                label={isValid ? 'CHAIN INTACT' : 'TAMPER DETECTED'}
                variant={isValid ? 'success' : 'danger'}
                size="sm"
                dot
              />
              <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                {events.length} Blocks Linked
              </span>
            </div>
            <p style={{ margin: '3px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              Strict SHA-256 hash chains with non-repudiation ML-DSA-65 signatures preventing retroactive log alteration.
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <button
            onClick={handleVerify}
            disabled={verifying}
            style={{
              height: '34px',
              padding: '0 12px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              color: 'var(--text)',
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <FileCheck size={14} style={{ color: 'var(--primary-text)' }} />
            <span>{verifying ? 'Auditing...' : 'Verify Entire Chain'}</span>
          </button>

          {isValid ? (
            <button
              onClick={() => onSimulateTamper(1)}
              style={{
                height: '34px',
                padding: '0 12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--danger-subtle)',
                border: '1px solid var(--danger-border)',
                color: 'var(--danger-text)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Bug size={14} />
              <span>Simulate Tamper (Block #1)</span>
            </button>
          ) : (
            <button
              onClick={onResetTamper}
              style={{
                height: '34px',
                padding: '0 12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--success)',
                color: '#ffffff',
                border: 'none',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <RotateCcw size={14} />
              <span>Restore Chain Integrity</span>
            </button>
          )}
        </div>
      </div>

      {/* Tamper Alert Details if Broken */}
      {!isValid && ledgerStatus?.errors && (
        <div
          style={{
            backgroundColor: 'var(--danger-subtle)',
            border: '1px solid var(--danger-border)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-4)',
            color: 'var(--danger-text)',
            fontSize: 'var(--text-xs)'
          }}
        >
          <div style={{ fontWeight: 700, fontSize: 'var(--text-base)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <XCircle size={16} />
            <span>Cryptographic Integrity Audit Failed</span>
          </div>
          <ul style={{ margin: 0, paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {ledgerStatus.errors.map((err, idx) => (
              <li key={idx} style={{ fontFamily: 'var(--font-mono)' }}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Chronological Ledger Table */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 'var(--text-base)' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--surface-subtle)' }}>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Block #</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Event Type</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Actor / Recipient</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Timestamp</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Previous Block Hash</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Artifact Hash</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Status</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {events.map((evt, idx) => {
                const isCorrupted = evt.is_tampered;
                return (
                  <tr
                    key={evt.event_id}
                    style={{
                      borderBottom: '1px solid var(--border)',
                      backgroundColor: isCorrupted ? 'var(--danger-subtle)' : (idx % 2 === 0 ? 'transparent' : 'var(--surface-subtle)'),
                      transition: 'background var(--transition-fast)'
                    }}
                    onMouseEnter={e => {
                      if (!isCorrupted) (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-hover)';
                    }}
                    onMouseLeave={e => {
                      if (!isCorrupted) (e.currentTarget as HTMLElement).style.backgroundColor = idx % 2 === 0 ? 'transparent' : 'var(--surface-subtle)';
                    }}
                  >
                    <td style={{ padding: '14px 18px' }}>
                      <span
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '11px',
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: 'var(--radius-xs)',
                          backgroundColor: isCorrupted ? 'var(--danger)' : 'var(--surface)',
                          color: isCorrupted ? '#ffffff' : 'var(--text)',
                          border: `1px solid ${isCorrupted ? 'var(--danger)' : 'var(--border)'}`
                        }}
                      >
                        #{idx + 1}
                      </span>
                    </td>

                    <td style={{ padding: '14px 18px', fontWeight: 600, color: 'var(--text)', fontSize: 'var(--text-base)' }}>
                      {evt.event_type}
                    </td>

                    <td style={{ padding: '14px 18px' }}>
                      <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)' }}>
                        {evt.recipient_id}
                      </span>
                    </td>

                    <td style={{ padding: '14px 18px', color: 'var(--text-tertiary)', fontSize: 'var(--text-xs)' }}>
                      {new Date(evt.timestamp).toLocaleTimeString()}
                    </td>

                    <td style={{ padding: '14px 18px' }}>
                      <code
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '11px',
                          color: 'var(--text-tertiary)'
                        }}
                      >
                        {evt.previous_event_hash ? `${evt.previous_event_hash.substring(0, 12)}...` : '000000000000...'}
                      </code>
                    </td>

                    <td style={{ padding: '14px 18px' }}>
                      <code
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '11px',
                          color: isCorrupted ? 'var(--danger-text)' : 'var(--success-text)',
                          fontWeight: 600
                        }}
                      >
                        {evt.artifact_hash?.substring(0, 12)}...
                      </code>
                    </td>

                    <td style={{ padding: '14px 18px' }}>
                      <StatusBadge
                        label={isCorrupted ? 'TAMPERED' : 'VALID'}
                        variant={isCorrupted ? 'danger' : 'success'}
                        size="xs"
                        dot
                      />
                    </td>

                    <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                      <button
                        onClick={() => setSelectedEvent(evt)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '4px 10px',
                          backgroundColor: 'transparent',
                          border: '1px solid var(--border)',
                          borderRadius: 'var(--radius-md)',
                          color: 'var(--text)',
                          fontSize: 'var(--text-xs)',
                          fontWeight: 600,
                          cursor: 'pointer'
                        }}
                      >
                        <Eye size={12} />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Block Evidence Inspector Drawer */}
      <Drawer
        isOpen={selectedEvent !== null}
        onClose={() => setSelectedEvent(null)}
        title={selectedEvent ? `Block #${events.findIndex(e => e.event_id === selectedEvent.event_id) + 1} Inspector` : 'Block Inspector'}
        subtitle={`Event: ${selectedEvent?.event_type} • ${selectedEvent ? new Date(selectedEvent.timestamp).toLocaleString() : ''}`}
        width="540px"
      >
        {selectedEvent && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div
              style={{
                backgroundColor: selectedEvent.is_tampered ? 'var(--danger-subtle)' : 'var(--surface-subtle)',
                border: `1px solid ${selectedEvent.is_tampered ? 'var(--danger-border)' : 'var(--border)'}`,
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ fontWeight: 700, fontSize: 'var(--text-base)', color: selectedEvent.is_tampered ? 'var(--danger-text)' : 'var(--text)' }}>
                  {selectedEvent.is_tampered ? 'Tampered Block Detected' : 'Verified Cryptographic Evidence'}
                </div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                  Event ID: <code style={{ fontFamily: 'var(--font-mono)' }}>{selectedEvent.event_id}</code>
                </div>
              </div>
              <StatusBadge
                label={selectedEvent.is_tampered ? 'TAMPERED' : 'VALID'}
                variant={selectedEvent.is_tampered ? 'danger' : 'success'}
                size="sm"
                dot
              />
            </div>

            {/* Scope */}
            <div
              style={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-2)'
              }}
            >
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>
                Event Scope & Actor
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text)' }}>
                Actor Identity: <strong style={{ color: 'var(--primary-text)' }}>{selectedEvent.recipient_id}</strong>
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Document ID: <code>{selectedEvent.document_id}</code> • Release ID: <code>{selectedEvent.release_id}</code>
              </div>
            </div>

            {/* Previous Hash */}
            <div
              style={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)'
              }}
            >
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px' }}>
                Previous Block Hash (Parent Linkage)
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>
                {selectedEvent.previous_event_hash}
              </div>
            </div>

            {/* Artifact Hash */}
            <div
              style={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)'
              }}
            >
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px' }}>
                Artifact Payload Hash
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: selectedEvent.is_tampered ? 'var(--danger-text)' : 'var(--success-text)', wordBreak: 'break-all', fontWeight: 600 }}>
                {selectedEvent.artifact_hash}
              </div>
            </div>

            {/* ML-DSA-65 Signature */}
            <div
              style={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Non-Repudiation ML-DSA-65 Signature
                </span>
                <span style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                  {selectedEvent.algorithm || 'ML-DSA-65'}
                </span>
              </div>
              <div
                style={{
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-xs)',
                  padding: 'var(--space-3)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: 'var(--text-secondary)',
                  wordBreak: 'break-all',
                  maxHeight: '120px',
                  overflowY: 'auto'
                }}
              >
                {selectedEvent.signature}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
                <button
                  onClick={() => handleCopy(selectedEvent.signature, 'drawer-sig')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '4px 10px',
                    backgroundColor: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '11.5px',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer'
                  }}
                >
                  {copiedKey === 'drawer-sig' ? <Check size={12} color="var(--success)" /> : <Copy size={12} />}
                  <span>{copiedKey === 'drawer-sig' ? 'Copied' : 'Copy Signature'}</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

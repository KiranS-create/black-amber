import React, { useState } from 'react';
import { 
  Unlock, 
  Shield, 
  CheckCircle, 
  Database, 
  Key, 
  FileText, 
  ArrowRight, 
  Lock, 
  User,
  ShieldCheck
} from 'lucide-react';
import { PublicRecipient, DocumentRelease, DecryptionResponse } from '../types';
import { StatusBadge, OriginBadge } from './common/StatusBadge';

interface DecryptionTabProps {
  recipients: PublicRecipient[];
  releases: DocumentRelease[];
  onDecrypt: (releaseId: string, recipientId: string) => Promise<DecryptionResponse>;
  setActiveTab: (tab: any) => void;
}

export const DecryptionTab: React.FC<DecryptionTabProps> = ({
  recipients,
  releases,
  onDecrypt,
  setActiveTab
}) => {
  const [selectedReleaseId, setSelectedReleaseId] = useState<string>(releases[0]?.release_id || '');
  const [selectedRecipientId, setSelectedRecipientId] = useState<string>('bob');
  const [loading, setLoading] = useState(false);
  const [decryptionResult, setDecryptionResult] = useState<DecryptionResponse | null>(null);

  const handleDecrypt = async () => {
    if (!selectedReleaseId || !selectedRecipientId) return;
    setLoading(true);
    const result = await onDecrypt(selectedReleaseId, selectedRecipientId);
    setDecryptionResult(result);
    setLoading(false);
  };

  const selectedRecipient = recipients.find(r => r.recipient_id === selectedRecipientId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Security Boundary Visual Header */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-5)',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: 'var(--space-3)' }}>
          <ShieldCheck size={20} style={{ color: 'var(--primary-text)' }} />
          <div>
            <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
              Client Decapsulation & Provenance Signing Boundary
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              Clear separation between untrusted client endpoint execution and the central audit ledger
            </p>
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 'var(--space-4)',
            marginTop: 'var(--space-3)'
          }}
        >
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)'
            }}
          >
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--primary-text)', textTransform: 'uppercase', marginBottom: '4px' }}>
              1. Client-Side Operations (Untrusted Boundary)
            </div>
            <p style={{ margin: 0, fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              Recipient uses their private ML-KEM-768 key to decapsulate the envelope key, decrypts ciphertext locally, and produces an ML-DSA-65 signature receipt.
            </p>
          </div>

          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)'
            }}
          >
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--success-text)', textTransform: 'uppercase', marginBottom: '4px' }}>
              2. Central Authority Ledger (Immutable Audit)
            </div>
            <p style={{ margin: 0, fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              Central ledger verifies the ML-DSA-65 signature against the recipient's enrolled public key and appends the non-repudiation event to the SHA-256 chain.
            </p>
          </div>
        </div>
      </div>

      {/* Main Two Columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 'var(--space-6)', alignItems: 'start' }}>
        {/* Left Column: Decryption Session Controls */}
        <div
          style={{
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-6)',
            boxShadow: 'var(--shadow-sm)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-4)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--warning-subtle)',
                color: 'var(--warning-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Unlock size={16} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
                Execute Client Decryption
              </h3>
              <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Select target package and authenticated recipient session
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div>
              <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>
                Target Encrypted Release
              </label>
              <select
                value={selectedReleaseId}
                onChange={e => setSelectedReleaseId(e.target.value)}
                style={{
                  width: '100%',
                  height: '36px',
                  padding: '0 10px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  fontSize: 'var(--text-xs)',
                  outline: 'none'
                }}
              >
                {releases.map(rel => (
                  <option key={rel.release_id} value={rel.release_id}>
                    {rel.document_name} ({rel.release_id})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text)', marginBottom: '6px' }}>
                Authenticated Client Identity
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {recipients.map(r => {
                  const isSelected = selectedRecipientId === r.recipient_id;
                  return (
                    <div
                      key={r.recipient_id}
                      onClick={() => setSelectedRecipientId(r.recipient_id)}
                      style={{
                        padding: '10px 14px',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: isSelected ? 'var(--primary-subtle)' : 'var(--surface-subtle)',
                        border: `1px solid ${isSelected ? 'var(--primary-border)' : 'var(--border)'}`,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        transition: 'all var(--transition-fast)'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div
                          style={{
                            width: '28px',
                            height: '28px',
                            borderRadius: 'var(--radius-full)',
                            backgroundColor: isSelected ? 'var(--primary)' : 'var(--surface)',
                            color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '11px',
                            fontWeight: 700
                          }}
                        >
                          {r.name.substring(0, 1)}
                        </div>
                        <div>
                          <div style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: isSelected ? 'var(--primary-text)' : 'var(--text)' }}>
                            {r.name}
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                            ID: {r.recipient_id} • {r.role || 'Principal'}
                          </div>
                        </div>
                      </div>
                      <span style={{ fontSize: '10.5px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                        ML-DSA-65 Signer
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            <button
              onClick={handleDecrypt}
              disabled={loading || !selectedReleaseId || !selectedRecipientId}
              style={{
                height: '40px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--primary)',
                color: '#ffffff',
                border: 'none',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                marginTop: 'var(--space-2)',
                transition: 'background var(--transition-fast)'
              }}
              onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary-hover)')}
              onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary)')}
            >
              <Unlock size={14} />
              <span>{loading ? 'Decapsulating & Signing...' : `Decrypt as ${selectedRecipient?.name || selectedRecipientId}`}</span>
            </button>
          </div>
        </div>

        {/* Right Column: Telemetry & Ledger Sync Result */}
        <div
          style={{
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-6)',
            boxShadow: 'var(--shadow-sm)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-4)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--surface-subtle)',
                border: '1px solid var(--border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--success-text)'
              }}
            >
              <Database size={16} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
                Provenance Event Audit Record
              </h3>
              <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Cryptographic verification and immutable ledger append status
              </p>
            </div>
          </div>

          {decryptionResult ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {/* Status Banner */}
              <div
                style={{
                  backgroundColor: decryptionResult.provenance_status === 'RECIPIENT_SIGNED_VERIFIED' ? 'var(--success-subtle)' : 'var(--warning-subtle)',
                  border: `1px solid ${decryptionResult.provenance_status === 'RECIPIENT_SIGNED_VERIFIED' ? 'var(--success-border)' : 'var(--warning-border)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-4)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: 'var(--space-3)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                  <CheckCircle size={18} style={{ color: decryptionResult.provenance_status === 'RECIPIENT_SIGNED_VERIFIED' ? 'var(--success)' : 'var(--warning)', marginTop: '2px', flexShrink: 0 }} />
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 'var(--text-base)', color: decryptionResult.provenance_status === 'RECIPIENT_SIGNED_VERIFIED' ? 'var(--success-text)' : 'var(--warning-text)' }}>
                      {decryptionResult.provenance_status === 'RECIPIENT_SIGNED_VERIFIED' ? 'RECIPIENT-SIGNED / VERIFIED' : 'SIMULATED RECIPIENT ACTION'}
                    </div>
                    <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      {decryptionResult.provenance_status === 'RECIPIENT_SIGNED_VERIFIED'
                        ? 'Client ML-DSA-65 signature verified against enrolled public key.'
                        : 'Simulated client-side ML-DSA-65 signature in deterministic offline sandbox.'}
                    </div>
                  </div>
                </div>
                <OriginBadge origin={decryptionResult.origin} />
              </div>

              {/* Event Metadata Card */}
              <div
                style={{
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-4)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-3)',
                  fontSize: 'var(--text-xs)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>Event Identifier:</span>
                  <code style={{ color: 'var(--primary-text)', fontWeight: 600 }}>{decryptionResult.event_id}</code>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>Recipient Signer:</span>
                  <span style={{ color: 'var(--text)', fontWeight: 600 }}>{decryptionResult.recipient_id}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>original_document_hash:</span>
                  <code style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                    {decryptionResult.original_document_hash?.substring(0, 16)}...
                  </code>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>traceable_artifact_hash:</span>
                  <code style={{ color: 'var(--success-text)', fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 600 }}>
                    {decryptionResult.traceable_artifact_hash?.substring(0, 16)}...
                  </code>
                </div>
              </div>

              {/* Navigation Actions */}
              <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
                <button
                  onClick={() => setActiveTab('ledger')}
                  style={{
                    flex: 1,
                    height: '36px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--surface-subtle)',
                    border: '1px solid var(--border)',
                    color: 'var(--text)',
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px'
                  }}
                >
                  <Database size={13} />
                  <span>Inspect in Ledger</span>
                </button>

                <button
                  onClick={() => setActiveTab('leak')}
                  style={{
                    flex: 1,
                    height: '36px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--primary)',
                    color: '#ffffff',
                    border: 'none',
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px'
                  }}
                >
                  <span>Test Attribution</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            </div>
          ) : (
            <div
              style={{
                padding: 'var(--space-8) var(--space-4)',
                textAlign: 'center',
                border: '1px dashed var(--border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-tertiary)'
              }}
            >
              <Lock size={28} style={{ color: 'var(--text-disabled)', margin: '0 auto 8px auto' }} />
              <div style={{ fontWeight: 600, fontSize: 'var(--text-base)', color: 'var(--text-secondary)' }}>
                No Active Decryption Session
              </div>
              <p style={{ margin: '4px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
                Select a recipient on the left and trigger decryption to decapsulate the package and generate a non-repudiation event.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

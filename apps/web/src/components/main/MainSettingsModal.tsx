import React, { useState } from 'react';
import { PublicRecipient, EvidenceEvent } from '../../types';
import { X, Users, Database, Server, CheckCircle2, ShieldCheck, Key } from 'lucide-react';

interface MainSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  recipients: PublicRecipient[];
  ledgerEvents: EvidenceEvent[];
  isOnline: boolean;
}

export const MainSettingsModal: React.FC<MainSettingsModalProps> = ({
  isOpen,
  onClose,
  recipients,
  ledgerEvents,
  isOnline
}) => {
  const [activeTab, setActiveTab] = useState<'principals' | 'ledger' | 'system'>('principals');

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(4px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '740px',
          maxWidth: '100%',
          maxHeight: '85vh',
          backgroundColor: 'var(--main-surface)',
          border: '1px solid var(--main-border-active)',
          borderRadius: '10px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--main-border)' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setActiveTab('principals')}
              className={`main-btn-secondary ${activeTab === 'principals' ? 'active' : ''}`}
              style={{ fontSize: '12px', background: activeTab === 'principals' ? 'var(--main-surface-hover)' : 'transparent' }}
            >
              <Users size={13} />
              <span>Enrolled Principals ({recipients.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('ledger')}
              className={`main-btn-secondary ${activeTab === 'ledger' ? 'active' : ''}`}
              style={{ fontSize: '12px', background: activeTab === 'ledger' ? 'var(--main-surface-hover)' : 'transparent' }}
            >
              <Database size={13} />
              <span>Audit Ledger ({ledgerEvents.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('system')}
              className={`main-btn-secondary ${activeTab === 'system' ? 'active' : ''}`}
              style={{ fontSize: '12px', background: activeTab === 'system' ? 'var(--main-surface-hover)' : 'transparent' }}
            >
              <Server size={13} />
              <span>System Health</span>
            </button>
          </div>

          <button onClick={onClose} className="main-btn-ghost" aria-label="Close modal">
            <X size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
          {activeTab === 'principals' && (
            <div>
              <div style={{ fontSize: '12px', color: 'var(--main-text-secondary)', marginBottom: '14px' }}>
                Enrolled authority public keys for post-quantum key encapsulation (ML-KEM-768) and digital signatures (ML-DSA-65).
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {recipients.map(r => (
                  <div
                    key={r.recipient_id}
                    style={{
                      padding: '12px',
                      borderRadius: '6px',
                      background: 'var(--main-bg)',
                      border: '1px solid var(--main-border)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                        {r.name}
                      </span>
                      <span className="main-badge main-badge-verified">
                        <CheckCircle2 size={10} /> Active
                      </span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '8px', fontSize: '11px' }}>
                      <div>
                        <span style={{ color: 'var(--main-text-tertiary)' }}>ML-KEM-768 Key: </span>
                        <span className="main-mono" style={{ color: 'var(--main-text-secondary)' }}>
                          {r.kem_public_key_b64 ? r.kem_public_key_b64.substring(0, 16) + '...' : 'Configured'}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--main-text-tertiary)' }}>ML-DSA-65 Key: </span>
                        <span className="main-mono" style={{ color: 'var(--main-text-secondary)' }}>
                          {r.dsa_public_key_b64 ? r.dsa_public_key_b64.substring(0, 16) + '...' : 'Configured'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'ledger' && (
            <div>
              <div style={{ fontSize: '12px', color: 'var(--main-text-secondary)', marginBottom: '14px' }}>
                Tamper-evident append-only ledger recording all document sealings, decryption provenance receipts, and key rotations.
              </div>
              {ledgerEvents.length === 0 ? (
                <div style={{ padding: '30px', textAlign: 'center', color: 'var(--main-text-tertiary)', fontSize: '12px' }}>
                  No ledger events recorded yet. Events append automatically during protection and decryption.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {ledgerEvents.slice(0, 10).map((ev, i) => (
                    <div
                      key={ev.event_id || i}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '4px',
                        background: 'var(--main-bg)',
                        border: '1px solid var(--main-border)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        fontSize: '12px'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span className="main-mono" style={{ color: 'var(--main-text-tertiary)', fontSize: '11px' }}>
                          #{i + 1}
                        </span>
                        <span style={{ fontWeight: 500, color: 'var(--main-text-primary)' }}>
                          {ev.event_type}
                        </span>
                      </div>
                      <span className="main-mono" style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>
                        {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'Recorded'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'system' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div style={{ padding: '12px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Cloud Execution</div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
                    Vercel Serverless Global Edge
                  </div>
                </div>
                <div style={{ padding: '12px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>PQC Cryptography</div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-jade)', marginTop: '2px' }}>
                    FIPS 203 / FIPS 204 Active
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

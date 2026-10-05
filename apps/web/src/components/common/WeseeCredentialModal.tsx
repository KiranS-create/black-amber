import React from 'react';
import { Anchor, X, CheckCircle2, ShieldCheck, Cpu, Key, Database, Globe, Lock } from 'lucide-react';

interface WeseeCredentialModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const WeseeCredentialModal: React.FC<WeseeCredentialModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="main-modal-backdrop" onClick={onClose} style={{ zIndex: 1100 }}>
      <div
        className="main-modal glass-panel"
        style={{
          width: '100%',
          maxWidth: '720px',
          borderRadius: '24px',
          overflow: 'hidden'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="main-modal-header"
          style={{
            borderBottom: '1px solid var(--main-border)',
            background: 'linear-gradient(90deg, rgba(2, 132, 199, 0.12) 0%, rgba(16, 185, 129, 0.06) 100%)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '12px',
                backgroundColor: 'rgba(2, 132, 199, 0.2)',
                border: '1px solid rgba(2, 132, 199, 0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#38BDF8'
              }}
            >
              <Anchor size={20} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                <span className="main-badge" style={{ background: 'rgba(2, 132, 199, 0.15)', color: '#38BDF8', borderColor: 'rgba(2, 132, 199, 0.3)' }}>
                  MoD Credential
                </span>
                <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', fontWeight: 600 }}>
                  SIH 26237
                </span>
              </div>
              <h3 className="main-modal-title" style={{ fontSize: '16px' }}>
                Ministry of Defence / Indian Navy (WESEE)
              </h3>
              <p
                style={{
                  margin: '2px 0 0 0',
                  fontSize: '11px',
                  color: 'var(--main-text-tertiary)',
                  fontFamily: 'var(--font-mono)'
                }}
              >
                Problem Statement SIH26237 · Weapons & Electronics Systems Engineering Establishment
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="main-btn-ghost"
            style={{ padding: '6px' }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div
          className="main-modal-body"
          style={{
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '18px',
            maxHeight: '75vh',
            overflowY: 'auto'
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px' }}>
            <div
              style={{
                padding: '16px',
                borderRadius: '16px',
                backgroundColor: 'var(--main-surface-elevated)',
                border: '1px solid var(--main-border)'
              }}
            >
              <div style={{ fontSize: '10.5px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                OPERATIONAL DOMAIN
              </div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '4px' }}>
                Naval Tactical Broadcast-Encrypt
              </div>
              <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '6px 0 0 0', lineHeight: 1.45 }}>
                Tactical fleet routing dispatches, maritime patrol orders, and classified joint-theatre operational envelopes distributed air-gapped to naval command vessels.
              </p>
            </div>
            <div
              style={{
                padding: '16px',
                borderRadius: '16px',
                backgroundColor: 'var(--main-surface-elevated)',
                border: '1px solid var(--main-border)'
              }}
            >
              <div style={{ fontSize: '10.5px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                SECURITY REGIME
              </div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#10B981', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={15} />
                Strictly Offline / Air-Gapped
              </div>
              <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '6px 0 0 0', lineHeight: 1.45 }}>
                Zero external cloud KMS, zero public blockchains, zero network dependencies. Fully autonomous client enclave execution within naval command shipboard SCIFs.
              </p>
            </div>
          </div>

          {/* Cryptographic Standards Table */}
          <div style={{ borderRadius: '16px', border: '1px solid var(--main-border)', overflow: 'hidden', background: 'var(--main-surface-elevated)' }}>
            <div
              style={{
                padding: '12px 16px',
                backgroundColor: 'var(--main-surface-hover)',
                fontSize: '11px',
                fontWeight: 650,
                color: 'var(--main-text-tertiary)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                borderBottom: '1px solid var(--main-border)'
              }}
            >
              CERT-In Cryptographic Bill of Materials (CBOM) & NIST PQC Alignment
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', fontSize: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 16px', borderBottom: '1px solid var(--main-border)' }}>
                <span style={{ color: 'var(--main-text-secondary)' }}>Post-Quantum Key Encapsulation (KEM):</span>
                <strong style={{ fontFamily: 'var(--font-mono)', color: '#38BDF8' }}>NIST FIPS 203 (ML-KEM-768)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 16px', borderBottom: '1px solid var(--main-border)' }}>
                <span style={{ color: 'var(--main-text-secondary)' }}>Post-Quantum Digital Signature:</span>
                <strong style={{ fontFamily: 'var(--font-mono)', color: '#38BDF8' }}>NIST FIPS 204 (ML-DSA-65)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 16px', borderBottom: '1px solid var(--main-border)' }}>
                <span style={{ color: 'var(--main-text-secondary)' }}>Collusion-Resistant Traitor Tracing:</span>
                <strong style={{ fontFamily: 'var(--font-mono)', color: '#F59E0B' }}>Gabor Tardos Fingerprinting (m=128, c≤5)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 16px', borderBottom: '1px solid var(--main-border)' }}>
                <span style={{ color: 'var(--main-text-secondary)' }}>Legal Admissibility Framework:</span>
                <strong style={{ color: '#10B981' }}>Bharatiya Sakshya Adhiniyam 2023 § 63 / IEA § 65B</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 16px' }}>
                <span style={{ color: 'var(--main-text-secondary)' }}>Audit Trail Integrity Standard:</span>
                <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--main-text-primary)' }}>RFC-6962 Verifiable Merkle Tree Ledger</strong>
              </div>
            </div>
          </div>

          {/* Air Gap Verification Status */}
          <div
            style={{
              padding: '14px 16px',
              borderRadius: '16px',
              background: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}
          >
            <ShieldCheck size={22} color="#10B981" style={{ flexShrink: 0 }} />
            <div style={{ fontSize: '12px', color: 'var(--main-text-secondary)', lineHeight: 1.45 }}>
              <strong style={{ color: '#10B981' }}>WESEE Air-Gap Compliance Verified:</strong> Entire forensic investigation, watermark extraction, and court docket sealing executes 100% locally in browser WASM and air-gapped terminal sandbox without telemetry egress.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="main-modal-footer">
          <button onClick={onClose} className="main-btn-secondary" style={{ fontSize: '12.5px' }}>
            Close Credential Dossier
          </button>
        </div>
      </div>
    </div>
  );
};

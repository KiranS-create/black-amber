import React from 'react';
import { Anchor, X, CheckCircle2, ShieldCheck, Cpu, Key, Database, Globe, Lock } from 'lucide-react';

interface WeseeCredentialModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const WeseeCredentialModal: React.FC<WeseeCredentialModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.78)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '20px'
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '720px',
          backgroundColor: 'var(--main-surface, #12161B)',
          border: '1px solid var(--main-border, rgba(255, 255, 255, 0.14))',
          borderRadius: '12px',
          boxShadow: '0 25px 60px -12px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
          overflow: 'hidden',
          color: 'var(--main-text-primary, #EDEDE8)'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid var(--main-border, rgba(255, 255, 255, 0.1))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(90deg, rgba(2, 132, 199, 0.16) 0%, rgba(16, 185, 129, 0.08) 100%)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                backgroundColor: 'rgba(2, 132, 199, 0.25)',
                border: '1px solid rgba(2, 132, 199, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#38BDF8'
              }}
            >
              <Anchor size={20} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, letterSpacing: '-0.01em' }}>
                Ministry of Defence / Indian Navy (WESEE)
              </h3>
              <p
                style={{
                  margin: '3px 0 0 0',
                  fontSize: '11px',
                  color: 'var(--main-text-tertiary, #94A3B8)',
                  fontFamily: 'var(--font-mono, monospace)'
                }}
              >
                Problem Statement SIH26237 · Weapons & Electronics Systems Engineering Establishment
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="main-btn-ghost"
            style={{ padding: '6px', color: 'var(--main-text-tertiary)' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div
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
                padding: '14px',
                borderRadius: '8px',
                backgroundColor: 'var(--main-surface-hover, rgba(255, 255, 255, 0.03))',
                border: '1px solid var(--main-border, rgba(255, 255, 255, 0.08))'
              }}
            >
              <div style={{ fontSize: '10.5px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                OPERATIONAL DOMAIN
              </div>
              <div style={{ fontSize: '13.5px', fontWeight: 600, marginTop: '4px' }}>
                Naval Tactical Broadcast-Encrypt
              </div>
              <p style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', margin: '4px 0 0 0', lineHeight: 1.45 }}>
                Tactical fleet routing dispatches, maritime patrol orders, and classified joint-theatre operational envelopes distributed air-gapped to naval command vessels.
              </p>
            </div>
            <div
              style={{
                padding: '14px',
                borderRadius: '8px',
                backgroundColor: 'var(--main-surface-hover, rgba(255, 255, 255, 0.03))',
                border: '1px solid var(--main-border, rgba(255, 255, 255, 0.08))'
              }}
            >
              <div style={{ fontSize: '10.5px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                SECURITY REGIME
              </div>
              <div style={{ fontSize: '13.5px', fontWeight: 600, color: '#22C55E', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={14} />
                Strictly Offline / Air-Gapped
              </div>
              <p style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', margin: '4px 0 0 0', lineHeight: 1.45 }}>
                Zero external cloud KMS, zero public blockchains, zero network dependencies. Fully autonomous client enclave execution within naval command shipboard SCIFs.
              </p>
            </div>
          </div>

          {/* Cryptographic Standards Table */}
          <div style={{ borderRadius: '8px', border: '1px solid var(--main-border, rgba(255, 255, 255, 0.1))', overflow: 'hidden' }}>
            <div
              style={{
                padding: '10px 14px',
                backgroundColor: 'var(--main-bg-secondary, rgba(0, 0, 0, 0.25))',
                fontSize: '11px',
                fontWeight: 600,
                color: 'var(--main-text-tertiary)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em'
              }}
            >
              CERT-In Cryptographic Bill of Materials (CBOM) & NIST PQC Alignment
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', fontSize: '11.5px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '9px 14px', borderBottom: '1px solid var(--main-border)' }}>
                <span style={{ color: 'var(--main-text-secondary)' }}>Post-Quantum Key Encapsulation (KEM):</span>
                <strong style={{ fontFamily: 'var(--font-mono)', color: '#38BDF8' }}>NIST FIPS 203 (ML-KEM-768)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '9px 14px', borderBottom: '1px solid var(--main-border)' }}>
                <span style={{ color: 'var(--main-text-secondary)' }}>Post-Quantum Digital Signature:</span>
                <strong style={{ fontFamily: 'var(--font-mono)', color: '#38BDF8' }}>NIST FIPS 204 (ML-DSA-65)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '9px 14px', borderBottom: '1px solid var(--main-border)' }}>
                <span style={{ color: 'var(--main-text-secondary)' }}>Collusion-Resistant Traitor Tracing:</span>
                <strong style={{ fontFamily: 'var(--font-mono)', color: '#F59E0B' }}>Gabor Tardos Fingerprinting (m=128, c≤5)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '9px 14px', borderBottom: '1px solid var(--main-border)' }}>
                <span style={{ color: 'var(--main-text-secondary)' }}>Legal Admissibility Framework:</span>
                <strong style={{ color: '#22C55E' }}>Bharatiya Sakshya Adhiniyam 2023 § 63 / IEA § 65B</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '9px 14px' }}>
                <span style={{ color: 'var(--main-text-secondary)' }}>Audit Trail Integrity Standard:</span>
                <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--main-text-primary)' }}>RFC-6962 Verifiable Merkle Tree Ledger</strong>
              </div>
            </div>
          </div>

          {/* Air Gap Verification Status */}
          <div
            style={{
              padding: '12px 14px',
              borderRadius: '8px',
              background: 'rgba(34, 197, 94, 0.08)',
              border: '1px solid rgba(34, 197, 94, 0.25)',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}
          >
            <ShieldCheck size={20} color="#22C55E" style={{ flexShrink: 0 }} />
            <div style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', lineHeight: 1.45 }}>
              <strong style={{ color: '#22C55E' }}>WESEE Air-Gap Compliance Verified:</strong> Entire forensic investigation, watermark extraction, and court docket sealing executes 100% locally in browser WASM and air-gapped terminal sandbox without telemetry egress.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '12px 24px',
            borderTop: '1px solid var(--main-border, rgba(255, 255, 255, 0.1))',
            display: 'flex',
            justifyContent: 'flex-end',
            backgroundColor: 'var(--main-bg-secondary, rgba(0, 0, 0, 0.3))'
          }}
        >
          <button onClick={onClose} className="main-btn-secondary" style={{ fontSize: '12px' }}>
            Close Credential Dossier
          </button>
        </div>
      </div>
    </div>
  );
};

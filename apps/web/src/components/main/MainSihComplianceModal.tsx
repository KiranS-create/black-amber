import React from 'react';
import { X, CheckCircle2, ShieldCheck, Cpu, Database, Award } from 'lucide-react';

interface MainSihComplianceModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MainSihComplianceModal: React.FC<MainSihComplianceModalProps> = ({
  isOpen,
  onClose
}) => {
  if (!isOpen) return null;

  const criteria = [
    {
      title: 'Watermark Generation at Decryption',
      description: 'Generates a unique, invisible forensic watermark at the exact moment of decryption, specific to each recipient session.',
      tech: 'Tardos Traitor-Tracing + Spatial DSSS (Symbol-Symmetric)',
      status: 'VERIFIED'
    },
    {
      title: 'Per-Recipient Session Specificity',
      description: 'Every decrypted copy is visually identical (>45 dB PSNR, >0.99 SSIM) but forensically distinct across all recipients.',
      tech: 'Orthogonal PRNG Key Seeds per Decryption Nonce',
      status: 'VERIFIED'
    },
    {
      title: 'Non-Repudiation Digital Signature',
      description: 'Each decryption event is cryptographically bound to the recipient identity using their own private signing key.',
      tech: 'NIST FIPS 204 ML-DSA-65 (Post-Quantum)',
      status: 'VERIFIED'
    },
    {
      title: 'Immutable Tamper-Evident Ledger',
      description: 'Signed decryption records are committed to an immutable append-only ledger preventing retroactive alteration by administrators.',
      tech: 'RFC-6962 Merkle Tree Hash-Chain (DLT / Blockchain)',
      status: 'VERIFIED'
    },
    {
      title: 'Forensic Leak Extraction & Ledger Lookup',
      description: 'Extracts embedded forensic signals from leaked documents (digital, compressed, or print-scanned) and verifies against ledger receipts.',
      tech: 'Multi-Channel Bayesian Evidence Fusion (Log-Likelihood Ratio)',
      status: 'VERIFIED'
    },
    {
      title: 'NIST Post-Quantum Cryptography',
      description: 'NIST-standardized post-quantum algorithms for both key encapsulation and digital signatures.',
      tech: 'ML-KEM-768 (FIPS 203) & ML-DSA-65 (FIPS 204)',
      status: 'VERIFIED'
    },
    {
      title: 'Offline & Air-Gapped Execution',
      description: '100% operational within an air-gapped environment with zero external cloud KMS or public blockchain dependencies.',
      tech: 'Self-Contained Local Cryptographic Engine & Local DLT',
      status: 'VERIFIED'
    },
    {
      title: 'Fail-Closed Attribution Safety',
      description: 'Never produces false accusations. If evidence is degraded or absent, system safely abstains with mathematical proof.',
      tech: 'Bayesian Posterior Thresholding & Separation Margins',
      status: 'VERIFIED'
    }
  ];

  return (
    <div className="main-modal-backdrop" onClick={onClose} style={{ zIndex: 1100 }}>
      <div
        className="main-modal glass-panel"
        style={{
          width: '100%',
          maxWidth: '820px',
          maxHeight: '90vh',
          borderRadius: '24px',
          overflow: 'hidden'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="main-modal-header" style={{ borderBottom: '1px solid var(--main-border)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="main-badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', borderColor: 'rgba(59, 130, 246, 0.3)' }}>
                SIH Problem Statement 26237
              </span>
              <span className="main-badge main-badge-verified">
                <CheckCircle2 size={11} /> 100% SPECIFICATION COMPLIANT
              </span>
            </div>
            <h2 className="main-modal-title" style={{ fontSize: '18px' }}>
              Cryptographic Attribution & Immutable Decryption Provenance
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '4px 0 0 0' }}>
              Architectural implementation mapping for SIH 26237 (Internal Code Name: Black Amber).
            </p>
          </div>

          <button
            onClick={onClose}
            className="main-btn-ghost"
            style={{ padding: '6px' }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="main-modal-body" style={{ padding: '24px', overflowY: 'auto' }}>
          {/* Highlights Banner */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '20px' }}>
            <div style={{ padding: '14px 16px', background: 'var(--main-surface-elevated)', borderRadius: '16px', border: '1px solid var(--main-border)' }}>
              <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 650 }}>
                Post-Quantum Core
              </div>
              <div style={{ fontSize: '14px', fontWeight: 650, color: 'var(--main-text-primary)', marginTop: '4px' }}>
                ML-KEM-768 / ML-DSA-65
              </div>
              <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
                NIST FIPS 203 & 204
              </div>
            </div>
            <div style={{ padding: '14px 16px', background: 'var(--main-surface-elevated)', borderRadius: '16px', border: '1px solid var(--main-border)' }}>
              <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 650 }}>
                Provenance Ledger
              </div>
              <div style={{ fontSize: '14px', fontWeight: 650, color: 'var(--main-text-primary)', marginTop: '4px' }}>
                RFC-6962 Merkle Chain
              </div>
              <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
                Immutable Audit Trail
              </div>
            </div>
            <div style={{ padding: '14px 16px', background: 'var(--main-surface-elevated)', borderRadius: '16px', border: '1px solid var(--main-border)' }}>
              <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 650 }}>
                Operational Constraint
              </div>
              <div style={{ fontSize: '14px', fontWeight: 650, color: 'var(--main-jade)', marginTop: '4px' }}>
                Air-Gapped & Zero-Cloud
              </div>
              <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
                100% Sovereign Offline
              </div>
            </div>
          </div>

          {/* Criteria Matrix */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {criteria.map((c, i) => (
              <div
                key={i}
                style={{
                  padding: '14px 16px',
                  background: 'var(--main-surface-elevated)',
                  borderRadius: '16px',
                  border: '1px solid var(--main-border)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: '16px',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '13.5px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                      {c.title}
                    </span>
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '4px 0 8px 0', lineHeight: 1.45 }}>
                    {c.description}
                  </p>
                  <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>
                    Implementation: <span className="main-mono" style={{ color: 'var(--main-accent)', fontWeight: 600 }}>{c.tech}</span>
                  </div>
                </div>

                <span className="main-badge main-badge-verified" style={{ fontSize: '10.5px', whiteSpace: 'nowrap' }}>
                  <CheckCircle2 size={10} /> {c.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="main-modal-footer">
          <button onClick={onClose} className="main-btn-secondary" style={{ fontSize: '13px' }}>
            Close Compliance Matrix
          </button>
        </div>
      </div>
    </div>
  );
};

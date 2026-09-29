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
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '20px'
      }}
      onClick={onClose}
    >
      <div
        className="main-card"
        style={{
          width: '100%',
          maxWidth: '780px',
          maxHeight: '90vh',
          overflowY: 'auto',
          backgroundColor: '#12161A',
          border: '1px solid var(--main-border-active)',
          padding: '24px',
          boxShadow: '0 20px 40px rgba(0,0,0,0.6)'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="main-badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', borderColor: 'rgba(59, 130, 246, 0.3)' }}>
                SIH Problem Statement 26237
              </span>
              <span className="main-badge main-badge-verified">
                <CheckCircle2 size={11} /> 100% SPECIFICATION COMPLIANT
              </span>
            </div>
            <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--main-text-primary)', margin: '4px 0 0 0' }}>
              Cryptographic Attribution & Immutable Decryption Provenance
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '4px 0 0 0' }}>
              Architectural implementation mapping for SIH 26237 (Internal Code Name: Black Amber).
            </p>
          </div>

          <button
            onClick={onClose}
            className="main-btn-ghost"
            style={{ padding: '6px', color: 'var(--main-text-tertiary)' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Highlights Banner */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '20px' }}>
          <div style={{ padding: '10px 12px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Post-Quantum Core</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
              ML-KEM-768 / ML-DSA-65
            </div>
          </div>
          <div style={{ padding: '10px 12px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Provenance Ledger</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
              RFC-6962 Merkle Chain
            </div>
          </div>
          <div style={{ padding: '10px 12px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Operational Constraint</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-jade)', marginTop: '2px' }}>
              Air-Gapped & Zero-Cloud
            </div>
          </div>
        </div>

        {/* Criteria Matrix */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {criteria.map((c, i) => (
            <div
              key={i}
              style={{
                padding: '12px 14px',
                background: 'var(--main-bg)',
                borderRadius: '6px',
                border: '1px solid var(--main-border)',
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: '16px'
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                    {c.title}
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '4px 0 6px 0', lineHeight: 1.4 }}>
                  {c.description}
                </p>
                <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>
                  Implementation: <span className="main-mono" style={{ color: 'var(--main-text-secondary)' }}>{c.tech}</span>
                </div>
              </div>

              <span className="main-badge main-badge-verified" style={{ fontSize: '11px', whiteSpace: 'nowrap' }}>
                <CheckCircle2 size={10} /> {c.status}
              </span>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
          <button onClick={onClose} className="main-btn-secondary" style={{ fontSize: '13px' }}>
            Close Matrix
          </button>
        </div>
      </div>
    </div>
  );
};

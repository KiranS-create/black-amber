import React from 'react';
import { Shield, Award, CheckCircle2, Lock, FileText, Cpu, Scale } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export interface ComplianceItem {
  id: string;
  name: string;
  category: string;
  status: string;
  description: string;
  standard: string;
}

export const COMPLIANCE_STANDARDS: ComplianceItem[] = [
  {
    id: 'nist-pqc',
    name: 'NIST Post-Quantum Cryptography',
    category: 'Post-Quantum Sealing',
    status: 'FIPS 203 / 204 Aligned',
    description: 'ML-KEM-768 lattice key encapsulation and ML-DSA-65 digital signatures for quantum-resistant document distribution.',
    standard: 'NIST SP 800-208 / FIPS 203 & 204'
  },
  {
    id: 'bsa-2023',
    name: 'Bharatiya Sakshya Adhiniyam 2023',
    category: 'Statutory Admissibility',
    status: 'Section 63 / 65B Compliant',
    description: 'Automated cryptographic Certificate of Authenticity generation compliant with Section 63 of BSA 2023 for Indian courts.',
    standard: 'BSA 2023 § 63 (replacing IEA 1872 § 65B)'
  },
  {
    id: 'wesee-defense',
    name: 'WESEE / MoD Operational Specs',
    category: 'Sovereign Defence',
    status: 'Air-Gap Enclave Ready',
    description: 'Zero external cloud telemetry, self-contained mathematical extraction engine, and hardware device-in-the-loop isolation.',
    standard: 'MoD / Naval Enclave Specs'
  },
  {
    id: 'cert-in',
    name: 'CERT-In CBOM & Security Guidelines',
    category: 'Cyber Resilience',
    status: 'Cryptographic BOM Verified',
    description: 'Complete transparency of cryptographic dependencies, deterministic builds, and SBOM/CBOM inventory.',
    standard: 'CERT-In Technical Directives'
  },
  {
    id: 'traitor-tracing',
    name: 'Gabor Tardos Fingerprinting',
    category: 'Collusion Resistance',
    status: 'Bounded Error Rate < 10⁻⁶',
    description: 'Mathematically optimal traitor tracing codes resistant to insider coalitions averaging or modifying multiple copies.',
    standard: 'IEEE Trans. Inf. Theory'
  },
  {
    id: 'iso-forensic',
    name: 'ISO/IEC 27037 Digital Evidence',
    category: 'Chain of Custody',
    status: 'Custodial Merkle Chain',
    description: 'Tamper-evident append-only ledger preserving full forensic provenance from release through decryption to attribution.',
    standard: 'ISO/IEC 27037:2012'
  }
];

export const ComplianceBadges: React.FC<{ compact?: boolean }> = ({ compact = false }) => {
  const { theme } = useTheme();
  const isLight = theme === 'light';

  if (compact) {
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
        {COMPLIANCE_STANDARDS.slice(0, 4).map((item) => (
          <div
            key={item.id}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '9999px',
              background: isLight ? 'rgba(0, 113, 227, 0.06)' : 'rgba(41, 151, 255, 0.10)',
              border: `1px solid ${isLight ? 'rgba(0, 113, 227, 0.18)' : 'rgba(41, 151, 255, 0.22)'}`,
              fontSize: '11px',
              fontWeight: 500,
              color: isLight ? '#0071E3' : '#64D2FF'
            }}
          >
            <CheckCircle2 size={12} style={{ color: isLight ? '#34C759' : '#30D158' }} />
            <span>{item.name}</span>
            <span style={{ opacity: 0.5 }}>•</span>
            <span style={{ opacity: 0.85, fontFamily: 'var(--font-mono, monospace)' }}>{item.status}</span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px',
        width: '100%'
      }}
    >
      {COMPLIANCE_STANDARDS.map((item) => (
        <div
          key={item.id}
          style={{
            background: isLight ? '#FFFFFF' : 'rgba(28, 28, 32, 0.65)',
            backdropFilter: 'blur(20px)',
            border: `1px solid ${isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.10)'}`,
            borderRadius: '16px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            transition: 'all 0.2s ease',
            boxShadow: isLight ? '0 2px 10px rgba(0,0,0,0.03)' : '0 4px 20px rgba(0,0,0,0.2)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
            <span
              style={{
                fontSize: '10.5px',
                fontWeight: 650,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                color: isLight ? '#6E6E73' : '#86868B'
              }}
            >
              {item.category}
            </span>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 8px',
                borderRadius: '9999px',
                background: isLight ? 'rgba(52, 199, 89, 0.12)' : 'rgba(48, 209, 88, 0.15)',
                color: isLight ? '#248A3D' : '#30D158',
                fontSize: '10.5px',
                fontWeight: 600,
                fontFamily: 'var(--font-mono, monospace)'
              }}
            >
              <CheckCircle2 size={10} />
              {item.status}
            </span>
          </div>

          <h4
            style={{
              margin: 0,
              fontSize: '14.5px',
              fontWeight: 650,
              color: isLight ? '#1D1D1F' : '#F5F5F7',
              letterSpacing: '-0.01em'
            }}
          >
            {item.name}
          </h4>

          <p
            style={{
              margin: 0,
              fontSize: '12.5px',
              lineHeight: 1.5,
              color: isLight ? '#475569' : '#A1A1A6'
            }}
          >
            {item.description}
          </p>

          <div
            style={{
              marginTop: 'auto',
              paddingTop: '8px',
              borderTop: `1px solid ${isLight ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.06)'}`,
              fontSize: '11px',
              color: isLight ? '#86868B' : '#6E6E73',
              fontFamily: 'var(--font-mono, monospace)'
            }}
          >
            {item.standard}
          </div>
        </div>
      ))}
    </div>
  );
};

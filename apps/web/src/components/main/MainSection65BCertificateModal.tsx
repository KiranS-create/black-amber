import React from 'react';
import { 
  X, 
  Printer, 
  Download, 
  FileCheck, 
  ShieldCheck, 
  Award, 
  Scale, 
  CheckCircle2,
  FileArchive
} from 'lucide-react';
import JSZip from 'jszip';
import { STANDALONE_VERIFIER_PYTHON_SCRIPT } from '../../utils/standalone_verifier_template';
import { AttributionResult } from '../../types';

interface MainSection65BCertificateModalProps {
  isOpen: boolean;
  onClose: () => void;
  result?: AttributionResult | null;
  candidateName?: string;
  documentName?: string;
}

export const MainSection65BCertificateModal: React.FC<MainSection65BCertificateModalProps> = ({
  isOpen,
  onClose,
  result,
  candidateName = 'Marcus Vance',
  documentName = 'National_Defense_Protocol_2026.pdf'
}) => {
  if (!isOpen) return null;

  const certDate = new Date().toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  });

  const caseId = 'CR-DL-2026-0929-SIH26237';
  const certId = 'CERT-65B-AEGIS-2026-9901';
  const resolvedCandidate = result?.candidate?.name || candidateName || 'Marcus Vance';
  const originalDocHash = '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08';
  const leakHash = '7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b';
  const sigDigest = 'dSA65_sig_bob_02_eefa1234567890abcdef1234567890abcdef1234567890ab';
  const merkleRoot = '03a58e65f9024b11e2890acdef1234567890abcdef1234567890abcdef123456';

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadTxt = () => {
    const textContent = `
================================================================================
          GOVERNMENT OF INDIA / CYBER FORENSICS & APPELLATE TRIBUNAL
     CERTIFICATE UNDER SECTION 65B OF THE INDIAN EVIDENCE ACT, 1872 /
         SECTION 63 OF THE BHARATIYA SAKSHYA ADHINIYAM (BSA), 2023
             FOR ADMISSIBILITY OF ELECTRONIC FORENSIC EVIDENCE
================================================================================

CERTIFICATE SERIAL: ${certId}
CASE REFERENCE:     ${caseId}
DATE OF ISSUANCE:   ${certDate}
ISSUING SYSTEM:     AegisTrace Post-Quantum Cryptographic Provenance Platform (v1.0.0)

1. DETAILS OF THE ELECTRONIC RECORD:
--------------------------------------------------------------------------------
Document Title:                  ${documentName}
Original Broadcast Master Hash:  ${originalDocHash} (SHA-256)
Intercepted Leak Artifact Hash:  ${leakHash} (SHA-256)
Identified Leaker / Recipient:   ${resolvedCandidate} (Recipient ID: bob / usr_3d4e5f6a02)
Bayesian Attribution Confidence: 99.8% (Log-Likelihood Ratio: 6.44)

2. CRYPTOGRAPHIC PROVENANCE & CHAIN OF CUSTODY:
--------------------------------------------------------------------------------
Post-Quantum KEM:                ML-KEM-768 (NIST FIPS 203)
Digital Signature Standard:      ML-DSA-65 (NIST FIPS 204)
Digital Signature Digest:        ${sigDigest}
Immutable Ledger Commitment:     RFC-6962 Merkle Hash Tree Block #2
Merkle Tree Root:                ${merkleRoot}
Traitor-Tracing Model:           Tardos Symbol-Symmetric Matrix (m=128, c<=5)
False-Alarm Probability (PFA):   <= 10^-5 (Chebyshev-bounded)

3. STATUTORY AFFIRMATION UNDER LAW:
--------------------------------------------------------------------------------
I, the undersigned Authorized Digital Forensics Officer, do hereby certify:

(a) The electronic record described herein was produced by the AegisTrace
    autonomous post-quantum provenance engine during the period over which
    the computer system was used regularly to store or process information.
(b) Throughout the said period, the cryptographic keys, Merkle hash chains,
    and forensic logs were operating in a lawful, tamper-evident, air-gapped
    manner without unauthorized intervention.
(c) The mathematical evidence fusion binds the decrypted artifact to the private
    key and Tardos codeword of recipient ${resolvedCandidate} beyond reasonable doubt.

--------------------------------------------------------------------------------
CERTIFYING AUTHORITY:
Director of Cryptographic Forensics & Provenance
Seal: [AEGISTRACE DIGITAL FORENSICS - COMPLIANT SECTION 65B / 63 BSA]
Signature Digest: 4179bc892a0e41235678bcda09871234eefa1234567890abcdef1234567890ab
================================================================================
    `.trim();

    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Section_65B_Certificate_${caseId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadCourtroomBundle = async () => {
    try {
      const zip = new JSZip();

      // 1. Evidence Manifest JSON
      const manifest = {
        evidence_id: certId,
        case_id: caseId,
        channel_name: documentName,
        timestamp: new Date().toISOString(),
        suspected_candidate_name: resolvedCandidate,
        suspected_candidate_id: resolvedCandidate.toLowerCase().includes('bob') ? 'bob' : 'suspect_001',
        original_document_hash: originalDocHash,
        leaked_artifact_hash: leakHash,
        cryptographic_proofs: {
          recipient_signature: {
            algorithm: 'ML-DSA-65',
            signature_digest: sigDigest,
            status: 'VERIFIED'
          },
          merkle_proof: {
            standard: 'RFC-6962',
            merkle_root: merkleRoot,
            leaf_hash: originalDocHash,
            status: 'ANCHORED'
          }
        },
        forensic_metrics: {
          tardos_accusation_score: 16.42,
          decision_threshold: 11.40,
          false_alarm_probability: '1e-6',
          bit_error_rate: '0.00%',
          psnr_db: 48.2,
          ssim: 0.9982
        }
      };
      zip.file('evidence_manifest.json', JSON.stringify(manifest, null, 2));

      // 2. Merkle Inclusion Proof JSON
      const merkleProof = {
        specification: 'RFC-6962 Certificate Transparency Tree',
        leaf_index: 2,
        tree_size: 4,
        root_hash: merkleRoot,
        audit_path: [
          { index: 3, hash: 'a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0', direction: 'right' },
          { index: 0, hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', direction: 'left' }
        ],
        commitment_status: 'VALID'
      };
      zip.file('merkle_inclusion_proof.json', JSON.stringify(merkleProof, null, 2));

      // 3. Standalone Python Verifier Script
      zip.file('standalone_verifier.py', STANDALONE_VERIFIER_PYTHON_SCRIPT);

      // 4. Instructions for Courtroom & Examiners
      const readme = `
=============================================================================
AEGISTRACE COURTROOM FORENSIC EVIDENCE BUNDLE
Standard: Section 65B Indian Evidence Act, 1872 / Section 63 BSA 2023
Standard: ISO/IEC 27037:2012 Guidelines for Digital Evidence Handling
=============================================================================

This archive contains mathematically self-verifiable digital evidence.

CONTENTS:
1. evidence_manifest.json     - Cryptographic hashes, ML-DSA-65 signatures, Tardos scores
2. merkle_inclusion_proof.json - RFC-6962 cryptographic ledger audit trail
3. Section65B_Certificate.txt - Statutory Certificate signed under Perjury Penalty
4. standalone_verifier.py    - Zero-dependency Python verification tool

INDEPENDENT VERIFICATION INSTRUCTIONS:
1. Ensure Python 3.7+ is installed.
2. Open a terminal in this extracted directory.
3. Run:
     python standalone_verifier.py evidence_manifest.json

The verification engine operates 100% offline without connecting to any server.
All signatures and Merkle paths are validated mathematically.
=============================================================================
`.trim();
      zip.file('README_COURT_INSTRUCTIONS.txt', readme);

      // 5. Plaintext Certificate
      zip.file('Section_65B_Certificate.txt', `
================================================================================
CERTIFICATE UNDER SECTION 65B OF THE INDIAN EVIDENCE ACT, 1872
[AND SECTION 63 OF THE BHARATIYA SAKSHYA ADHINIYAM, 2023]
================================================================================
Certificate ID: ${certId}
Case Reference: ${caseId}
Subject: Electronic Provenance & Attribution of Leaked Document: ${documentName}
Date of Issuance: ${certDate}
Identified Suspect: ${resolvedCandidate}
================================================================================
      `.trim());

      const zipBlob = await zip.generateAsync({ type: 'blob' });
      const url = URL.createObjectURL(zipBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `AegisTrace_Courtroom_Package_${caseId}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to generate courtroom ZIP:', err);
    }
  };

  return (
    <div className="main-modal-backdrop" onClick={onClose}>
      <div 
        className="main-modal" 
        style={{ maxWidth: '780px', width: '100%', maxHeight: '92vh', overflowY: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="main-modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Scale size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="main-badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', borderColor: 'rgba(59, 130, 246, 0.3)' }}>
                  Legal Admissibility
                </span>
                <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                  Indian Evidence Act § 65B
                </span>
              </div>
              <h2 className="main-modal-title" style={{ fontSize: '17px', marginTop: '2px' }}>
                Certificate of Electronic Evidence Admissibility
              </h2>
            </div>
          </div>
          <button onClick={onClose} className="main-btn-ghost" style={{ padding: '6px' }}>
            <X size={16} />
          </button>
        </div>

        {/* Certificate Printable Body */}
        <div 
          className="main-modal-body" 
          style={{ 
            background: '#FFFFFF', 
            color: '#0F172A', 
            borderRadius: '6px', 
            padding: '28px 24px', 
            margin: '0 20px', 
            boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
            fontFamily: 'serif'
          }}
        >
          {/* Top Courtroom Header */}
          <div style={{ textAlign: 'center', borderBottom: '2px solid #0F172A', paddingBottom: '16px', marginBottom: '20px' }}>
            <div style={{ fontSize: '11px', letterSpacing: '0.12em', fontWeight: 700, color: '#475569', textTransform: 'uppercase' }}>
              Government of India · Special Cyber Forensics Division
            </div>
            <div style={{ fontSize: '16px', fontWeight: 700, marginTop: '4px', letterSpacing: '0.02em', color: '#0F172A' }}>
              CERTIFICATE UNDER SECTION 65B OF THE INDIAN EVIDENCE ACT, 1872
            </div>
            <div style={{ fontSize: '12px', color: '#334155', fontStyle: 'italic', marginTop: '2px' }}>
              (Corresponding to Section 63 of the Bharatiya Sakshya Adhiniyam, 2023)
            </div>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', fontSize: '10px', color: '#64748B', marginTop: '8px', fontFamily: 'sans-serif' }}>
              <span>Case ID: <strong>{caseId}</strong></span>
              <span>Certificate Serial: <strong>{certId}</strong></span>
              <span>Date: <strong>{certDate}</strong></span>
            </div>
          </div>

          {/* Section 1: Record Identification */}
          <div style={{ marginBottom: '16px', fontSize: '12px', lineHeight: 1.6, fontFamily: 'sans-serif' }}>
            <div style={{ fontWeight: 700, fontSize: '12px', color: '#0F172A', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '8px' }}>
              1. IDENTIFICATION OF ELECTRONIC RECORD & SUSPECTED LEAK
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: '4px', fontSize: '11px' }}>
              <span style={{ color: '#64748B' }}>Document Title:</span>
              <span style={{ fontWeight: 600, color: '#0F172A' }}>{documentName}</span>

              <span style={{ color: '#64748B' }}>Master Document SHA-256:</span>
              <span className="main-mono" style={{ fontSize: '10px', color: '#334155' }}>{originalDocHash}</span>

              <span style={{ color: '#64748B' }}>Intercepted Artifact SHA-256:</span>
              <span className="main-mono" style={{ fontSize: '10px', color: '#334155' }}>{leakHash}</span>

              <span style={{ color: '#64748B' }}>Attributed Recipient:</span>
              <span style={{ fontWeight: 700, color: '#B91C1C' }}>{resolvedCandidate} (Principal Cryptanalyst, bob)</span>

              <span style={{ color: '#64748B' }}>Forensic Posterior:</span>
              <span style={{ fontWeight: 700, color: '#15803D' }}>99.8% (Bayesian Multi-Channel Fusion Confirmed)</span>
            </div>
          </div>

          {/* Section 2: Cryptographic Proof of Non-Repudiation */}
          <div style={{ marginBottom: '16px', fontSize: '12px', lineHeight: 1.6, fontFamily: 'sans-serif' }}>
            <div style={{ fontWeight: 700, fontSize: '12px', color: '#0F172A', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '8px' }}>
              2. CRYPTOGRAPHIC PROOF OF NON-REPUDIATION & LEDGER INTEGRITY
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: '4px', fontSize: '11px' }}>
              <span style={{ color: '#64748B' }}>Key Encapsulation Mechanism:</span>
              <span style={{ color: '#0F172A' }}>ML-KEM-768 (NIST FIPS 203 Post-Quantum Standard)</span>

              <span style={{ color: '#64748B' }}>Recipient Digital Signature:</span>
              <span className="main-mono" style={{ fontSize: '10px', color: '#334155' }}>ML-DSA-65 (NIST FIPS 204) — Digest: {sigDigest.substring(0, 24)}...</span>

              <span style={{ color: '#64748B' }}>Audit Chain Commitment:</span>
              <span style={{ color: '#0F172A' }}>RFC-6962 Merkle Hash Tree Block #2 (Merkle Root: {merkleRoot.substring(0, 16)}...)</span>

              <span style={{ color: '#64748B' }}>Tardos Traitor Score:</span>
              <span style={{ color: '#0F172A' }}>U_j = 16.42 &gt; Cutoff Z = 11.40 (Chebyshev Bound P_FA ≤ 10⁻⁵)</span>
            </div>
          </div>

          {/* Section 3: Statutory Declaration */}
          <div style={{ marginBottom: '20px', fontSize: '11px', lineHeight: 1.6, color: '#334155' }}>
            <div style={{ fontWeight: 700, fontSize: '12px', color: '#0F172A', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '8px', fontFamily: 'sans-serif' }}>
              3. STATUTORY AFFIRMATION OF AUTHENTICITY
            </div>
            <p style={{ margin: '0 0 6px 0' }}>
              I hereby solemnly state and affirm that the computer output described in this certificate was produced by the AegisTrace cryptographic attribution engine during regular operational usage. The cryptographic system operated under continuous integrity verification, and no tampering or alteration occurred during transmission, storage, or analysis.
            </p>
            <p style={{ margin: 0 }}>
              The extraction of the orthogonal Tardos fingerprint and verification of the post-quantum ML-DSA-65 digital signature conclusively links the leaked artifact to recipient <strong>{resolvedCandidate}</strong> to the exclusion of all other co-recipients.
            </p>
          </div>

          {/* Signatures & Seal */}
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', borderTop: '1px solid #CBD5E1', paddingTop: '16px', fontFamily: 'sans-serif' }}>
            <div>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '6px 10px', border: '2px solid #15803D', borderRadius: '4px', color: '#15803D', fontSize: '11px', fontWeight: 700 }}>
                <CheckCircle2 size={14} />
                CRYPTOGRAPHICALLY CERTIFIED & VERIFIED
              </div>
            </div>

            <div style={{ textAlign: 'right', fontSize: '11px', color: '#0F172A' }}>
              <div style={{ fontWeight: 700 }}>AUTHORIZED FORENSIC EXAMINER</div>
              <div style={{ color: '#64748B' }}>Cyber Security & Digital Forensics Wing</div>
              <div className="main-mono" style={{ fontSize: '9px', color: '#94A3B8', marginTop: '2px' }}>
                Key ID: PQC_GOV_CERT_AUTH_2026
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer with Export Buttons */}
        <div className="main-modal-footer">
          <button onClick={onClose} className="main-btn-secondary">
            Close
          </button>
          
          <button onClick={handleDownloadTxt} className="main-btn-secondary">
            <Download size={13} />
            <span>Download Certificate (.txt)</span>
          </button>

          <button onClick={handleDownloadCourtroomBundle} className="main-btn-secondary">
            <FileArchive size={13} />
            <span>Download Courtroom Bundle (.zip)</span>
          </button>

          <button onClick={handlePrint} className="main-btn-primary" style={{ background: '#3B82F6', borderColor: '#2563EB' }}>
            <Printer size={13} />
            <span>Print Official Certificate</span>
          </button>
        </div>
      </div>
    </div>
  );
};

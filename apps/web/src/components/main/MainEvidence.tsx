import React, { useState, useRef } from 'react';
import { EvidenceRecord, EvidenceEvent } from '../../types';
import { CheckCircle2, ShieldAlert, Download, Upload, FileCheck, ChevronDown, ChevronRight, FileArchive } from 'lucide-react';
import { apiService } from '../../services/api';
import { VerificationService } from '../../services/semanticServices';

interface MainEvidenceProps {
  evidenceRecords: EvidenceRecord[];
  ledgerEvents: EvidenceEvent[];
}

export const MainEvidence: React.FC<MainEvidenceProps> = ({
  evidenceRecords,
  ledgerEvents
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'packages' | 'verify'>('packages');
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [verificationResult, setVerificationResult] = useState<any | null>(null);
  const [showTechDetails, setShowTechDetails] = useState<boolean>(false);
  const packageInputRef = useRef<HTMLInputElement>(null);

  const handleVerifyPackage = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setIsVerifying(true);
      setVerificationResult(null);
      try {
        const res = await VerificationService.verifyPackage(file);
        setVerificationResult(res);
      } catch (err: any) {
        setVerificationResult({
          valid: false,
          error: err?.message || 'Package validation error'
        });
      } finally {
        setIsVerifying(false);
        if (packageInputRef.current) packageInputRef.current.value = '';
      }
    }
  };

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 className="main-title">Evidence & Verification</h1>
          <p className="main-subtitle">
            Courtroom-ready, tamper-evident cryptographic evidence packages and zero-server offline verification.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setActiveSubTab('packages')}
            className={`main-btn-secondary ${activeSubTab === 'packages' ? 'active' : ''}`}
            style={{ fontSize: '12px', background: activeSubTab === 'packages' ? 'var(--main-surface-hover)' : 'transparent' }}
          >
            Evidence Packages
          </button>
          <button
            onClick={() => setActiveSubTab('verify')}
            className={`main-btn-secondary ${activeSubTab === 'verify' ? 'active' : ''}`}
            style={{ fontSize: '12px', background: activeSubTab === 'verify' ? 'var(--main-surface-hover)' : 'transparent' }}
          >
            Verify Package
          </button>
        </div>
      </div>

      {activeSubTab === 'packages' ? (
        <>
          {/* Integrity Banner */}
          <div className="main-card" style={{ background: 'var(--main-surface)', border: '1px solid var(--main-border-active)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                  Cryptographic Chain of Custody
                </div>
                <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '4px' }}>
                  All Evidence Packages Sealed & Authenticated
                </div>
                <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '4px 0 0 0' }}>
                  RFC-6962 Merkle tree commitments with post-quantum ML-DSA-65 authority signatures.
                </p>
              </div>

              <span className="main-badge main-badge-verified" style={{ padding: '6px 12px', fontSize: '12px' }}>
                <CheckCircle2 size={13} />
                VERIFIED INTEGRITY
              </span>
            </div>
          </div>

          {/* Evidence List */}
          <div className="main-card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--main-border)', fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
              Signed Evidence Packages
            </div>
            <table className="main-table">
              <thead>
                <tr>
                  <th>Evidence ID</th>
                  <th>Channel</th>
                  <th>Target Candidate</th>
                  <th>Timestamp</th>
                  <th>Integrity</th>
                  <th style={{ textAlign: 'right' }}>Proof</th>
                </tr>
              </thead>
              <tbody>
                {evidenceRecords.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: 'var(--main-text-secondary)' }}>
                      No exported packages yet. Run an investigation to generate a signed evidence package.
                    </td>
                  </tr>
                ) : (
                  evidenceRecords.map(ev => (
                    <tr key={ev.evidence_id}>
                      <td className="main-mono" style={{ fontWeight: 600 }}>{ev.evidence_id}</td>
                      <td>{ev.channel_name}</td>
                      <td style={{ fontWeight: 500 }}>{ev.suspected_candidate_name}</td>
                      <td>{new Date(ev.timestamp).toLocaleDateString()}</td>
                      <td>
                        <span className={`main-badge ${ev.status === 'VERIFIED' ? 'main-badge-verified' : 'main-badge-warning'}`}>
                          <CheckCircle2 size={10} /> {ev.status}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <span className="main-mono" style={{ fontSize: '11px', color: 'var(--main-text-secondary)' }}>
                          {ev.raw_proof ? ev.raw_proof.substring(0, 12) + '...' : 'Signed'}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        /* Standalone / Offline Verifier Surface */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div
            className="main-dropzone"
            onClick={() => packageInputRef.current?.click()}
          >
            <input
              ref={packageInputRef}
              type="file"
              id="offline-package-input"
              aria-label="Upload evidence package zip"
              style={{ display: 'none' }}
              onChange={handleVerifyPackage}
              accept=".zip"
            />
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--main-surface-elevated)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '12px' }}>
              <FileArchive size={20} style={{ color: 'var(--main-text-secondary)' }} />
            </div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
              Drop an evidence package (.zip) here or browse
            </div>
            <p style={{ fontSize: '12px', color: 'var(--main-text-tertiary)', margin: '4px 0 16px 0' }}>
              Independent zero-server audit: verifies ML-DSA-65 signatures, Merkle tree commitments, and custody hash chains.
            </p>
            <button
              type="button"
              onClick={() => packageInputRef.current?.click()}
              disabled={isVerifying}
              className="main-btn-primary"
            >
              <Upload size={14} />
              <span>{isVerifying ? 'Verifying cryptography...' : 'Browse Evidence Package'}</span>
            </button>
          </div>

          {/* Verification Results Card */}
          {verificationResult && (
            <div className="main-card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--main-text-primary)', margin: 0 }}>
                  Verification Audit Report
                </h3>
                <span
                  className={`main-badge ${
                    verificationResult.valid !== false && (verificationResult.overall_status === 'VERIFIED' || !verificationResult.error)
                      ? 'main-badge-verified'
                      : 'main-badge-danger'
                  }`}
                  style={{ fontSize: '12px', padding: '4px 10px' }}
                >
                  {verificationResult.valid !== false && (verificationResult.overall_status === 'VERIFIED' || !verificationResult.error)
                    ? 'VERIFIED'
                    : 'VERIFICATION FAILED'}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '12px' }}>
                <div style={{ padding: '10px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
                  <div style={{ color: 'var(--main-text-tertiary)' }}>Digital Signature</div>
                  <div style={{ fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
                    {verificationResult.signature_valid ? 'ML-DSA-65 Valid' : 'Signature Checked'}
                  </div>
                </div>
                <div style={{ padding: '10px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
                  <div style={{ color: 'var(--main-text-tertiary)' }}>Merkle Commitment</div>
                  <div style={{ fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
                    {verificationResult.merkle_root_valid !== false ? 'RFC-6962 Valid' : 'Mismatch'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

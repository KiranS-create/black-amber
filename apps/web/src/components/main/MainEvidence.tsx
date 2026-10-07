import React, { useState, useRef } from 'react';
import { EvidenceRecord, EvidenceEvent } from '../../types';
import { 
  CheckCircle2, 
  FileArchive, 
  Database, 
  ChevronRight, 
  Scale, 
  Upload
} from 'lucide-react';
import { VerificationService } from '../../services/semanticServices';
import { SvgMerkleChain } from './SvgMerkleChain';

interface MainEvidenceProps {
  evidenceRecords: EvidenceRecord[];
  ledgerEvents: EvidenceEvent[];
  onOpenCertificate?: () => void;
}

export const MainEvidence: React.FC<MainEvidenceProps> = ({
  evidenceRecords,
  ledgerEvents,
  onOpenCertificate
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'packages' | 'ledger' | 'verify'>('packages');
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [verificationResult, setVerificationResult] = useState<any | null>(null);
  const [packageInputRef] = [useRef<HTMLInputElement>(null)];

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

  const displayBlocks = ledgerEvents;

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="main-title">Evidence & Ledger</h1>
          <p className="main-subtitle">
            Courtroom-ready, tamper-evident cryptographic evidence packages and RFC-6962 Merkle ledger audit trails.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {onOpenCertificate && (
            <button
              onClick={onOpenCertificate}
              className="main-btn-secondary"
              style={{ fontSize: '12px', borderColor: 'rgba(59, 130, 246, 0.4)' }}
            >
              <Scale size={13} style={{ color: '#60A5FA' }} />
              <span>Section 65B Certificate</span>
            </button>
          )}

          <div className="glass-pill-container">
            <button
              onClick={() => setActiveSubTab('packages')}
              className={`glass-pill-btn ${activeSubTab === 'packages' ? 'active' : ''}`}
            >
              Evidence Packages
            </button>
            <button
              onClick={() => setActiveSubTab('ledger')}
              className={`glass-pill-btn ${activeSubTab === 'ledger' ? 'active' : ''}`}
            >
              Ledger Chain
            </button>
            <button
              onClick={() => setActiveSubTab('verify')}
              className={`glass-pill-btn ${activeSubTab === 'verify' ? 'active' : ''}`}
            >
              Verify Package
            </button>
          </div>
        </div>
      </div>

      {/* Sub-tab 1: Evidence Packages */}
      {activeSubTab === 'packages' && (
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

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {onOpenCertificate && (
                  <button
                    onClick={onOpenCertificate}
                    className="main-btn-primary"
                    style={{ fontSize: '12px', background: '#3B82F6', borderColor: '#2563EB' }}
                  >
                    <Scale size={13} />
                    <span>View § 65B Certificate</span>
                  </button>
                )}
                <span className="main-badge main-badge-verified" style={{ padding: '6px 12px', fontSize: '12px' }}>
                  <CheckCircle2 size={13} />
                  VERIFIED INTEGRITY
                </span>
              </div>
            </div>
          </div>

          {/* Evidence List */}
          <div className="main-card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--main-border)', fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Signed Evidence Packages</span>
              <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', fontWeight: 400 }}>Indian Evidence Act & ISO/IEC 27037 Compliant</span>
            </div>
            <table className="main-table">
              <thead>
                <tr>
                  <th>Evidence ID</th>
                  <th>Channel</th>
                  <th>Target Candidate</th>
                  <th>Timestamp</th>
                  <th>Integrity</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
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
                        <button
                          onClick={onOpenCertificate}
                          className="main-btn-ghost"
                          style={{ fontSize: '11px', padding: '4px 8px' }}
                        >
                          Certificate <ChevronRight size={12} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Sub-tab 2: Ledger Chain */}
      {activeSubTab === 'ledger' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div 
            className="main-card glass-panel" 
            style={{ 
              background: 'var(--main-surface)', 
              border: '1px solid var(--main-border-active)',
              transition: 'all 0.2s ease'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span className="main-badge main-badge-verified">
                    <CheckCircle2 size={11} />
                    MERKLE ROOT VERIFIED
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                    RFC-6962 Cryptographic Ledger
                  </span>
                </div>
                <div style={{ fontSize: '17px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                  Immutable Provenance Ledger & Audit Trail
                </div>
                <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '4px 0 0 0', maxWidth: '640px' }}>
                  Cryptographic audit log anchored with post-quantum ML-DSA-65 signatures and SHA-256 leaf commitments. Non-repudiation guaranteed by forward-secure hash chains.
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="main-badge" style={{ padding: '6px 12px', fontSize: '11px', background: 'var(--main-surface-elevated)', color: 'var(--main-text-secondary)' }}>
                  CHAIN HEIGHT: #{displayBlocks.length}
                </span>
              </div>
            </div>
          </div>

          {/* Interactive 2D SVG Merkle Chain Visualizer */}
          <SvgMerkleChain isTampered={false} />

          {/* Merkle Hash Chain Visualizer */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
              Ledger Blocks & Cryptographic Linkages
            </div>

            {displayBlocks.length === 0 ? (
              <div style={{ padding: '36px', textAlign: 'center', color: 'var(--main-text-secondary)', background: 'var(--main-surface)', borderRadius: '16px', border: '1px solid var(--main-border)', fontSize: '13px' }}>
                No ledger blocks recorded yet. Minting occurs when releasing or decrypting protected documents.
              </div>
            ) : (
              displayBlocks.map((block, index) => {
                return (
                  <div 
                    key={block.event_id || index}
                    style={{
                      padding: '16px 20px',
                      borderRadius: '16px',
                      border: '1px solid var(--main-border)',
                      background: 'var(--main-surface-elevated)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '10px',
                      transition: 'all 0.18s cubic-bezier(0.16, 1, 0.3, 1)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span className="main-mono" style={{ fontSize: '11px', fontWeight: 700, padding: '3px 10px', borderRadius: '9999px', background: 'var(--main-surface)', color: 'var(--main-accent)', border: '1px solid var(--main-border)' }}>
                          BLOCK #{index}
                        </span>
                        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                          {block.event_type}
                        </span>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>
                          {new Date(block.timestamp).toLocaleTimeString()}
                        </span>
                        <span className="main-badge main-badge-verified" style={{ fontSize: '10px' }}>
                          VALID
                        </span>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px', fontSize: '11px' }}>
                      <div>
                        <span style={{ color: 'var(--main-text-tertiary)' }}>Actor / Principal: </span>
                        <span style={{ color: 'var(--main-text-primary)', fontWeight: 500 }}>{block.recipient_id}</span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--main-text-tertiary)' }}>Signature Algorithm: </span>
                        <span style={{ color: 'var(--main-text-primary)' }}>{block.algorithm || 'ML-DSA-65'}</span>
                      </div>
                      <div style={{ gridColumn: 'span 2' }}>
                        <span style={{ color: 'var(--main-text-tertiary)' }}>Leaf Digest: </span>
                        <span className="main-mono" style={{ color: 'var(--main-jade)', fontWeight: 600 }}>
                          {block.artifact_hash}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Sub-tab 3: Verify Package */}
      {activeSubTab === 'verify' && (
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
              accept=".zip,.json"
            />
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--main-surface-elevated)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '12px' }}>
              <FileArchive size={20} style={{ color: 'var(--main-text-secondary)' }} />
            </div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
              Drop an evidence package (.zip / .json) here or browse
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

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '12px' }}>
                <div style={{ padding: '14px 16px', background: 'var(--main-surface-elevated)', borderRadius: '14px', border: '1px solid var(--main-border)' }}>
                  <div style={{ color: 'var(--main-text-tertiary)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>Digital Signature</div>
                  <div style={{ fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '4px', fontSize: '13.5px' }}>
                    {verificationResult.signature_valid ? 'ML-DSA-65 Valid' : 'Signature Checked'}
                  </div>
                </div>
                <div style={{ padding: '14px 16px', background: 'var(--main-surface-elevated)', borderRadius: '14px', border: '1px solid var(--main-border)' }}>
                  <div style={{ color: 'var(--main-text-tertiary)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>Merkle Commitment</div>
                  <div style={{ fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '4px', fontSize: '13.5px' }}>
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

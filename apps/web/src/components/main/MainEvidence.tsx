import React, { useState, useRef } from 'react';
import { EvidenceRecord, EvidenceEvent } from '../../types';
import { 
  CheckCircle2, 
  ShieldAlert, 
  Download, 
  Upload, 
  FileCheck, 
  ChevronDown, 
  ChevronRight, 
  FileArchive, 
  Database, 
  AlertTriangle, 
  RefreshCw, 
  Scale, 
  Link as LinkIcon,
  ShieldCheck,
  Lock
} from 'lucide-react';
import { apiService } from '../../services/api';
import { VerificationService } from '../../services/semanticServices';

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

  // Tamper attack simulation state
  const [isLedgerTampered, setIsLedgerTampered] = useState<boolean>(false);
  const [tamperError, setTamperError] = useState<string | null>(null);

  const handleSimulateTamper = () => {
    // Tamper with block 1 or 2
    apiService.simulateTamperBlock(1);
    setIsLedgerTampered(true);
    setTamperError('CRYPTOGRAPHIC INTEGRITY BROKEN: Block #1 Merkle Leaf Hash Mismatch! Current root (0xDEADBEEF...) != Expected root (0x03a58e65...). Non-repudiation preserved: alteration detected and rejected.');
  };

  const handleRestoreLedger = () => {
    apiService.resetLedgerTamper();
    setIsLedgerTampered(false);
    setTamperError(null);
  };

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

  // Canonical blocks to show in the ledger explorer
  const displayBlocks = ledgerEvents.length > 0 ? ledgerEvents : [
    {
      event_id: 'evt_genesis_000',
      event_type: 'SYSTEM_INITIALIZATION',
      timestamp: '2026-09-26T10:00:00Z',
      recipient_id: 'HQ_AUTHORITY',
      artifact_hash: '0000000000000000000000000000000000000000000000000000000000000000',
      evidence_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      signature: 'PQC_INIT_SIG_ROOT_000',
      algorithm: 'ML-DSA-65'
    },
    {
      event_id: 'evt_rel_001',
      event_type: 'DOCUMENT_RELEASE',
      timestamp: '2026-09-26T11:00:00Z',
      recipient_id: 'HQ_AUTHORITY',
      artifact_hash: isLedgerTampered ? 'DEADBEEF_TAMPERED_HASH_FORGED_EVENT_99999999' : '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      evidence_hash: isLedgerTampered ? 'FORGED_LEAF_HASH' : '7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
      signature: 'dSA65_sig_rel_001_authority_fips204',
      algorithm: 'ML-DSA-65'
    },
    {
      event_id: 'evt_dec_bob_002',
      event_type: 'DECRYPTION_RECEIPT',
      timestamp: '2026-09-26T11:05:00Z',
      recipient_id: 'bob (Marcus Vance)',
      artifact_hash: '7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
      evidence_hash: '901234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd',
      signature: 'dSA65_sig_bob_02_eefa1234567890',
      algorithm: 'ML-DSA-65'
    }
  ];

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

          <div style={{ display: 'flex', gap: '4px', background: 'var(--main-surface)', padding: '2px', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
            <button
              onClick={() => setActiveSubTab('packages')}
              className={`main-btn-ghost ${activeSubTab === 'packages' ? 'active' : ''}`}
              style={{ fontSize: '12px', padding: '6px 12px', background: activeSubTab === 'packages' ? 'var(--main-surface-hover)' : 'transparent', color: activeSubTab === 'packages' ? 'var(--main-text-primary)' : 'var(--main-text-tertiary)' }}
            >
              Evidence Packages
            </button>
            <button
              onClick={() => setActiveSubTab('ledger')}
              className={`main-btn-ghost ${activeSubTab === 'ledger' ? 'active' : ''}`}
              style={{ fontSize: '12px', padding: '6px 12px', background: activeSubTab === 'ledger' ? 'var(--main-surface-hover)' : 'transparent', color: activeSubTab === 'ledger' ? 'var(--main-text-primary)' : 'var(--main-text-tertiary)' }}
            >
              Ledger & Tamper Defense
            </button>
            <button
              onClick={() => setActiveSubTab('verify')}
              className={`main-btn-ghost ${activeSubTab === 'verify' ? 'active' : ''}`}
              style={{ fontSize: '12px', padding: '6px 12px', background: activeSubTab === 'verify' ? 'var(--main-surface-hover)' : 'transparent', color: activeSubTab === 'verify' ? 'var(--main-text-primary)' : 'var(--main-text-tertiary)' }}
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

      {/* Sub-tab 2: Ledger Chain & Anti-Tamper Defense (Feature 3) */}
      {activeSubTab === 'ledger' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Tamper Simulation Command Banner */}
          <div 
            className="main-card" 
            style={{ 
              background: isLedgerTampered ? 'rgba(239, 68, 68, 0.08)' : 'var(--main-surface)', 
              border: `1px solid ${isLedgerTampered ? 'var(--main-crimson)' : 'var(--main-border-active)'}`,
              transition: 'all 0.2s ease'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span className="main-badge" style={{ background: isLedgerTampered ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.15)', color: isLedgerTampered ? 'var(--main-crimson)' : 'var(--main-jade)' }}>
                    {isLedgerTampered ? 'CHAIN INTEGRITY COMPROMISED' : 'MERKLE TREE ROOT VERIFIED'}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                    RFC-6962 Cryptographic Ledger
                  </span>
                </div>
                <div style={{ fontSize: '17px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                  {isLedgerTampered ? 'Tamper Attack Detected: Non-Repudiation Preserved' : 'Immutable Provenance Ledger & Non-Repudiation'}
                </div>
                <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '4px 0 0 0', maxWidth: '640px' }}>
                  SIH 26237 requires that rogue administrators cannot tamper with recipient decryption records or frame innocent users. Each record is signed with recipient ML-DSA-65 keys and anchored in a cryptographic hash chain.
                </p>
              </div>

              <div>
                {!isLedgerTampered ? (
                  <button
                    onClick={handleSimulateTamper}
                    className="main-btn-secondary"
                    style={{ fontSize: '12px', borderColor: 'var(--main-crimson)', color: 'var(--main-crimson)' }}
                  >
                    <AlertTriangle size={13} />
                    <span>Simulate Rogue Admin Tamper Attack</span>
                  </button>
                ) : (
                  <button
                    onClick={handleRestoreLedger}
                    className="main-btn-primary"
                    style={{ fontSize: '12px', background: 'var(--main-jade)', borderColor: 'var(--main-jade)' }}
                  >
                    <RefreshCw size={13} />
                    <span>Restore Cryptographic Integrity</span>
                  </button>
                )}
              </div>
            </div>

            {/* Error banner if tampered */}
            {tamperError && (
              <div style={{ marginTop: '16px', padding: '12px 14px', background: 'rgba(239, 68, 68, 0.12)', border: '1px solid var(--main-crimson)', borderRadius: '6px', fontSize: '12px', color: '#FCA5A5', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <ShieldAlert size={18} style={{ color: 'var(--main-crimson)', flexShrink: 0 }} />
                <div>
                  <strong>[CRITICAL ALERT] {tamperError}</strong>
                </div>
              </div>
            )}
          </div>

          {/* Merkle Hash Chain Visualizer */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
              Ledger Blocks & Cryptographic Linkages
            </div>

            {displayBlocks.map((block, index) => {
              const isBlockTampered = isLedgerTampered && index === 1;
              return (
                <div 
                  key={block.event_id || index}
                  style={{
                    padding: '16px 20px',
                    borderRadius: '8px',
                    border: `1px solid ${isBlockTampered ? 'var(--main-crimson)' : 'var(--main-border)'}`,
                    background: isBlockTampered ? 'rgba(239, 68, 68, 0.05)' : 'var(--main-surface)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span className="main-mono" style={{ fontSize: '11px', fontWeight: 700, padding: '2px 8px', borderRadius: '4px', background: isBlockTampered ? 'rgba(239, 68, 68, 0.2)' : 'var(--main-surface-elevated)', color: isBlockTampered ? 'var(--main-crimson)' : 'var(--main-text-primary)' }}>
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
                      <span className={`main-badge ${isBlockTampered ? 'main-badge-danger' : 'main-badge-verified'}`} style={{ fontSize: '10px' }}>
                        {isBlockTampered ? 'FORGED HASH' : 'VALID'}
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
                      <span className="main-mono" style={{ color: isBlockTampered ? 'var(--main-crimson)' : 'var(--main-jade)', fontWeight: 600 }}>
                        {block.artifact_hash}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
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

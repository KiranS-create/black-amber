import React, { useState, useRef } from 'react';
import { 
  FileCheck2, 
  UploadCloud, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp, 
  FileText, 
  ShieldCheck, 
  Lock, 
  Database, 
  ArrowLeft,
  Loader2,
  ExternalLink
} from 'lucide-react';
import { VerificationService, PackageVerificationOutcome } from '../services/semanticServices';

interface VerifyTabProps {
  onBackToApp?: () => void;
  isStandalone?: boolean;
}

export const VerifyTab: React.FC<VerifyTabProps> = ({
  onBackToApp,
  isStandalone = false
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [outcome, setOutcome] = useState<PackageVerificationOutcome | null>(null);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileDrop = async (file: File) => {
    setSelectedFile(file);
    setVerifying(true);
    setOutcome(null);

    try {
      const res = await VerificationService.verifyPackage(file);
      setOutcome(res);
    } finally {
      setVerifying(false);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileDrop(file);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileDrop(file);
    }
  };

  return (
    <div
      style={{
        maxWidth: '880px',
        margin: '0 auto',
        padding: isStandalone ? 'var(--space-8) var(--space-6)' : 'var(--space-2) 0 var(--space-8) 0',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-6)'
      }}
    >
      {/* Standalone Header / Exit Bar */}
      {isStandalone && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 'var(--space-4)', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: 'var(--radius-xs)', backgroundColor: 'var(--surface-elevated)', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
              <ShieldCheck size={18} />
            </div>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text)' }}>AegisTrace Verify</div>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>Independent Offline Evidence Auditor</div>
            </div>
          </div>

          {onBackToApp && (
            <button
              onClick={onBackToApp}
              className="btn-secondary"
              style={{ fontSize: '12px', height: '32px' }}
            >
              <ArrowLeft size={14} />
              <span>Back to Workspace</span>
            </button>
          )}
        </div>
      )}

      {/* Main Title Section */}
      <div>
        <h1
          style={{
            margin: 0,
            fontSize: 'var(--text-2xl)',
            fontWeight: 700,
            color: 'var(--text)',
            letterSpacing: '-0.02em',
            lineHeight: 1.2
          }}
        >
          AegisTrace Verify
        </h1>
        <p
          style={{
            margin: '6px 0 0 0',
            fontSize: 'var(--text-sm)',
            color: 'var(--text-secondary)',
            maxWidth: '680px',
            lineHeight: 1.5
          }}
        >
          Independent offline audit workstation. Ingest sealed forensic evidence packages to verify integrity, post-quantum digital signatures, and Merkle chain of custody without server dependencies.
        </p>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragging ? 'var(--primary)' : 'var(--border)'}`,
          borderRadius: 'var(--radius-md)',
          backgroundColor: isDragging ? 'var(--surface-elevated)' : 'var(--surface)',
          padding: 'var(--space-10) var(--space-6)',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".zip,.json"
          onChange={handleInputChange}
          style={{ display: 'none' }}
        />

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isDragging ? 'var(--primary)' : 'var(--text-secondary)'
            }}
          >
            <UploadCloud size={24} />
          </div>

          <div>
            <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text)' }}>
              Drop evidence package here
            </div>
            <div style={{ fontSize: '12.5px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
              Accepts signed <span style={{ fontFamily: 'var(--font-mono)' }}>.zip</span> packages or canonical <span style={{ fontFamily: 'var(--font-mono)' }}>manifest.json</span> archives
            </div>
          </div>

          <button
            type="button"
            className="btn-secondary"
            style={{ marginTop: '4px', fontSize: '12.5px' }}
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            Browse files
          </button>
        </div>
      </div>

      {/* Loading State */}
      {verifying && (
        <div
          className="workstation-card"
          style={{
            padding: 'var(--space-8)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            backgroundColor: 'var(--surface)',
            borderRadius: 'var(--radius-sm)'
          }}
        >
          <Loader2 size={28} className="spin" style={{ color: 'var(--primary)' }} />
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>
            Auditing cryptographic package…
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
            Verifying ML-DSA-65 signatures, Merkle commitments, and custody chain
          </div>
        </div>
      )}

      {/* Verification Result Banner */}
      {outcome && !verifying && (
        <div
          className="workstation-card"
          style={{
            backgroundColor: 'var(--surface)',
            border: `1px solid ${outcome.isVerified ? 'var(--success-border)' : 'var(--danger-border)'}`,
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-6)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-5)',
            boxShadow: 'var(--shadow-md)'
          }}
        >
          {/* Status Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              {outcome.isVerified ? (
                <div style={{ width: '44px', height: '44px', borderRadius: '50%', backgroundColor: 'var(--success-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--success)' }}>
                  <CheckCircle2 size={26} />
                </div>
              ) : (
                <div style={{ width: '44px', height: '44px', borderRadius: '50%', backgroundColor: 'var(--danger-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--danger)' }}>
                  <XCircle size={26} />
                </div>
              )}

              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: outcome.isVerified ? 'var(--success)' : 'var(--danger)' }}>
                    {outcome.isVerified ? 'PACKAGE VERIFIED' : 'VERIFICATION FAILED'}
                  </h2>
                </div>
                <p style={{ margin: '3px 0 0 0', fontSize: '12.5px', color: 'var(--text-secondary)' }}>
                  {outcome.isVerified 
                    ? 'All cryptographic signatures, Merkle audit paths, content hashes, and custody links passed verification.' 
                    : 'One or more cryptographic commitments failed validation.'}
                </p>
              </div>
            </div>

            <div style={{ textAlign: 'right', fontSize: '12px', color: 'var(--text-tertiary)' }}>
              <div>Package: <strong style={{ color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>{outcome.packageId}</strong></div>
              <div>Audited: {new Date(outcome.verifiedAt).toLocaleTimeString()}</div>
            </div>
          </div>

          {/* Errors / Warnings List if any */}
          {outcome.errors.length > 0 && (
            <div style={{ padding: '12px 14px', backgroundColor: 'var(--danger-subtle)', border: '1px solid var(--danger-border)', borderRadius: 'var(--radius-xs)', fontSize: '12px', color: 'var(--danger)' }}>
              <div style={{ fontWeight: 600, marginBottom: '4px' }}>Detected Verification Errors:</div>
              <ul style={{ margin: 0, paddingLeft: '18px' }}>
                {outcome.errors.map((err, idx) => (
                  <li key={idx}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Technical Details Accordion Toggle */}
          <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: 'var(--space-4)' }}>
            <button
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
              style={{
                background: 'none',
                border: 'none',
                padding: 0,
                color: 'var(--primary)',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <span>Technical details</span>
              {showTechnicalDetails ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
            </button>

            {showTechnicalDetails && (
              <div
                style={{
                  marginTop: 'var(--space-4)',
                  padding: '16px',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-xs)',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  gap: '12px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Manifest Signature</span>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: outcome.technicalDetails.manifestSignatureValid ? 'var(--success)' : 'var(--danger)' }}>
                    {outcome.technicalDetails.manifestSignatureValid ? 'VALID (ML-DSA-65)' : 'INVALID'}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Merkle Commitment</span>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: outcome.technicalDetails.merkleRootValid ? 'var(--success)' : 'var(--danger)' }}>
                    {outcome.technicalDetails.merkleRootValid ? 'VALID (RFC-6962)' : 'INVALID'}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Content-Addressed Hashes</span>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: outcome.technicalDetails.objectHashesValid ? 'var(--success)' : 'var(--danger)' }}>
                    {outcome.technicalDetails.objectHashesValid ? 'VALID (SHA-256)' : 'INVALID'}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Dependency DAG</span>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: outcome.technicalDetails.dependencyGraphValid ? 'var(--success)' : 'var(--danger)' }}>
                    {outcome.technicalDetails.dependencyGraphValid ? 'VALID (Acyclic)' : 'INVALID'}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Chain of Custody</span>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: outcome.technicalDetails.custodyChainValid ? 'var(--success)' : 'var(--danger)' }}>
                    {outcome.technicalDetails.custodyChainValid ? 'VALID (Hash Chain)' : 'INVALID'}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Temporal Key Invariant</span>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: outcome.technicalDetails.historicalKeysValid ? 'var(--success)' : 'var(--danger)' }}>
                    {outcome.technicalDetails.historicalKeysValid ? 'VALID (Bound)' : 'INVALID'}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState } from 'react';
import { DocumentMetadata, PublicRecipient } from '../../types';
import { X, ShieldCheck, ChevronDown, ChevronRight, Lock, Users, Download, ArrowRight, Trash2, AlertTriangle, Loader2 } from 'lucide-react';

interface MainDocumentDrawerProps {
  document: DocumentMetadata | null;
  recipients: PublicRecipient[];
  onClose: () => void;
  onProtectAndRelease: (documentId: string, recipientIds: string[]) => Promise<void>;
  onDeleteDocument?: (documentId: string) => Promise<void>;
}

export const MainDocumentDrawer: React.FC<MainDocumentDrawerProps> = ({
  document,
  recipients,
  onClose,
  onProtectAndRelease,
  onDeleteDocument
}) => {
  const [selectedRecipients, setSelectedRecipients] = useState<string[]>(() => 
    recipients.slice(0, 3).map(r => r.recipient_id)
  );
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [releaseComplete, setReleaseComplete] = useState<boolean>(false);
  const [showConfirmDelete, setShowConfirmDelete] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  if (!document) return null;

  const toggleRecipient = (id: string) => {
    setSelectedRecipients(prev => 
      prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
    );
  };

  const handleProtect = async () => {
    if (selectedRecipients.length === 0) return;
    setIsProcessing(true);
    try {
      await onProtectAndRelease(document.document_id, selectedRecipients);
      setReleaseComplete(true);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '460px',
        maxWidth: '100vw',
        background: 'var(--main-surface)',
        borderLeft: '1px solid var(--main-border-active)',
        boxShadow: '-8px 0 24px rgba(0,0,0,0.5)',
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        padding: '24px'
      }}
    >
      {/* Drawer Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '16px', borderBottom: '1px solid var(--main-border)' }}>
        <div>
          <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
            Artifact Inspector
          </span>
          <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--main-text-primary)', margin: '4px 0 0 0' }}>
            {document.document_name}
          </h2>
        </div>
        <button onClick={onClose} className="main-btn-ghost" aria-label="Close drawer">
          <X size={18} />
        </button>
      </div>

      {/* Drawer Body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 0', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Core Attributes */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div style={{ padding: '10px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Format</div>
            <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--main-text-primary)', marginTop: '2px' }}>
              {document.mime_type.split('/')[1]?.toUpperCase() || 'DOCUMENT'}
            </div>
          </div>
          <div style={{ padding: '10px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Size</div>
            <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--main-text-primary)', marginTop: '2px' }}>
              {Math.max(1, Math.round(document.size_bytes / 1024))} KB
            </div>
          </div>
        </div>

        {/* Protection & Distribution Workflow */}
        <div style={{ padding: '16px', background: 'var(--main-bg)', borderRadius: '8px', border: '1px solid var(--main-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Lock size={15} style={{ color: 'var(--main-text-primary)' }} />
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
              Protect & Distribute
            </span>
          </div>

          <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '0 0 14px 0', lineHeight: 1.5 }}>
            Seal this document with individual post-quantum key encapsulation and Tardos traceability fingerprints.
          </p>

          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--main-text-secondary)', marginBottom: '8px' }}>
            Select Recipients ({selectedRecipients.length})
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '16px' }}>
            {recipients.map(r => {
              const isSelected = selectedRecipients.includes(r.recipient_id);
              return (
                <label
                  key={r.recipient_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    background: isSelected ? 'var(--main-surface-hover)' : 'transparent',
                    border: `1px solid ${isSelected ? 'var(--main-border-active)' : 'var(--main-border)'}`,
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleRecipient(r.recipient_id)}
                      style={{ accentColor: 'var(--main-text-primary)', cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--main-text-primary)' }}>
                      {r.name}
                    </span>
                  </div>
                  <span className="main-mono" style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>
                    {r.recipient_id}
                  </span>
                </label>
              );
            })}
          </div>

          <button
            onClick={handleProtect}
            disabled={isProcessing || selectedRecipients.length === 0}
            className="main-btn-primary"
            style={{ width: '100%', justifyContent: 'center' }}
          >
            {isProcessing ? 'Applying PQC & Tardos...' : releaseComplete ? 'Re-generate Release' : 'Protect document'}
          </button>

          {releaseComplete && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '10px', color: 'var(--main-jade)', fontSize: '12px', justifyContent: 'center' }}>
              <ShieldCheck size={14} />
              <span>Release created. Individualized packages ready.</span>
            </div>
          )}
        </div>

        {/* Technical Details (Progressive Disclosure) */}
        <div className="main-tech-details">
          <div 
            className="main-tech-summary"
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          >
            <span>Technical details</span>
            {showTechnicalDetails ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </div>

          {showTechnicalDetails && (
            <div className="main-tech-body">
              <div style={{ marginBottom: '8px' }}>
                <span style={{ color: 'var(--main-text-tertiary)' }}>Document ID: </span>
                <span className="main-mono">{document.document_id}</span>
              </div>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ color: 'var(--main-text-tertiary)' }}>Original SHA-256: </span>
                <span className="main-mono" style={{ wordBreak: 'break-all' }}>{document.original_document_hash}</span>
              </div>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ color: 'var(--main-text-tertiary)' }}>Cryptographic Scheme: </span>
                <span>ML-KEM-768 / AES-256-GCM / Tardos (m=2048)</span>
              </div>
              <div>
                <span style={{ color: 'var(--main-text-tertiary)' }}>Storage Plane: </span>
                <span>Content-Addressed Immutable Data Plane</span>
              </div>
            </div>
          )}
        </div>

        {/* Danger Zone: Artifact Removal */}
        {onDeleteDocument && (
          <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--main-border)' }}>
            {!showConfirmDelete ? (
              <button
                type="button"
                onClick={() => setShowConfirmDelete(true)}
                className="main-btn-secondary"
                style={{
                  width: '100%',
                  justifyContent: 'center',
                  borderColor: 'rgba(239, 68, 68, 0.35)',
                  color: 'var(--main-crimson)',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <Trash2 size={13} />
                <span>Remove Artifact from Registry</span>
              </button>
            ) : (
              <div style={{
                padding: '12px',
                borderRadius: '6px',
                background: 'var(--main-crimson-subtle)',
                border: '1px solid var(--main-crimson)',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--main-crimson)', fontSize: '12px', fontWeight: 600 }}>
                  <AlertTriangle size={14} />
                  <span>Confirm Permanent Removal</span>
                </div>
                <p style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', margin: 0, lineHeight: 1.4 }}>
                  Permanently purge this document and its cryptographic master envelope from storage?
                </p>
                <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                  <button
                    type="button"
                    disabled={isDeleting}
                    onClick={() => setShowConfirmDelete(false)}
                    className="main-btn-secondary"
                    style={{ flex: 1, padding: '5px 8px', fontSize: '11px', justifyContent: 'center' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    disabled={isDeleting}
                    onClick={async () => {
                      setIsDeleting(true);
                      try {
                        await onDeleteDocument(document.document_id);
                        onClose();
                      } finally {
                        setIsDeleting(false);
                      }
                    }}
                    style={{
                      flex: 1,
                      padding: '5px 8px',
                      fontSize: '11px',
                      justifyContent: 'center',
                      background: 'var(--main-crimson)',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontWeight: 600
                    }}
                  >
                    {isDeleting ? <Loader2 size={12} className="animate-spin" /> : <Trash2 size={12} />}
                    <span>{isDeleting ? 'Removing...' : 'Confirm Remove'}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};


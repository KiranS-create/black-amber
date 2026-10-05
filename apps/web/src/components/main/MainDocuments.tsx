import React, { useState, useRef } from 'react';
import { DocumentMetadata, PublicRecipient } from '../../types';
import { Upload, FileText, Search, Shield, ChevronRight, Check, Key, Eye, Sparkles, Trash2, AlertTriangle, Loader2 } from 'lucide-react';
import { MainDocumentDrawer } from './MainDocumentDrawer';

interface MainDocumentsProps {
  documents: DocumentMetadata[];
  recipients: PublicRecipient[];
  onUpload: (file: File) => Promise<void>;
  onProtectAndRelease: (documentId: string, recipientIds: string[]) => Promise<void>;
  onDeleteDocument?: (documentId: string) => Promise<void>;
  onOpenDecryptionPortal?: (doc?: DocumentMetadata) => void;
  onOpenComparator?: () => void;
}

export const MainDocuments: React.FC<MainDocumentsProps> = ({
  documents,
  recipients,
  onUpload,
  onProtectAndRelease,
  onDeleteDocument,
  onOpenDecryptionPortal,
  onOpenComparator
}) => {
  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [docToDelete, setDocToDelete] = useState<DocumentMetadata | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleBrowseClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await processUpload(file);
      // Reset input value to permit re-uploading the exact same file
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processUpload(e.dataTransfer.files[0]);
    }
  };

  const processUpload = async (file: File) => {
    setUploadError(null);
    setIsUploading(true);
    try {
      await onUpload(file);
    } catch (err: any) {
      setUploadError(err?.message || 'Failed to upload document.');
    } finally {
      setIsUploading(false);
    }
  };

  const filteredDocs = documents.filter(d => 
    d.document_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (d.original_document_hash && d.original_document_hash.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="main-title">Document Registry</h1>
          <p className="main-subtitle">
            Content-addressed forensic repository. Documents are sealed with post-quantum envelopes prior to distribution.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={handleBrowseClick}
            disabled={isUploading}
            className="main-btn-primary"
            style={{ fontSize: '12px' }}
          >
            <Upload size={14} />
            <span>{isUploading ? 'Importing...' : 'Import Document'}</span>
          </button>
        </div>
      </div>


      {/* Import Dropzone */}
      <div
        className={`main-dropzone ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleBrowseClick}
      >
        {/* Hidden Native File Input with React Ref */}
        <input
          ref={fileInputRef}
          type="file"
          id="main-file-upload-input"
          aria-label="Upload document file"
          style={{ display: 'none' }}
          onChange={handleFileChange}
          accept=".pdf,.docx,.pptx,.xlsx,.png,.jpeg,.jpg,.txt,.csv,.rtf,.zip"
        />

        <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'var(--main-surface-elevated)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '10px' }}>
          <Upload size={16} style={{ color: 'var(--main-text-secondary)' }} />
        </div>

        <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--main-text-primary)' }}>
          Drop a document here or browse
        </div>

        <p style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', margin: '4px 0 14px 0' }}>
          PDF · DOCX · PPTX · XLSX · PNG · JPEG
        </p>

        <button
          type="button"
          onClick={handleBrowseClick}
          disabled={isUploading}
          className="main-btn-secondary"
          style={{ fontSize: '12px', padding: '6px 14px' }}
        >
          Browse Files
        </button>

        {uploadError && (
          <div style={{ marginTop: '12px', color: 'var(--main-crimson)', fontSize: '12px' }}>
            {uploadError}
          </div>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
        <div style={{ position: 'relative', width: '320px' }}>
          <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--main-text-tertiary)' }} />
          <input
            type="text"
            placeholder="Search documents by name or hash..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              background: 'var(--main-surface)',
              border: '1px solid var(--main-border)',
              borderRadius: '9999px',
              padding: '8px 14px 8px 34px',
              color: 'var(--main-text-primary)',
              fontSize: '12.5px',
              outline: 'none',
              boxShadow: 'inset 0 1px 2px rgba(0, 0, 0, 0.06)',
              transition: 'border-color 0.15s ease, box-shadow 0.15s ease'
            }}
          />
        </div>
        <div style={{ fontSize: '12px', color: 'var(--main-text-secondary)' }}>
          Showing {filteredDocs.length} of {documents.length} artifacts
        </div>
      </div>

      {/* Document Table */}
      <div className="main-card" style={{ padding: 0, overflow: 'hidden' }}>
        {filteredDocs.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--main-text-secondary)', fontSize: '13px' }}>
            {searchTerm ? 'No documents match the search criteria.' : 'No protected artifacts yet. Import a document above.'}
          </div>
        ) : (
          <table className="main-table">
            <thead>
              <tr>
                <th>Document Name</th>
                <th>Format</th>
                <th>Content SHA-256</th>
                <th>Created</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.map(doc => (
                <tr 
                  key={doc.document_id}
                  onClick={() => setSelectedDoc(doc)}
                  style={{ cursor: 'pointer' }}
                >
                  <td style={{ fontWeight: 500 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <FileText size={14} style={{ color: 'var(--main-text-secondary)' }} />
                      <span>{doc.document_name}</span>
                    </div>
                  </td>
                  <td>
                    <span style={{ fontSize: '11px', color: 'var(--main-text-secondary)' }}>
                      {doc.mime_type.split('/')[1]?.toUpperCase() || 'DOC'}
                    </span>
                  </td>
                  <td>
                    <span className="main-mono" style={{ fontSize: '11px', color: 'var(--main-text-secondary)' }}>
                      {doc.original_document_hash ? doc.original_document_hash.substring(0, 16) + '...' : doc.document_id}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '12px', color: 'var(--main-text-secondary)' }}>
                      {new Date(doc.created_at).toLocaleDateString()}
                    </span>
                  </td>
                  <td>
                    <span className="main-badge main-badge-verified">
                      <Check size={10} /> Sealed
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '6px' }}>
                      {onOpenDecryptionPortal && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenDecryptionPortal(doc);
                          }}
                          className="main-btn-secondary"
                          style={{ padding: '3px 8px', fontSize: '11px', borderColor: 'rgba(59, 130, 246, 0.4)' }}
                        >
                          <Key size={11} style={{ color: '#60A5FA' }} /> Decrypt Copy
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedDoc(doc);
                        }}
                        className="main-btn-ghost"
                        style={{ padding: '3px 8px', fontSize: '11px' }}
                      >
                        Inspect <ChevronRight size={12} />
                      </button>
                      {onDeleteDocument && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setDocToDelete(doc);
                          }}
                          className="main-btn-ghost"
                          title={`Remove ${doc.document_name} from registry`}
                          style={{
                            padding: '3px 8px',
                            fontSize: '11px',
                            color: 'var(--main-crimson)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                        >
                          <Trash2 size={11} />
                          <span>Remove</span>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Document Detail Drawer */}
      {selectedDoc && (
        <MainDocumentDrawer
          document={selectedDoc}
          recipients={recipients}
          onClose={() => setSelectedDoc(null)}
          onProtectAndRelease={onProtectAndRelease}
          onDeleteDocument={onDeleteDocument}
        />
      )}

      {/* Document Removal Confirmation Modal */}
      {docToDelete && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.65)',
          backdropFilter: 'blur(6px)',
          WebkitBackdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '16px'
        }}>
          <div style={{
            background: 'var(--main-surface)',
            border: '1px solid var(--main-border-active)',
            borderRadius: '12px',
            width: '100%',
            maxWidth: '460px',
            padding: '24px',
            boxShadow: '0 24px 48px rgba(0, 0, 0, 0.45)',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '38px',
                height: '38px',
                borderRadius: '50%',
                background: 'var(--main-crimson-subtle)',
                color: 'var(--main-crimson)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <Trash2 size={18} />
              </div>
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--main-text-primary)', margin: 0 }}>
                  Remove Artifact from Registry
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--main-text-tertiary)', margin: '2px 0 0 0' }}>
                  Permanent purge from content-addressed storage
                </p>
              </div>
            </div>

            <div style={{
              padding: '12px',
              borderRadius: '8px',
              background: 'var(--main-bg)',
              border: '1px solid var(--main-border)',
              fontSize: '12px'
            }}>
              <div style={{ fontWeight: 600, color: 'var(--main-text-primary)' }}>
                {docToDelete.document_name}
              </div>
              <div className="main-mono" style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '4px', wordBreak: 'break-all' }}>
                SHA-256: {docToDelete.original_document_hash || docToDelete.document_id}
              </div>
            </div>

            <p style={{ fontSize: '12.5px', color: 'var(--main-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Are you sure you want to permanently delete this master document from the registry? Any pending local operations will be cancelled.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '6px' }}>
              <button
                type="button"
                disabled={isDeleting}
                onClick={() => setDocToDelete(null)}
                className="main-btn-secondary"
                style={{ padding: '7px 14px', fontSize: '12px' }}
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isDeleting}
                onClick={async () => {
                  if (!onDeleteDocument || !docToDelete) return;
                  setIsDeleting(true);
                  try {
                    await onDeleteDocument(docToDelete.document_id);
                    if (selectedDoc?.document_id === docToDelete.document_id) {
                      setSelectedDoc(null);
                    }
                    setDocToDelete(null);
                  } finally {
                    setIsDeleting(false);
                  }
                }}
                style={{
                  padding: '7px 16px',
                  fontSize: '12px',
                  fontWeight: 600,
                  background: 'var(--main-crimson)',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {isDeleting ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
                <span>{isDeleting ? 'Removing...' : 'Confirm Remove'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

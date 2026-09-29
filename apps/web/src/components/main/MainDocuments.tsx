import React, { useState, useRef } from 'react';
import { DocumentMetadata, PublicRecipient } from '../../types';
import { Upload, FileText, Search, Shield, ChevronRight, Check } from 'lucide-react';
import { MainDocumentDrawer } from './MainDocumentDrawer';

interface MainDocumentsProps {
  documents: DocumentMetadata[];
  recipients: PublicRecipient[];
  onUpload: (file: File) => Promise<void>;
  onProtectAndRelease: (documentId: string, recipientIds: string[]) => Promise<void>;
}

export const MainDocuments: React.FC<MainDocumentsProps> = ({
  documents,
  recipients,
  onUpload,
  onProtectAndRelease
}) => {
  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [uploadError, setUploadError] = useState<string | null>(null);
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
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 className="main-title">Document Registry</h1>
          <p className="main-subtitle">
            Content-addressed forensic repository. Documents are sealed with post-quantum envelopes prior to distribution.
          </p>
        </div>

        <button
          onClick={handleBrowseClick}
          disabled={isUploading}
          className="main-btn-primary"
        >
          <Upload size={14} />
          <span>{isUploading ? 'Importing...' : 'Import artifact'}</span>
        </button>
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
              borderRadius: '6px',
              padding: '8px 12px 8px 32px',
              color: 'var(--main-text-primary)',
              fontSize: '12px',
              outline: 'none'
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
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedDoc(doc);
                      }}
                      className="main-btn-ghost"
                      style={{ padding: '4px 8px', fontSize: '12px' }}
                    >
                      Inspect <ChevronRight size={12} />
                    </button>
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
        />
      )}
    </div>
  );
};

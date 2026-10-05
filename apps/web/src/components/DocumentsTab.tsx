import React, { useState, useRef } from 'react';
import { 
  FileText, 
  Search, 
  UploadCloud, 
  Copy, 
  Check, 
  Package, 
  ArrowRight,
  ChevronDown,
  ChevronUp,
  FileCheck2,
  FileSpreadsheet,
  FileImage,
  Layers,
  AlertCircle,
  Loader2,
  Trash2
} from 'lucide-react';
import { DocumentMetadata, DocumentRelease } from '../types';
import { StatusBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';
import { EmptyState } from './common/EmptyState';

interface DocumentsTabProps {
  documents: DocumentMetadata[];
  releases: DocumentRelease[];
  onUploadDocument: (file: File, name?: string) => Promise<DocumentMetadata>;
  onDeleteDocument?: (documentId: string) => Promise<void>;
  setActiveTab: (tab: any) => void;
  onSelectForRelease?: (docId: string) => void;
}

type UploadLifecycleState = 'IDLE' | 'VALIDATING' | 'UPLOADING' | 'PROCESSING' | 'READY' | 'ERROR';

export const DocumentsTab: React.FC<DocumentsTabProps> = ({
  documents,
  releases,
  onUploadDocument,
  onDeleteDocument,
  setActiveTab,
  onSelectForRelease
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [classificationFilter, setClassificationFilter] = useState<string>('ALL');
  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);
  const [uploadState, setUploadState] = useState<UploadLifecycleState>('IDLE');
  const [uploadProgressText, setUploadProgressText] = useState<string>('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);
  const [showTechDetails, setShowTechDetails] = useState(false);
  const [docToDelete, setDocToDelete] = useState<DocumentMetadata | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const SUPPORTED_FORMATS = [
    { ext: 'PDF', mime: 'application/pdf', mode: 'Rendered Carrier' },
    { ext: 'DOCX', mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', mode: 'Rendered Carrier' },
    { ext: 'PPTX', mime: 'application/vnd.openxmlformats-officedocument.presentationml.presentation', mode: 'Rendered Carrier' },
    { ext: 'XLSX', mime: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', mode: 'Rendered Carrier' },
    { ext: 'PNG', mime: 'image/png', mode: 'Direct Carrier' },
    { ext: 'JPEG', mime: 'image/jpeg', mode: 'Direct Carrier' },
    { ext: 'TXT', mime: 'text/plain', mode: 'Rendered Carrier' },
    { ext: 'CSV', mime: 'text/csv', mode: 'Rendered Carrier' },
    { ext: 'RTF', mime: 'application/rtf', mode: 'Rendered Carrier' },
    { ext: 'ODT', mime: 'application/vnd.oasis.opendocument.text', mode: 'Rendered Carrier' },
    { ext: 'ZIP', mime: 'application/zip', mode: 'Container' },
    { ext: 'JSON', mime: 'application/json', mode: 'Structured Data' }
  ];

  const filteredDocs = documents.filter(doc => {
    const matchesSearch = 
      doc.document_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.document_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.original_document_hash.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (doc.owner_name && doc.owner_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (doc.owner_department && doc.owner_department.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesClassification = 
      classificationFilter === 'ALL' || 
      (doc.classification && doc.classification === classificationFilter);

    return matchesSearch && matchesClassification;
  });

  const getFormatIcon = (filename: string, mime?: string) => {
    const lower = filename.toLowerCase();
    if (lower.endsWith('.pdf') || mime?.includes('pdf')) return <FileText size={14} style={{ color: 'var(--primary)', flexShrink: 0 }} />;
    if (lower.endsWith('.xlsx') || lower.endsWith('.xls') || mime?.includes('spreadsheet')) return <FileSpreadsheet size={14} style={{ color: 'var(--success)', flexShrink: 0 }} />;
    if (lower.endsWith('.pptx') || lower.endsWith('.ppt') || mime?.includes('presentation')) return <Layers size={14} style={{ color: 'var(--warning)', flexShrink: 0 }} />;
    if (lower.endsWith('.png') || lower.endsWith('.jpg') || lower.endsWith('.jpeg') || mime?.includes('image')) return <FileImage size={14} style={{ color: 'var(--info)', flexShrink: 0 }} />;
    return <FileText size={14} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />;
  };

  const getFormatBadge = (filename: string, mime?: string) => {
    const lower = filename.toLowerCase();
    if (lower.endsWith('.pdf') || mime?.includes('pdf')) return 'PDF';
    if (lower.endsWith('.docx') || lower.endsWith('.doc')) return 'DOCX';
    if (lower.endsWith('.pptx') || lower.endsWith('.ppt')) return 'PPTX';
    if (lower.endsWith('.xlsx') || lower.endsWith('.xls')) return 'XLSX';
    if (lower.endsWith('.png')) return 'PNG';
    if (lower.endsWith('.jpg') || lower.endsWith('.jpeg')) return 'JPEG';
    if (lower.endsWith('.txt')) return 'TXT';
    if (lower.endsWith('.csv')) return 'CSV';
    if (lower.endsWith('.rtf')) return 'RTF';
    if (lower.endsWith('.odt')) return 'ODT';
    if (lower.endsWith('.ods')) return 'ODS';
    if (lower.endsWith('.odp')) return 'ODP';
    if (lower.endsWith('.zip')) return 'ZIP';
    if (lower.endsWith('.json')) return 'JSON';
    return 'CARRIER';
  };

  const processSelectedFile = async (file: File) => {
    const lower = file.name.toLowerCase();
    const isSupported = 
      lower.endsWith('.pdf') || 
      lower.endsWith('.docx') || 
      lower.endsWith('.pptx') || 
      lower.endsWith('.xlsx') || 
      lower.endsWith('.png') || 
      lower.endsWith('.jpg') || 
      lower.endsWith('.jpeg') ||
      lower.endsWith('.txt') ||
      lower.endsWith('.csv') ||
      lower.endsWith('.rtf') ||
      lower.endsWith('.odt') ||
      lower.endsWith('.ods') ||
      lower.endsWith('.odp') ||
      lower.endsWith('.zip') ||
      lower.endsWith('.json');

    if (!isSupported) {
      setUploadState('ERROR');
      setUploadError(`Unsupported file format (${file.name}). Supported formats: PDF, DOCX, PPTX, XLSX, PNG, JPEG, TXT, CSV, RTF, ODT, ZIP, JSON.`);
      return;
    }

    setUploadError(null);
    setUploadState('VALIDATING');
    setUploadProgressText(`Validating ${file.name} against format registry…`);

    try {
      await new Promise(r => setTimeout(r, 200));
      setUploadState('UPLOADING');
      setUploadProgressText(`Uploading artifact (${formatBytes(file.size)})…`);

      await new Promise(r => setTimeout(r, 150));
      setUploadState('PROCESSING');
      setUploadProgressText(`Processing ${getFormatBadge(file.name)} carrier & computing SHA-256…`);

      const newDoc = await onUploadDocument(file, file.name);
      setUploadState('READY');
      setUploadProgressText(`Artifact ready. ${file.name} successfully registered.`);
      setSelectedDoc(newDoc);

      setTimeout(() => {
        setUploadState('IDLE');
        setUploadProgressText('');
      }, 3000);
    } catch (err: any) {
      setUploadState('ERROR');
      setUploadError(err?.message || 'Upload failed. The artifact could not be processed.');
    }
  };

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await processSelectedFile(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      await processSelectedFile(file);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const getClassificationVariant = (cls?: string): 'danger' | 'warning' | 'info' | 'neutral' => {
    switch (cls) {
      case 'TOP_SECRET': return 'danger';
      case 'SECRET': return 'warning';
      case 'CONFIDENTIAL': return 'info';
      default: return 'neutral';
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600, color: 'var(--text)', letterSpacing: '-0.015em' }}>
            Document Registry
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '640px' }}>
            Content-addressed forensic repository. Cryptographic envelopes seal document payloads prior to multi-recipient distribution.
          </p>
        </div>

        <button
          onClick={() => fileInputRef.current?.click()}
          className="btn-primary"
          style={{ cursor: 'pointer' }}
          disabled={uploadState === 'UPLOADING' || uploadState === 'PROCESSING'}
        >
          {uploadState === 'UPLOADING' || uploadState === 'PROCESSING' ? (
            <>
              <Loader2 size={15} className="animate-spin" />
              <span>Importing artifact…</span>
            </>
          ) : (
            <>
              <UploadCloud size={15} />
              <span>Import artifact</span>
            </>
          )}
        </button>
        <input 
          ref={fileInputRef}
          id="doc-upload-input" 
          type="file" 
          onChange={handleFileInputChange} 
          style={{ display: 'none' }} 
          accept=".pdf,.docx,.pptx,.xlsx,.png,.jpg,.jpeg,.txt,.csv,.rtf,.odt,.ods,.odp,.zip,.json" 
        />
      </div>

      {/* Forensic Native Upload Dropzone (Dual Mode: Primary [ Browse Files ] + Drag & Drop) */}
      <div
        className={`forensic-dropzone ${isDragActive ? 'drag-active' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{
          padding: 'var(--space-6)',
          backgroundColor: 'var(--surface-subtle)',
          border: isDragActive ? '1px dashed var(--primary)' : '1px dashed var(--border-strong)',
          borderRadius: 'var(--radius-md)',
          textAlign: 'center',
          position: 'relative'
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: 'var(--radius-xs)',
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary)'
            }}
          >
            <UploadCloud size={20} />
          </div>

          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>
            Import artifact
          </div>

          <p style={{ margin: 0, fontSize: '12.5px', color: 'var(--text-secondary)' }}>
            Drop a document here or click to browse your workstation
          </p>

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="btn-secondary"
            style={{ marginTop: '4px', cursor: 'pointer' }}
          >
            <span>Browse Files</span>
          </button>

          {/* Supported Formats Strip */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', flexWrap: 'wrap', justifyContent: 'center' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Supported formats:
            </span>
            {SUPPORTED_FORMATS.map(fmt => (
              <span
                key={fmt.ext}
                style={{
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  padding: '1px 6px',
                  borderRadius: '3px',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-secondary)'
                }}
              >
                {fmt.ext}
              </span>
            ))}
          </div>

          {/* Upload Status / Progression Indicator */}
          {uploadState !== 'IDLE' && (
            <div
              style={{
                marginTop: '10px',
                padding: '8px 14px',
                borderRadius: 'var(--radius-xs)',
                backgroundColor: uploadState === 'ERROR' ? 'var(--danger-subtle)' : (uploadState === 'READY' ? 'var(--success-subtle)' : 'var(--primary-subtle)'),
                border: `1px solid ${uploadState === 'ERROR' ? 'var(--danger-border)' : (uploadState === 'READY' ? 'var(--success-border)' : 'var(--primary-border)')}`,
                fontSize: '12px',
                color: uploadState === 'ERROR' ? 'var(--danger-text)' : (uploadState === 'READY' ? 'var(--success-text)' : 'var(--primary-text)'),
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              {uploadState === 'UPLOADING' || uploadState === 'PROCESSING' || uploadState === 'VALIDATING' ? (
                <Loader2 size={13} className="animate-spin" />
              ) : uploadState === 'READY' ? (
                <Check size={13} />
              ) : (
                <AlertCircle size={13} />
              )}
              <span>{uploadProgressText || uploadError}</span>
            </div>
          )}
        </div>
      </div>

      {documents.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="Workspace ready. No protected artifacts yet."
          description="Import a document to begin post-quantum protection, recipient binding, and multi-channel distribution."
          primaryAction={{
            label: uploadState === 'UPLOADING' ? "Importing artifact…" : "Import artifact",
            onClick: () => fileInputRef.current?.click()
          }}
        />
      ) : (
        <>
          {/* Filter and Search Controls */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px'
            }}
          >
            <div style={{ position: 'relative', width: '380px', maxWidth: '100%' }}>
              <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
              <input
                type="text"
                placeholder="Search documents by title, hash, or department…"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="form-input"
                style={{ paddingLeft: '34px', height: '36px' }}
              />
            </div>

            {/* Classification Filter */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: 'var(--surface-subtle)', padding: '3px', borderRadius: '4px', border: '1px solid var(--border)' }}>
              {[
                { id: 'ALL', label: 'All tiers' },
                { id: 'TOP_SECRET', label: 'Top Secret' },
                { id: 'SECRET', label: 'Secret' },
                { id: 'CONFIDENTIAL', label: 'Confidential' }
              ].map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setClassificationFilter(cat.id)}
                  style={{
                    height: '28px',
                    padding: '0 10px',
                    borderRadius: '3px',
                    border: 'none',
                    backgroundColor: classificationFilter === cat.id ? 'var(--surface-elevated)' : 'transparent',
                    color: classificationFilter === cat.id ? 'var(--text)' : 'var(--text-secondary)',
                    fontSize: '11.5px',
                    fontWeight: classificationFilter === cat.id ? 600 : 400,
                    cursor: 'pointer',
                    transition: 'background var(--transition-fast)'
                  }}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Documents Table */}
          <div className="workstation-card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ overflowX: 'auto' }}>
              <table className="evidence-table">
                <thead>
                  <tr>
                    <th>Artifact</th>
                    <th>Format</th>
                    <th>Size</th>
                    <th>Classification</th>
                    <th>Custodian</th>
                    <th>SHA-256 Digest</th>
                    <th>Releases</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredDocs.length === 0 ? (
                    <tr>
                      <td colSpan={8} style={{ padding: '40px 16px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                        <FileText size={28} style={{ margin: '0 auto 8px', opacity: 0.4 }} />
                        <div style={{ fontWeight: 500, fontSize: '13px', color: 'var(--text-secondary)' }}>No matching documents found</div>
                        <div style={{ fontSize: '12px', marginTop: '2px' }}>Adjust search query or import a new artifact above.</div>
                      </td>
                    </tr>
                  ) : (
                    filteredDocs.map((doc, idx) => {
                      const associatedReleases = releases.filter(r => r.document_id === doc.document_id || r.document_name === doc.document_name);
                      const isSelected = selectedDoc?.document_id === doc.document_id;
                      const badge = getFormatBadge(doc.document_name, doc.mime_type);
                      return (
                        <tr
                          key={doc.document_id || idx}
                          onClick={() => setSelectedDoc(doc)}
                          style={{
                            backgroundColor: isSelected ? 'rgba(76, 154, 154, 0.08)' : undefined,
                            cursor: 'pointer'
                          }}
                        >
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              {getFormatIcon(doc.document_name, doc.mime_type)}
                              <span style={{ fontWeight: 500, color: 'var(--text)', fontSize: '13px' }}>
                                {doc.document_name}
                              </span>
                            </div>
                          </td>

                          <td>
                            <span
                              style={{
                                fontSize: '10.5px',
                                fontFamily: 'var(--font-mono)',
                                padding: '1px 5px',
                                borderRadius: '3px',
                                backgroundColor: 'var(--surface-elevated)',
                                border: '1px solid var(--border)',
                                color: 'var(--text-secondary)'
                              }}
                            >
                              {badge}
                            </span>
                          </td>

                          <td style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                            {formatBytes(doc.size_bytes)}
                          </td>

                          <td>
                            <StatusBadge
                              label={doc.classification ? doc.classification.replace('_', ' ') : 'Top Secret'}
                              variant={getClassificationVariant(doc.classification)}
                              size="xs"
                            />
                          </td>

                          <td style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                            {doc.owner_name ? (
                              <span>{doc.owner_name} {doc.owner_department && <span style={{ color: 'var(--text-tertiary)' }}>({doc.owner_department})</span>}</span>
                            ) : (
                              <span style={{ color: 'var(--text-tertiary)' }}>—</span>
                            )}
                          </td>

                          <td>
                            <code style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)' }}>
                              {doc.original_document_hash ? doc.original_document_hash.substring(0, 16) + '…' : '—'}
                            </code>
                          </td>

                          <td style={{ fontSize: '12px', color: associatedReleases.length > 0 ? 'var(--text)' : 'var(--text-tertiary)' }}>
                            {associatedReleases.length} {associatedReleases.length === 1 ? 'release' : 'releases'}
                          </td>

                          <td style={{ textAlign: 'right' }}>
                            <div style={{ display: 'inline-flex', gap: '6px' }}>
                              <button
                                onClick={e => {
                                  e.stopPropagation();
                                  setSelectedDoc(doc);
                                }}
                                className="btn-secondary"
                                style={{ padding: '4px 9px', fontSize: '11px' }}
                              >
                                Inspect
                              </button>

                              <button
                                onClick={e => {
                                  e.stopPropagation();
                                  if (onSelectForRelease) onSelectForRelease(doc.document_id);
                                  setActiveTab('releases');
                                }}
                                className="btn-secondary"
                                style={{ padding: '4px 9px', fontSize: '11px' }}
                                title="Authorize encrypted release"
                              >
                                Release
                              </button>

                              {onDeleteDocument && (
                                <button
                                  onClick={e => {
                                    e.stopPropagation();
                                    setDocToDelete(doc);
                                  }}
                                  className="btn-ghost"
                                  style={{ padding: '4px 8px', fontSize: '11px', color: 'var(--danger, #EF4444)' }}
                                  title={`Remove ${doc.document_name} from registry`}
                                >
                                  <Trash2 size={12} />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Document Detail & Forensic Inspector Drawer */}
      <Drawer
        isOpen={!!selectedDoc}
        onClose={() => setSelectedDoc(null)}
        title={selectedDoc?.document_name || 'Classified Document'}
        subtitle={`Asset ID: ${selectedDoc?.document_id || ''}`}
        width="480px"
      >
        {selectedDoc && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Digest Panel */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)', fontWeight: 600 }}>
                  SHA-256 Master Digest
                </span>
                <button
                  onClick={() => handleCopy(selectedDoc.original_document_hash)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: copiedHash ? 'var(--success)' : 'var(--text-tertiary)',
                    fontSize: '11px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  {copiedHash ? <Check size={12} /> : <Copy size={12} />}
                  <span>{copiedHash ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <div
                style={{
                  padding: '10px 12px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: 'var(--text-secondary)',
                  wordBreak: 'break-all',
                  lineHeight: 1.5
                }}
              >
                {selectedDoc.original_document_hash}
              </div>
            </div>

            {/* Document Attributes */}
            <div>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: '10px' }}>
                Document Attributes
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '130px 1fr', gap: '10px 16px', fontSize: '12.5px' }}>
                <span style={{ color: 'var(--text-tertiary)' }}>Classification</span>
                <div>
                  <StatusBadge
                    label={selectedDoc.classification ? selectedDoc.classification.replace('_', ' ') : 'Top Secret'}
                    variant={getClassificationVariant(selectedDoc.classification)}
                    size="xs"
                  />
                </div>

                <span style={{ color: 'var(--text-tertiary)' }}>Format Adapter</span>
                <span style={{ color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
                  {getFormatBadge(selectedDoc.document_name, selectedDoc.mime_type)} ({selectedDoc.mime_type?.includes('image') ? 'Direct Carrier' : 'Rendered Carrier'})
                </span>

                <span style={{ color: 'var(--text-tertiary)' }}>Custodian</span>
                <span style={{ color: 'var(--text)' }}>
                  {selectedDoc.owner_name ? `${selectedDoc.owner_name} (${selectedDoc.owner_department || 'Operations'})` : '—'}
                </span>

                <span style={{ color: 'var(--text-tertiary)' }}>File size</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                  {formatBytes(selectedDoc.size_bytes)}
                </span>

                <span style={{ color: 'var(--text-tertiary)' }}>Registered</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                  {selectedDoc.created_at ? new Date(selectedDoc.created_at).toISOString() : 'Recent'}
                </span>
              </div>
            </div>

            {/* Progressive Disclosure: Technical Details */}
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '14px' }}>
              <button
                type="button"
                onClick={() => setShowTechDetails(!showTechDetails)}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  color: 'var(--primary)',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <span>Technical details</span>
                {showTechDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>

              {showTechDetails && (
                <div
                  style={{
                    marginTop: '10px',
                    padding: '12px',
                    backgroundColor: 'var(--surface-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '11.5px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>KEM Scheme:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>NIST FIPS 203 (ML-KEM-768)</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Signature Scheme:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>NIST FIPS 204 (ML-DSA-65)</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Payload Cipher:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>AES-256-GCM (AEAD)</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Watermarking Engine:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>2D DSSS + RS(255, 223) ECC</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Audit Ledger Anchor:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>RFC 6962 SHA-256 Merkle Chain</span>
                  </div>
                </div>
              )}
            </div>

            {/* Release Action */}
            <button
              onClick={() => {
                if (onSelectForRelease) onSelectForRelease(selectedDoc.document_id);
                setActiveTab('releases');
                setSelectedDoc(null);
              }}
              className="btn-primary"
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                marginTop: '10px'
              }}
            >
              <Package size={15} />
              <span>Create release for document</span>
            </button>

            {/* Remove Action */}
            {onDeleteDocument && (
              <button
                onClick={() => setDocToDelete(selectedDoc)}
                className="btn-secondary"
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  marginTop: '8px',
                  color: 'var(--danger, #EF4444)',
                  borderColor: 'rgba(239, 68, 68, 0.3)'
                }}
              >
                <Trash2 size={14} />
                <span>Remove artifact from registry</span>
              </button>
            )}
          </div>
        )}
      </Drawer>

      {/* Delete Confirmation Modal */}
      {docToDelete && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.65)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '16px'
        }}>
          <div style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md, 8px)',
            width: '100%',
            maxWidth: '440px',
            padding: '24px',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: 'rgba(239, 68, 68, 0.15)',
                color: 'var(--danger, #EF4444)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <Trash2 size={18} />
              </div>
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text)', margin: 0 }}>
                  Remove Document from Registry
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', margin: '2px 0 0 0' }}>
                  Permanent purge from content-addressed storage
                </p>
              </div>
            </div>

            <div style={{
              padding: '12px',
              borderRadius: '4px',
              background: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              fontSize: '12px'
            }}>
              <div style={{ fontWeight: 600, color: 'var(--text)' }}>
                {docToDelete.document_name}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px', wordBreak: 'break-all' }}>
                SHA-256: {docToDelete.original_document_hash || docToDelete.document_id}
              </div>
            </div>

            <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Are you sure you want to remove this document from the registry? This will permanently delete the sealed master payload from storage.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '4px' }}>
              <button
                type="button"
                disabled={isDeleting}
                onClick={() => setDocToDelete(null)}
                className="btn-secondary"
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
                  background: 'var(--danger, #EF4444)',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '4px',
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

import React, { useState } from 'react';
import { 
  FileText, 
  Search, 
  UploadCloud, 
  Copy, 
  Check, 
  Package, 
  ArrowRight,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { DocumentMetadata, DocumentRelease } from '../types';
import { StatusBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';
import { EmptyState } from './common/EmptyState';

interface DocumentsTabProps {
  documents: DocumentMetadata[];
  releases: DocumentRelease[];
  onUploadDocument: (file: File, name?: string) => Promise<DocumentMetadata>;
  setActiveTab: (tab: any) => void;
  onSelectForRelease?: (docId: string) => void;
}

export const DocumentsTab: React.FC<DocumentsTabProps> = ({
  documents,
  releases,
  onUploadDocument,
  setActiveTab,
  onSelectForRelease
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [classificationFilter, setClassificationFilter] = useState<string>('ALL');
  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);
  const [uploading, setUploading] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);
  const [showTechDetails, setShowTechDetails] = useState(false);

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

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const newDoc = await onUploadDocument(file, file.name);
      setSelectedDoc(newDoc);
    } catch (err) {
      console.error('Document upload failed:', err);
    } finally {
      setUploading(false);
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
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600, color: 'var(--text-ivory)', letterSpacing: '-0.01em' }}>
            Protected Document Registry
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-slate)', maxWidth: '640px' }}>
            Content-addressed repository for classified assets. Cryptographic envelopes seal document payloads prior to multi-recipient distribution.
          </p>
        </div>

        <label
          className="btn-primary"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer'
          }}
        >
          <UploadCloud size={15} />
          <span>{uploading ? 'Importing artifact…' : 'Import artifact'}</span>
          <input id="doc-upload-input" type="file" onChange={handleFileUpload} style={{ display: 'none' }} accept=".pdf,.doc,.docx,.txt" />
        </label>
      </div>

      {documents.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No documents yet"
          description="Import a document to begin post-quantum protection and distribution."
          primaryAction={{
            label: uploading ? "Importing artifact…" : "Import artifact",
            onClick: () => document.getElementById('doc-upload-input')?.click()
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
            <div style={{ position: 'relative', width: '360px', maxWidth: '100%' }}>
              <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-graphite)' }} />
              <input
                type="text"
                placeholder="Search by title, SHA-256 digest, or department…"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  height: '36px',
                  paddingLeft: '34px',
                  paddingRight: '12px',
                  borderRadius: '4px',
                  border: '1px solid var(--border-subtle)',
                  backgroundColor: 'var(--bg-elevated)',
                  color: 'var(--text-ivory)',
                  fontSize: '12px',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            {/* Classification Filter Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: 'var(--bg-elevated)', padding: '3px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
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
                    backgroundColor: classificationFilter === cat.id ? 'var(--bg-surface)' : 'transparent',
                    color: classificationFilter === cat.id ? 'var(--text-ivory)' : 'var(--text-slate)',
                    fontSize: '11px',
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
                <th>Document</th>
                <th>Classification</th>
                <th>Owner / Department</th>
                <th>SHA-256 Digest</th>
                <th>Size</th>
                <th>Releases</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '40px 16px', textAlign: 'center', color: 'var(--text-graphite)' }}>
                    <FileText size={28} style={{ margin: '0 auto 8px', opacity: 0.4 }} />
                    <div style={{ fontWeight: 500, fontSize: '13px', color: 'var(--text-slate)' }}>No documents found</div>
                    <div style={{ fontSize: '12px', marginTop: '2px' }}>Adjust search query or register a new document above.</div>
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc, idx) => {
                  const associatedReleases = releases.filter(r => r.document_id === doc.document_id || r.document_name === doc.document_name);
                  const isSelected = selectedDoc?.document_id === doc.document_id;
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
                          <FileText size={14} style={{ color: 'var(--petrol)', flexShrink: 0 }} />
                          <span style={{ fontWeight: 500, color: 'var(--text-ivory)', fontSize: '13px' }}>
                            {doc.document_name}
                          </span>
                        </div>
                      </td>

                      <td>
                        <StatusBadge
                          label={doc.classification ? doc.classification.replace('_', ' ') : 'Top Secret'}
                          variant={getClassificationVariant(doc.classification)}
                          size="xs"
                        />
                      </td>

                      <td style={{ color: 'var(--text-slate)', fontSize: '12px' }}>
                        {doc.owner_name || 'Sarah Jenkins'} <span style={{ color: 'var(--text-graphite)' }}>({doc.owner_department || 'Cyber Defense'})</span>
                      </td>

                      <td>
                        <code style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-slate)' }}>
                          {doc.original_document_hash.substring(0, 16)}…
                        </code>
                      </td>

                      <td style={{ color: 'var(--text-graphite)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                        {formatBytes(doc.size_bytes)}
                      </td>

                      <td style={{ fontSize: '12px', color: associatedReleases.length > 0 ? 'var(--text-ivory)' : 'var(--text-graphite)' }}>
                        {associatedReleases.length} {associatedReleases.length === 1 ? 'release' : 'releases'}
                      </td>

                      <td style={{ textAlign: 'right' }}>
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            setSelectedDoc(doc);
                          }}
                          style={{
                            padding: '4px 10px',
                            borderRadius: '4px',
                            backgroundColor: 'var(--bg-elevated)',
                            border: '1px solid var(--border-subtle)',
                            color: 'var(--text-slate)',
                            fontSize: '11px',
                            cursor: 'pointer'
                          }}
                          onMouseEnter={e => {
                            e.currentTarget.style.color = 'var(--text-ivory)';
                            e.currentTarget.style.borderColor = 'var(--border-strong)';
                          }}
                          onMouseLeave={e => {
                            e.currentTarget.style.color = 'var(--text-slate)';
                            e.currentTarget.style.borderColor = 'var(--border-subtle)';
                          }}
                        >
                          Inspect
                        </button>
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

      {/* Document Detail Drawer */}
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
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>
                  SHA-256 Master Digest
                </span>
                <button
                  onClick={() => handleCopy(selectedDoc.original_document_hash)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: copiedHash ? 'var(--jade)' : 'var(--text-graphite)',
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
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: 'var(--text-slate)',
                  wordBreak: 'break-all',
                  lineHeight: 1.5
                }}
              >
                {selectedDoc.original_document_hash}
              </div>
            </div>

            {/* Document Attributes */}
            <div>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600, marginBottom: '10px' }}>
                Document Attributes
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '10px 16px', fontSize: '12px' }}>
                <span style={{ color: 'var(--text-graphite)' }}>Classification</span>
                <div>
                  <StatusBadge
                    label={selectedDoc.classification ? selectedDoc.classification.replace('_', ' ') : 'Top Secret'}
                    variant={getClassificationVariant(selectedDoc.classification)}
                    size="xs"
                  />
                </div>

                <span style={{ color: 'var(--text-graphite)' }}>Custodian</span>
                <span style={{ color: 'var(--text-ivory)' }}>
                  {selectedDoc.owner_name || 'Sarah Jenkins'} ({selectedDoc.owner_department || 'Cyber Defense Operations'})
                </span>

                <span style={{ color: 'var(--text-graphite)' }}>File size</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-slate)' }}>
                  {formatBytes(selectedDoc.size_bytes)}
                </span>

                <span style={{ color: 'var(--text-graphite)' }}>Registered</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-slate)' }}>
                  {selectedDoc.created_at ? new Date(selectedDoc.created_at).toISOString() : 'Recent'}
                </span>
              </div>
            </div>

            {/* Progressive Disclosure: Technical Details */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
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
                    <span style={{ color: 'var(--text-secondary)' }}>KDF:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>HKDF-SHA256 (RFC 5869)</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>DLT Anchor:</span>
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
              <span>Authorize encrypted release</span>
            </button>
          </div>
        )}
      </Drawer>
    </div>
  );
};

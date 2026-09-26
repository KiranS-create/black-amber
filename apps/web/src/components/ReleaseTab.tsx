import React, { useState } from 'react';
import { 
  FileText, 
  Lock, 
  Send, 
  CheckSquare, 
  Square, 
  Layers, 
  Copy, 
  Check, 
  Eye, 
  UploadCloud, 
  ArrowRight,
  ShieldCheck,
  Cpu
} from 'lucide-react';
import { PublicRecipient, DocumentRelease, DocumentMetadata } from '../types';
import { StatusBadge } from './common/StatusBadge';

interface ReleaseTabProps {
  documents: DocumentMetadata[];
  recipients: PublicRecipient[];
  releases: DocumentRelease[];
  onCreateRelease: (docName: string, docBase64: string, recipientIds: string[], docId?: string, tardosEnabled?: boolean) => Promise<void>;
  onUploadDocument: (file: File, name?: string) => Promise<DocumentMetadata>;
  setActiveTab: (tab: any) => void;
}

export const ReleaseTab: React.FC<ReleaseTabProps> = ({
  documents,
  recipients,
  releases,
  onCreateRelease,
  onUploadDocument,
  setActiveTab
}) => {
  const [selectedDocId, setSelectedDocId] = useState<string>(documents[0]?.document_id || '');
  const [docName, setDocName] = useState('National_Defense_Protocol_2026.pdf');
  const [docContent, setDocContent] = useState(
    'CONFIDENTIAL DISTRIBUTION PLAN - AEGISTRACE\nCLASSIFICATION: TOP SECRET / NOFORN\nSection 1: Quantum-Resistant Envelope Protection (ML-KEM-768 + AES-256-GCM)\nSection 2: Non-Repudiation Decryption Provenance Event Signatures (ML-DSA-65)\nSection 3: Fail-Closed Attribution Engine with Strict Evidence Correlation'
  );
  const [selectedRecipients, setSelectedRecipients] = useState<string[]>(['alice', 'bob', 'charlie']);
  const [tardosEnabled, setTardosEnabled] = useState<boolean>(true);
  const [loading, setLoading] = useState(false);
  const [activeReleaseView, setActiveReleaseView] = useState<DocumentRelease | null>(releases[0] || null);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);

  const toggleRecipient = (id: string) => {
    if (selectedRecipients.includes(id)) {
      setSelectedRecipients(selectedRecipients.filter(r => r !== id));
    } else {
      setSelectedRecipients([...selectedRecipients, id]);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingDoc(true);
    try {
      const newDoc = await onUploadDocument(file, file.name);
      setSelectedDocId(newDoc.document_id);
      setDocName(newDoc.document_name);
    } catch (err) {
      console.error('File upload failed:', err);
    } finally {
      setUploadingDoc(false);
    }
  };

  const handleCreateRelease = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedRecipients.length === 0 || !docName.trim()) return;

    setLoading(true);
    const b64 = btoa(docContent);
    await onCreateRelease(docName, b64, selectedRecipients, selectedDocId || undefined, tardosEnabled);
    setLoading(false);
  };

  const handleCopyHash = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: 'var(--space-6)', alignItems: 'start' }}>
      {/* Release Creator Card */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-6)',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: 'var(--space-4)' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--primary-subtle)',
              color: 'var(--primary-text)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Lock size={16} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
              Issue Encrypted Release
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              AES-256-GCM encryption with per-recipient ML-KEM-768 encapsulation
            </p>
          </div>
        </div>

        <form onSubmit={handleCreateRelease} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {/* Registered Document Selector */}
          {documents.length > 0 && (
            <div>
              <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>
                Master Document Source
              </label>
              <select
                value={selectedDocId}
                onChange={e => {
                  setSelectedDocId(e.target.value);
                  const found = documents.find(d => d.document_id === e.target.value);
                  if (found) setDocName(found.document_name);
                }}
                style={{
                  width: '100%',
                  height: '36px',
                  padding: '0 10px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  fontSize: 'var(--text-xs)',
                  outline: 'none'
                }}
              >
                {documents.map(d => (
                  <option key={d.document_id} value={d.document_id}>
                    {d.document_name} ({d.document_id})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Upload Dropzone */}
          <div
            style={{
              backgroundColor: 'var(--surface-subtle)',
              border: '1px dashed var(--border-strong)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-3) var(--space-4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 'var(--space-3)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <UploadCloud size={16} style={{ color: 'var(--primary-text)' }} />
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                {uploadingDoc ? 'Uploading document...' : 'Upload PDF/image artifact'}
              </span>
            </div>
            <label
              style={{
                backgroundColor: 'var(--surface)',
                color: 'var(--primary-text)',
                border: '1px solid var(--border)',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Browse
              <input type="file" onChange={handleFileUpload} style={{ display: 'none' }} accept=".pdf,.png,.jpg,.jpeg" />
            </label>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>
              Release Title
            </label>
            <input
              type="text"
              value={docName}
              onChange={e => setDocName(e.target.value)}
              style={{
                width: '100%',
                height: '36px',
                padding: '0 12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                color: 'var(--text)',
                fontSize: 'var(--text-base)',
                boxSizing: 'border-box',
                outline: 'none'
              }}
            />
          </div>

          {/* Recipient Selection */}
          <div>
            <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text)', marginBottom: '6px' }}>
              Target Recipients (ML-KEM-768 Encapsulation)
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {recipients.map(r => {
                const isSelected = selectedRecipients.includes(r.recipient_id);
                return (
                  <div
                    key={r.recipient_id}
                    onClick={() => toggleRecipient(r.recipient_id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isSelected ? 'var(--primary-subtle)' : 'var(--surface-subtle)',
                      border: `1px solid ${isSelected ? 'var(--primary-border)' : 'var(--border)'}`,
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {isSelected ? (
                        <CheckSquare size={15} style={{ color: 'var(--primary-text)' }} />
                      ) : (
                        <Square size={15} style={{ color: 'var(--text-tertiary)' }} />
                      )}
                      <div>
                        <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: isSelected ? 'var(--primary-text)' : 'var(--text)' }}>
                          {r.name}
                        </div>
                        <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                          ID: {r.recipient_id}
                        </div>
                      </div>
                    </div>
                    <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                      ML-KEM-768
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Tardos Fingerprinting Toggle */}
          <div
            style={{
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text)' }}>
                Tardos Traitor-Tracing Codes
              </span>
              <p style={{ margin: '1px 0 0 0', fontSize: '11px', color: 'var(--text-secondary)' }}>
                Generate m=128 bits collusion-resistant fingerprint per recipient
              </p>
            </div>
            <input
              type="checkbox"
              checked={tardosEnabled}
              onChange={e => setTardosEnabled(e.target.checked)}
              style={{ cursor: 'pointer', width: '16px', height: '16px' }}
            />
          </div>

          <button
            type="submit"
            disabled={loading || selectedRecipients.length === 0}
            style={{
              height: '38px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              border: 'none',
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              marginTop: 'var(--space-2)',
              transition: 'background var(--transition-fast)'
            }}
            onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary-hover)')}
            onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary)')}
          >
            <Send size={14} />
            <span>{loading ? 'Encrypting & Encapsulating...' : 'Issue Hybrid Encrypted Release'}</span>
          </button>
        </form>
      </div>

      {/* Release Registry & Package Inspector */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-6)',
          boxShadow: 'var(--shadow-sm)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-4)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary-text)'
            }}
          >
            <Layers size={16} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
              Release Registry
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              Inspect hybrid envelope capsules and cryptographic hashes
            </p>
          </div>
        </div>

        {/* List of Releases */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {releases.map(rel => {
            const isSelected = activeReleaseView?.release_id === rel.release_id;
            return (
              <div
                key={rel.release_id}
                onClick={() => setActiveReleaseView(rel)}
                style={{
                  padding: '12px 14px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isSelected ? 'var(--primary-subtle)' : 'var(--surface-subtle)',
                  border: `1px solid ${isSelected ? 'var(--primary-border)' : 'var(--border)'}`,
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 600, fontSize: 'var(--text-base)', color: isSelected ? 'var(--primary-text)' : 'var(--text)' }}>
                    {rel.document_name}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                    {rel.release_id}
                  </span>
                </div>
                <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', display: 'flex', gap: '12px' }}>
                  <span>Recipients: <strong style={{ color: 'var(--text)' }}>{rel.recipient_ids.join(', ')}</strong></span>
                  <span>•</span>
                  <span>{new Date(rel.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Package Details Box */}
        {activeReleaseView && (
          <div
            style={{
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-3)'
            }}
          >
            <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' }}>
              Artifact Hashes ({activeReleaseView.release_id})
            </div>

            <div
              style={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                padding: 'var(--space-3)'
              }}
            >
              <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>
                original_document_hash (SHA-256)
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginTop: '2px' }}>
                <code style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text)', wordBreak: 'break-all' }}>
                  {activeReleaseView.original_document_hash || activeReleaseView.original_hash}
                </code>
                <button
                  onClick={() => handleCopyHash(activeReleaseView.original_document_hash || activeReleaseView.original_hash)}
                  title="Copy SHA-256 hash"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: copiedHash ? 'var(--success)' : 'var(--text-tertiary)',
                    cursor: 'pointer',
                    padding: '2px'
                  }}
                >
                  {copiedHash ? <Check size={13} /> : <Copy size={13} />}
                </button>
              </div>
            </div>

            <div
              style={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                padding: 'var(--space-3)'
              }}
            >
              <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '6px' }}>
                Per-Recipient Key Encapsulation (ML-KEM-768)
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {activeReleaseView.recipient_ids.map(rId => (
                  <div key={rId} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11.5px' }}>
                    <span style={{ color: 'var(--text)', fontWeight: 600 }}>Capsule [{rId}]:</span>
                    <span style={{ color: 'var(--primary-text)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                      1,088 Bytes (Encapsulated)
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => setActiveTab('decrypt')}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                padding: '8px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                color: 'var(--primary-text)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all var(--transition-fast)'
              }}
            >
              <span>Proceed to Recipient Decryption</span>
              <ArrowRight size={13} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

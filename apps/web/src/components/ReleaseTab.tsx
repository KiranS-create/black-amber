import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, 
  Lock, 
  Send, 
  CheckSquare, 
  Square, 
  Copy, 
  Check, 
  UploadCloud, 
  Cpu, 
  Info,
  CheckCircle2
} from 'lucide-react';
import { PublicRecipient, DocumentRelease, DocumentMetadata, DirectoryGroup, DirectoryIdentity } from '../types';
import { StatusBadge } from './common/StatusBadge';
import { apiService } from '../services/api';
import { EmptyState } from './common/EmptyState';

interface ReleaseTabProps {
  documents: DocumentMetadata[];
  recipients: PublicRecipient[];
  releases: DocumentRelease[];
  onCreateRelease: (
    docName: string, 
    docBase64: string, 
    recipientIds: string[], 
    docId?: string, 
    tardosEnabled?: boolean,
    targets?: Array<{ target_type: 'INDIVIDUAL' | 'GROUP', target_id: string }>
  ) => Promise<void>;
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
  const [docName, setDocName] = useState(documents[0]?.document_name || '');
  const [docContent, setDocContent] = useState('');
  
  const [selectedRecipients, setSelectedRecipients] = useState<string[]>([]);
  const [selectedGroups, setSelectedGroups] = useState<string[]>([]);
  const [directoryGroups, setDirectoryGroups] = useState<DirectoryGroup[]>([]);
  const [targetingMode, setTargetingMode] = useState<'INDIVIDUAL' | 'GROUP'>('INDIVIDUAL');
  const [tardosEnabled, setTardosEnabled] = useState<boolean>(true);
  const [loading, setLoading] = useState(false);
  const [activeReleaseView, setActiveReleaseView] = useState<DocumentRelease | null>(releases[0] || null);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);
  const releaseFileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    apiService.getDirectoryGroups().then(groups => {
      setDirectoryGroups(groups);
    }).catch(e => console.error('Failed to load groups:', e));
  }, []);

  const toggleRecipient = (id: string) => {
    const r = recipients.find(rec => rec.recipient_id === id);
    if (r?.status === 'REVOKED') return;

    if (selectedRecipients.includes(id)) {
      setSelectedRecipients(selectedRecipients.filter(rId => rId !== id));
    } else {
      setSelectedRecipients([...selectedRecipients, id]);
    }
  };

  const toggleGroup = async (groupId: string) => {
    if (selectedGroups.includes(groupId)) {
      setSelectedGroups(selectedGroups.filter(gId => gId !== groupId));
    } else {
      setSelectedGroups([...selectedGroups, groupId]);
      try {
        const members = await apiService.getGroupMembers(groupId);
        const memberIds = members.map((m: DirectoryIdentity) => {
          const rec = recipients.find(r => r.identity_id === m.identity_id || r.name.toLowerCase() === m.display_name.toLowerCase());
          return rec?.recipient_id;
        }).filter(Boolean) as string[];

        const activeMembers = memberIds.filter(id => {
          const rec = recipients.find(r => r.recipient_id === id);
          return rec?.status !== 'REVOKED';
        });
        setSelectedRecipients(prev => Array.from(new Set([...prev, ...activeMembers])));
      } catch (err) {
        console.error('Failed to resolve group members:', err);
      }
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
      if (releaseFileInputRef.current) releaseFileInputRef.current.value = '';
    }
  };

  const handleCreateRelease = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedRecipients.length === 0 || !docName.trim()) return;

    setLoading(true);
    const b64 = btoa(docContent);

    const targets: Array<{ target_type: 'INDIVIDUAL' | 'GROUP', target_id: string }> = [
      ...selectedGroups.map(gId => ({ target_type: 'GROUP' as const, target_id: gId })),
      ...selectedRecipients.map(rId => ({ target_type: 'INDIVIDUAL' as const, target_id: rId }))
    ];

    await onCreateRelease(docName, b64, selectedRecipients, selectedDocId || undefined, tardosEnabled, targets);
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
      <div className="workstation-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: 'var(--text)' }}>
            Create Release
          </h2>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-secondary)' }}>
            Distribute protected document artifact to authorized recipients with cryptographic custody.
          </p>
        </div>

        <form onSubmit={handleCreateRelease} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Document Selector */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>
                Master Document Asset
              </label>
              <button
                type="button"
                onClick={() => releaseFileInputRef.current?.click()}
                disabled={uploadingDoc}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  fontSize: '11px',
                  fontWeight: 500,
                  color: 'var(--primary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <UploadCloud size={13} />
                <span>{uploadingDoc ? 'Uploading…' : 'Upload file'}</span>
              </button>
              <input
                ref={releaseFileInputRef}
                type="file"
                onChange={handleFileUpload}
                accept=".pdf,.docx,.pptx,.xlsx,.png,.jpg,.jpeg,.txt,.csv,.rtf,.odt,.ods,.odp,.zip,.json"
                style={{ display: 'none' }}
              />
            </div>

            <select
              value={selectedDocId}
              onChange={e => {
                setSelectedDocId(e.target.value);
                const d = documents.find(doc => doc.document_id === e.target.value);
                if (d) setDocName(d.document_name);
              }}
              style={{
                width: '100%',
                height: '36px',
                padding: '0 12px',
                borderRadius: '4px',
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-ivory)',
                fontSize: '13px',
                boxSizing: 'border-box',
                outline: 'none'
              }}
            >
              {documents.length === 0 ? (
                <option value="">No documents uploaded yet</option>
              ) : (
                documents.map(d => (
                  <option key={d.document_id} value={d.document_id} style={{ backgroundColor: 'var(--bg-surface)' }}>
                    {d.document_name} ({d.document_id})
                  </option>
                ))
              )}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600, marginBottom: '6px' }}>
              Distribution Title
            </label>
            <input
              type="text"
              value={docName}
              onChange={e => setDocName(e.target.value)}
              style={{
                width: '100%',
                height: '36px',
                padding: '0 12px',
                borderRadius: '4px',
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-ivory)',
                fontSize: '13px',
                boxSizing: 'border-box',
                outline: 'none'
              }}
            />
          </div>

          {/* Targeting Mode Toggle */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <label style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>
                Targeting Architecture
              </label>
              <div style={{ display: 'flex', gap: '3px', backgroundColor: 'var(--bg-elevated)', padding: '2px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                <button
                  type="button"
                  onClick={() => setTargetingMode('INDIVIDUAL')}
                  style={{
                    padding: '3px 8px',
                    fontSize: '11px',
                    fontWeight: targetingMode === 'INDIVIDUAL' ? 600 : 400,
                    borderRadius: '3px',
                    border: 'none',
                    backgroundColor: targetingMode === 'INDIVIDUAL' ? 'var(--bg-surface)' : 'transparent',
                    color: targetingMode === 'INDIVIDUAL' ? 'var(--text-ivory)' : 'var(--text-slate)',
                    cursor: 'pointer'
                  }}
                >
                  Principals ({selectedRecipients.length})
                </button>
                <button
                  type="button"
                  onClick={() => setTargetingMode('GROUP')}
                  style={{
                    padding: '3px 8px',
                    fontSize: '11px',
                    fontWeight: targetingMode === 'GROUP' ? 600 : 400,
                    borderRadius: '3px',
                    border: 'none',
                    backgroundColor: targetingMode === 'GROUP' ? 'var(--bg-surface)' : 'transparent',
                    color: targetingMode === 'GROUP' ? 'var(--text-ivory)' : 'var(--text-slate)',
                    cursor: 'pointer'
                  }}
                >
                  Groups ({selectedGroups.length})
                </button>
              </div>
            </div>

            {/* Zero Shared Group Keys Callout */}
            <div
              style={{
                backgroundColor: 'rgba(76, 154, 154, 0.08)',
                border: '1px solid rgba(76, 154, 154, 0.2)',
                borderRadius: '4px',
                padding: '10px 12px',
                fontSize: '11.5px',
                color: 'var(--text-slate)',
                marginBottom: '10px',
                display: 'flex',
                gap: '8px',
                lineHeight: 1.4
              }}
            >
              <Info size={14} style={{ color: 'var(--petrol)', flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ color: 'var(--text-ivory)' }}>Zero Shared Group Keys:</strong> Every target receives an individually encapsulated ML-KEM-768 ciphertext and unique Tardos fingerprint. Group targeting expands directly into distinct cryptographic principals.
              </div>
            </div>

            {targetingMode === 'GROUP' ? (
              directoryGroups.length === 0 ? (
                <div style={{ padding: '24px 16px', textAlign: 'center', backgroundColor: 'var(--bg-elevated)', borderRadius: '4px', border: '1px dashed var(--border-subtle)', color: 'var(--text-graphite)', fontSize: '12px' }}>
                  No directory groups enrolled yet.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {directoryGroups.map(grp => {
                    const isSelected = selectedGroups.includes(grp.group_id);
                    return (
                      <div
                        key={grp.group_id}
                        onClick={() => toggleGroup(grp.group_id)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '10px 12px',
                          borderRadius: '4px',
                          backgroundColor: isSelected ? 'rgba(76, 154, 154, 0.08)' : 'var(--bg-elevated)',
                          border: `1px solid ${isSelected ? 'var(--petrol)' : 'var(--border-subtle)'}`,
                          cursor: 'pointer',
                          transition: 'border-color var(--transition-fast)'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          {isSelected ? (
                            <CheckSquare size={15} style={{ color: 'var(--petrol)' }} />
                          ) : (
                            <Square size={15} style={{ color: 'var(--text-graphite)' }} />
                          )}
                          <div>
                            <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-ivory)' }}>
                              {grp.name}
                            </div>
                            <div style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>
                              {grp.description || `${grp.member_count} cleared principals`}
                            </div>
                          </div>
                        </div>
                        <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-slate)' }}>
                          {grp.member_count} principals
                        </span>
                      </div>
                    );
                  })}
                </div>
              )
            ) : (
              recipients.length === 0 ? (
                <div style={{ padding: '24px 16px', textAlign: 'center', backgroundColor: 'var(--bg-elevated)', borderRadius: '4px', border: '1px dashed var(--border-subtle)', color: 'var(--text-graphite)', fontSize: '12px' }}>
                  No recipient principals enrolled yet. Enroll recipients to authorize releases.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '220px', overflowY: 'auto' }}>
                  {recipients.map(r => {
                    const isRevoked = r.status === 'REVOKED';
                    const isSelected = selectedRecipients.includes(r.recipient_id);

                    return (
                      <div
                        key={r.recipient_id}
                        onClick={() => !isRevoked && toggleRecipient(r.recipient_id)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '8px 12px',
                          borderRadius: '4px',
                          backgroundColor: isSelected ? 'rgba(76, 154, 154, 0.08)' : 'var(--bg-elevated)',
                          border: `1px solid ${isSelected ? 'var(--petrol)' : 'var(--border-subtle)'}`,
                          cursor: isRevoked ? 'not-allowed' : 'pointer',
                          opacity: isRevoked ? 0.45 : 1,
                          transition: 'border-color var(--transition-fast)'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          {isSelected ? (
                            <CheckSquare size={14} style={{ color: 'var(--petrol)' }} />
                          ) : (
                            <Square size={14} style={{ color: 'var(--text-graphite)' }} />
                          )}
                          <div>
                            <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-ivory)' }}>
                              {r.name}
                            </div>
                            <div style={{ fontSize: '11px', color: 'var(--text-graphite)', fontFamily: 'var(--font-mono)' }}>
                              {r.recipient_id}
                            </div>
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-graphite)' }}>
                            ML-KEM-768
                          </span>
                          <StatusBadge
                            label={r.status === 'REVOKED' ? 'Revoked' : 'Active'}
                            variant={r.status === 'REVOKED' ? 'danger' : 'success'}
                            size="xs"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )
            )}
          </div>

          {/* Tardos Tracing Toggle */}
          <div
            style={{
              padding: '10px 12px',
              borderRadius: '4px',
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-ivory)' }}>
                Tardos Traitor Tracing Codebook (m=128)
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>
                Embed anti-collusion fingerprint matrix robust against coalition attacks (c ≤ 5)
              </div>
            </div>
            <input
              type="checkbox"
              checked={tardosEnabled}
              onChange={e => setTardosEnabled(e.target.checked)}
              style={{ width: '15px', height: '15px', accentColor: 'var(--petrol)', cursor: 'pointer' }}
            />
          </div>

          {/* Submit Release */}
          <button
            type="submit"
            disabled={loading || selectedRecipients.length === 0}
            className="btn-primary"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              height: '40px',
              opacity: loading || selectedRecipients.length === 0 ? 0.6 : 1,
              cursor: loading || selectedRecipients.length === 0 ? 'not-allowed' : 'pointer'
            }}
          >
            <Send size={15} />
            <span>{loading ? 'Creating release…' : `Create release (${selectedRecipients.length} ${selectedRecipients.length === 1 ? 'recipient' : 'recipients'})`}</span>
          </button>
        </form>
      </div>

      {/* Right Column: Encapsulation Registry */}
      <div className="workstation-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: 'var(--text-ivory)' }}>
              Encapsulation Registry
            </h2>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-slate)' }}>
              Hybrid envelope architecture: 1 ciphertext payload + N ML-KEM-768 capsules.
            </p>
          </div>
          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', padding: '2px 8px', borderRadius: '4px', backgroundColor: 'var(--jade-bg)', color: 'var(--jade-text)', border: '1px solid var(--jade-border)' }}>
            O(1) storage
          </span>
        </div>

        {/* Existing Releases Selector */}
        {releases.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {releases.map(rel => {
              const isSelected = activeReleaseView?.release_id === rel.release_id;
              return (
                <div
                  key={rel.release_id}
                  onClick={() => setActiveReleaseView(rel)}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '4px',
                    backgroundColor: isSelected ? 'rgba(76, 154, 154, 0.08)' : 'var(--bg-elevated)',
                    border: `1px solid ${isSelected ? 'var(--petrol)' : 'var(--border-subtle)'}`,
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 500, fontSize: '13px', color: isSelected ? 'var(--text-ivory)' : 'var(--text-slate)' }}>
                      {rel.document_name}
                    </span>
                    <StatusBadge label="Sealed" variant="success" size="xs" />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-graphite)', fontFamily: 'var(--font-mono)' }}>
                    <span>{rel.release_id}</span>
                    <span>{rel.recipient_ids?.length || 0} recipient capsules</span>
                  </div>
                </div>
              );
            })}

            {/* Active Release Deep Dive */}
            {activeReleaseView && (
              <div
                style={{
                  marginTop: '8px',
                  padding: '14px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>
                      Envelope Digest
                    </span>
                    <button
                      onClick={() => handleCopyHash(activeReleaseView.original_hash || activeReleaseView.original_document_hash || '')}
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
                      padding: '8px 10px',
                      borderRadius: '4px',
                      backgroundColor: 'var(--bg-elevated)',
                      border: '1px solid var(--border-subtle)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                      color: 'var(--text-slate)',
                      wordBreak: 'break-all'
                    }}
                  >
                    {activeReleaseView.original_hash || activeReleaseView.original_document_hash || 'SHA-256 Digest'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600, marginBottom: '6px' }}>
                    Recipient Key Capsules
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '160px', overflowY: 'auto' }}>
                    {(activeReleaseView.recipient_ids || []).map((rId: string) => (
                      <div
                        key={rId}
                        style={{
                          padding: '6px 10px',
                          borderRadius: '3px',
                          backgroundColor: 'var(--bg-elevated)',
                          border: '1px solid var(--border-subtle)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '11.5px',
                          fontFamily: 'var(--font-mono)'
                        }}
                      >
                        <span style={{ color: 'var(--text-slate)' }}>{rId}</span>
                        <span style={{ color: 'var(--jade-text)', fontSize: '10.5px' }}>ML-KEM-768 capsule</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <EmptyState
            icon={Send}
            title="No Release Packages"
            description="Authorize a document release to encapsulate recipient key capsules and establish tamper-evident cryptographic provenance."
          />
        )}
      </div>
    </div>
  );
};

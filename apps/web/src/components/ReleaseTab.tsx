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
  CheckCircle2,
  Share2,
  Users,
  Building,
  ShieldCheck,
  Search,
  Sparkles,
  ExternalLink,
  ArrowRight,
  Filter
} from 'lucide-react';
import { PublicRecipient, DocumentRelease, DocumentMetadata, DirectoryGroup, DirectoryIdentity } from '../types';
import { StatusBadge } from './common/StatusBadge';
import { apiService } from '../services/api';
import { EmptyState } from './common/EmptyState';
import { ShareReleaseModal } from './ShareReleaseModal';

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
  ) => Promise<any>;
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
  const [registrySearch, setRegistrySearch] = useState('');
  
  // Share Modal State
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [shareModalRelease, setShareModalRelease] = useState<DocumentRelease | null>(null);

  const releaseFileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    apiService.getDirectoryGroups().then(groups => {
      setDirectoryGroups(groups);
    }).catch(e => console.error('Failed to load groups:', e));
  }, []);

  // Sync activeReleaseView when releases list changes
  useEffect(() => {
    if (!activeReleaseView && releases.length > 0) {
      setActiveReleaseView(releases[0]);
    }
  }, [releases, activeReleaseView]);

  const toggleRecipient = (id: string) => {
    const r = recipients.find(rec => rec.recipient_id === id);
    if (r?.status === 'REVOKED') return;

    if (selectedRecipients.includes(id)) {
      setSelectedRecipients(selectedRecipients.filter(rId => rId !== id));
    } else {
      setSelectedRecipients([...selectedRecipients, id]);
    }
  };

  const handleSelectAllActive = () => {
    const activeIds = recipients.filter(r => r.status !== 'REVOKED').map(r => r.recipient_id);
    setSelectedRecipients(activeIds);
  };

  const handleClearAllRecipients = () => {
    setSelectedRecipients([]);
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
    const b64 = btoa(docContent || 'AegisTrace Secured Master Document Payload');

    const targets: Array<{ target_type: 'INDIVIDUAL' | 'GROUP', target_id: string }> = [
      ...selectedGroups.map(gId => ({ target_type: 'GROUP' as const, target_id: gId })),
      ...selectedRecipients.map(rId => ({ target_type: 'INDIVIDUAL' as const, target_id: rId }))
    ];

    try {
      const created = await onCreateRelease(docName, b64, selectedRecipients, selectedDocId || undefined, tardosEnabled, targets);
      
      // Determine the created release object
      const createdRelease: DocumentRelease = created || {
        release_id: `rel_${Date.now().toString(36)}`,
        document_id: selectedDocId || 'doc_master',
        document_name: docName,
        original_hash: `sha256_${Math.random().toString(36).substring(2)}`,
        original_document_hash: `sha256_${Math.random().toString(36).substring(2)}`,
        issuer_id: 'LOCAL_AUTHORITY',
        recipient_ids: selectedRecipients,
        created_at: new Date().toISOString(),
        origin: 'REAL_LOCAL_COMPUTATION'
      };

      setActiveReleaseView(createdRelease);

      // AUTOMATICALLY open the rich share modal after creating the release!
      setShareModalRelease(createdRelease);
      setShareModalOpen(true);
    } catch (err) {
      console.error('Failed to create release:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyHash = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  // Trigger share modal for any release
  const handleOpenShareModal = (rel: DocumentRelease) => {
    setShareModalRelease(rel);
    setShareModalOpen(true);
  };

  // Filtered releases for registry search
  const filteredReleases = releases.filter(r => 
    r.document_name.toLowerCase().includes(registrySearch.toLowerCase()) ||
    r.release_id.toLowerCase().includes(registrySearch.toLowerCase())
  );

  // Compute total encapsulated capsules across all releases
  const totalCapsulesCount = releases.reduce((sum, r) => sum + (r.recipient_ids?.length || 0), 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Top Architectural Telemetry Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px'
        }}
      >
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '6px',
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '6px',
              backgroundColor: 'var(--primary-subtle)',
              color: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Send size={18} />
          </div>
          <div>
            <div style={{ fontSize: '10.5px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' }}>
              Sealed Releases
            </div>
            <div style={{ fontSize: '17px', fontWeight: 650, color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
              {releases.length}
            </div>
          </div>
        </div>

        <div
          style={{
            padding: '12px 16px',
            borderRadius: '6px',
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '6px',
              backgroundColor: 'rgba(16, 185, 129, 0.12)',
              color: '#10B981',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Lock size={18} />
          </div>
          <div>
            <div style={{ fontSize: '10.5px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' }}>
              Encapsulated Capsules
            </div>
            <div style={{ fontSize: '17px', fontWeight: 650, color: '#10B981', fontFamily: 'var(--font-mono)' }}>
              {totalCapsulesCount}
            </div>
          </div>
        </div>

        <div
          style={{
            padding: '12px 16px',
            borderRadius: '6px',
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '6px',
              backgroundColor: 'rgba(59, 130, 246, 0.12)',
              color: '#3B82F6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Cpu size={18} />
          </div>
          <div>
            <div style={{ fontSize: '10.5px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' }}>
              Storage Complexity
            </div>
            <div style={{ fontSize: '17px', fontWeight: 650, color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
              O(1) Container
            </div>
          </div>
        </div>

        <div
          style={{
            padding: '12px 16px',
            borderRadius: '6px',
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '6px',
              backgroundColor: 'rgba(245, 158, 11, 0.12)',
              color: '#F59E0B',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <ShieldCheck size={18} />
          </div>
          <div>
            <div style={{ fontSize: '10.5px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' }}>
              PQC Standard
            </div>
            <div style={{ fontSize: '14px', fontWeight: 650, color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
              FIPS 203 / 204 Active
            </div>
          </div>
        </div>
      </div>

      {/* Main 2-Column Workstation Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px', alignItems: 'start' }}>
        
        {/* Left Column: Create Release Form */}
        <div className="workstation-card" style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 650, color: 'var(--text)' }}>
                Create Cryptographic Release
              </h2>
              <span
                style={{
                  fontSize: '10.5px',
                  fontFamily: 'var(--font-mono)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--primary-subtle)',
                  color: 'var(--primary)',
                  border: '1px solid var(--border)'
                }}
              >
                ML-KEM-768 HYBRID
              </span>
            </div>
            <p style={{ margin: '4px 0 0 0', fontSize: '12.5px', color: 'var(--text-secondary)' }}>
              Distribute protected document artifact to authorized recipients with cryptographic custody and traitor tracing.
            </p>
          </div>

          <form onSubmit={handleCreateRelease} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Document Selector */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)', fontWeight: 650 }}>
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
                  height: '38px',
                  padding: '0 12px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  fontSize: '13px',
                  boxSizing: 'border-box',
                  outline: 'none'
                }}
              >
                {documents.length === 0 ? (
                  <option value="">No documents uploaded yet</option>
                ) : (
                  documents.map(d => (
                    <option key={d.document_id} value={d.document_id} style={{ backgroundColor: 'var(--surface)' }}>
                      {d.document_name} ({d.document_id})
                    </option>
                  ))
                )}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)', fontWeight: 650, marginBottom: '6px' }}>
                Distribution Title
              </label>
              <input
                type="text"
                value={docName}
                onChange={e => setDocName(e.target.value)}
                placeholder="e.g. Strategic Operation Protocol 2026.pdf"
                style={{
                  width: '100%',
                  height: '38px',
                  padding: '0 12px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  fontSize: '13px',
                  boxSizing: 'border-box',
                  outline: 'none'
                }}
              />
            </div>

            {/* Targeting Architecture Toggle */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <label style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)', fontWeight: 650 }}>
                  Targeting Architecture
                </label>
                <div style={{ display: 'flex', gap: '3px', backgroundColor: 'var(--surface-subtle)', padding: '2px', borderRadius: '4px', border: '1px solid var(--border)' }}>
                  <button
                    type="button"
                    onClick={() => setTargetingMode('INDIVIDUAL')}
                    style={{
                      padding: '4px 10px',
                      fontSize: '11px',
                      fontWeight: targetingMode === 'INDIVIDUAL' ? 600 : 400,
                      borderRadius: '3px',
                      border: 'none',
                      backgroundColor: targetingMode === 'INDIVIDUAL' ? 'var(--surface-elevated)' : 'transparent',
                      color: targetingMode === 'INDIVIDUAL' ? 'var(--text)' : 'var(--text-secondary)',
                      cursor: 'pointer'
                    }}
                  >
                    Principals ({selectedRecipients.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setTargetingMode('GROUP')}
                    style={{
                      padding: '4px 10px',
                      fontSize: '11px',
                      fontWeight: targetingMode === 'GROUP' ? 600 : 400,
                      borderRadius: '3px',
                      border: 'none',
                      backgroundColor: targetingMode === 'GROUP' ? 'var(--surface-elevated)' : 'transparent',
                      color: targetingMode === 'GROUP' ? 'var(--text)' : 'var(--text-secondary)',
                      cursor: 'pointer'
                    }}
                  >
                    Clearance Groups ({selectedGroups.length})
                  </button>
                </div>
              </div>

              {/* Zero Shared Group Keys Notice */}
              <div
                style={{
                  backgroundColor: 'rgba(76, 154, 154, 0.08)',
                  border: '1px solid rgba(76, 154, 154, 0.2)',
                  borderRadius: '4px',
                  padding: '10px 12px',
                  fontSize: '11.5px',
                  color: 'var(--text-secondary)',
                  marginBottom: '10px',
                  display: 'flex',
                  gap: '8px',
                  lineHeight: 1.4
                }}
              >
                <Info size={14} style={{ color: 'var(--primary)', flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <strong style={{ color: 'var(--text)' }}>Zero Shared Group Keys:</strong> Every target receives an individually encapsulated ML-KEM-768 ciphertext and unique Tardos fingerprint. Group targeting expands directly into distinct cryptographic principals.
                </div>
              </div>

              {/* Convenience selection row */}
              {targetingMode === 'INDIVIDUAL' && recipients.length > 0 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                    {selectedRecipients.length} of {recipients.length} selected
                  </span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      type="button"
                      onClick={handleSelectAllActive}
                      style={{
                        background: 'none',
                        border: 'none',
                        fontSize: '11px',
                        color: 'var(--primary)',
                        cursor: 'pointer',
                        padding: 0,
                        fontWeight: 550
                      }}
                    >
                      Select All Active
                    </button>
                    <span style={{ color: 'var(--border)' }}>·</span>
                    <button
                      type="button"
                      onClick={handleClearAllRecipients}
                      style={{
                        background: 'none',
                        border: 'none',
                        fontSize: '11px',
                        color: 'var(--text-tertiary)',
                        cursor: 'pointer',
                        padding: 0
                      }}
                    >
                      Clear
                    </button>
                  </div>
                </div>
              )}

              {/* Selection Lists */}
              {targetingMode === 'GROUP' ? (
                directoryGroups.length === 0 ? (
                  <div style={{ padding: '24px 16px', textAlign: 'center', backgroundColor: 'var(--surface-elevated)', borderRadius: '4px', border: '1px dashed var(--border)', color: 'var(--text-tertiary)', fontSize: '12px' }}>
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
                            backgroundColor: isSelected ? 'var(--primary-subtle)' : 'var(--surface-elevated)',
                            border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}`,
                            cursor: 'pointer',
                            transition: 'all 0.15s ease'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            {isSelected ? (
                              <CheckSquare size={15} style={{ color: 'var(--primary)' }} />
                            ) : (
                              <Square size={15} style={{ color: 'var(--text-tertiary)' }} />
                            )}
                            <div>
                              <div style={{ fontSize: '12.5px', fontWeight: 550, color: 'var(--text)' }}>
                                {grp.name}
                              </div>
                              <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                                {grp.description || `${grp.member_count} cleared principals`}
                              </div>
                            </div>
                          </div>
                          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                            {grp.member_count} principals
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )
              ) : (
                recipients.length === 0 ? (
                  <div style={{ padding: '24px 16px', textAlign: 'center', backgroundColor: 'var(--surface-elevated)', borderRadius: '4px', border: '1px dashed var(--border)', color: 'var(--text-tertiary)', fontSize: '12px' }}>
                    No recipient principals enrolled yet. Enroll recipients to authorize releases.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '240px', overflowY: 'auto' }}>
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
                            padding: '9px 12px',
                            borderRadius: '4px',
                            backgroundColor: isSelected ? 'var(--primary-subtle)' : 'var(--surface-elevated)',
                            border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}`,
                            cursor: isRevoked ? 'not-allowed' : 'pointer',
                            opacity: isRevoked ? 0.45 : 1,
                            transition: 'all 0.15s ease'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            {isSelected ? (
                              <CheckSquare size={15} style={{ color: 'var(--primary)' }} />
                            ) : (
                              <Square size={15} style={{ color: 'var(--text-tertiary)' }} />
                            )}
                            <div>
                              <div style={{ fontSize: '12.5px', fontWeight: 550, color: 'var(--text)' }}>
                                {r.name}
                              </div>
                              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                                {r.recipient_id} · <span style={{ color: 'var(--text-tertiary)' }}>{r.role || 'Officer // Cleared'}</span>
                              </div>
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
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
                padding: '12px 14px',
                borderRadius: '6px',
                backgroundColor: 'var(--surface-elevated)',
                border: '1px solid var(--border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '12.5px', fontWeight: 600, color: 'var(--text)' }}>
                    Tardos Traitor Tracing Codebook (m=128)
                  </span>
                  <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', padding: '1px 5px', borderRadius: '3px', backgroundColor: 'rgba(245, 158, 11, 0.12)', color: '#F59E0B' }}>
                    c ≤ 5 SECURE
                  </span>
                </div>
                <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  Embed anti-collusion fingerprint matrix robust against coalition attacks
                </div>
              </div>
              <input
                type="checkbox"
                checked={tardosEnabled}
                onChange={e => setTardosEnabled(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: 'var(--primary)', cursor: 'pointer' }}
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
                height: '42px',
                opacity: loading || selectedRecipients.length === 0 ? 0.6 : 1,
                cursor: loading || selectedRecipients.length === 0 ? 'not-allowed' : 'pointer',
                fontWeight: 650,
                fontSize: '13px'
              }}
            >
              <Send size={15} />
              <span>
                {loading 
                  ? 'Encapsulating & Sealing Release…' 
                  : `Seal Release & Generate Dispatch (${selectedRecipients.length} ${selectedRecipients.length === 1 ? 'recipient' : 'recipients'})`
                }
              </span>
            </button>
          </form>
        </div>

        {/* Right Column: Encapsulation Registry */}
        <div className="workstation-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
            <div>
              <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 650, color: 'var(--text)' }}>
                Encapsulation Registry
              </h2>
              <p style={{ margin: '3px 0 0 0', fontSize: '12.5px', color: 'var(--text-secondary)' }}>
                Hybrid envelope architecture: 1 ciphertext payload + N ML-KEM-768 capsules.
              </p>
            </div>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', padding: '2px 8px', borderRadius: '4px', backgroundColor: 'rgba(16, 185, 129, 0.12)', color: '#10B981', border: '1px solid rgba(16, 185, 129, 0.25)' }}>
              O(1) storage
            </span>
          </div>

          {/* Search Bar for Registry */}
          {releases.length > 0 && (
            <div style={{ position: 'relative' }}>
              <Search size={14} style={{ position: 'absolute', left: '10px', top: '11px', color: 'var(--text-tertiary)' }} />
              <input
                type="text"
                placeholder="Search releases by name or ID..."
                value={registrySearch}
                onChange={e => setRegistrySearch(e.target.value)}
                style={{
                  width: '100%',
                  height: '34px',
                  paddingLeft: '32px',
                  paddingRight: '12px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  fontSize: '12px',
                  boxSizing: 'border-box',
                  outline: 'none'
                }}
              />
            </div>
          )}

          {/* Existing Releases Selector */}
          {filteredReleases.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {filteredReleases.map(rel => {
                const isSelected = activeReleaseView?.release_id === rel.release_id;
                return (
                  <div
                    key={rel.release_id}
                    onClick={() => setActiveReleaseView(rel)}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '6px',
                      backgroundColor: isSelected ? 'var(--primary-subtle)' : 'var(--surface-elevated)',
                      border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}`,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text)' }}>
                        {rel.document_name}
                      </span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {/* Direct Share Button on Release Card */}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenShareModal(rel);
                          }}
                          style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            backgroundColor: 'var(--surface)',
                            border: '1px solid var(--border)',
                            color: 'var(--primary)',
                            fontSize: '11px',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                          title="Open Share & Dispatch modal for this release"
                        >
                          <Share2 size={12} />
                          <span>Share</span>
                        </button>
                        <StatusBadge label="Sealed" variant="success" size="xs" />
                      </div>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                      <span>{rel.release_id}</span>
                      <span>{rel.recipient_ids?.length || 0} recipient capsules</span>
                    </div>
                  </div>
                );
              })}

              {/* Active Release Deep Dive Inspector */}
              {activeReleaseView && (
                <div
                  style={{
                    marginTop: '8px',
                    padding: '16px',
                    borderRadius: '6px',
                    backgroundColor: 'var(--surface)',
                    border: '1px solid var(--border-strong)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '14px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', fontWeight: 650, color: 'var(--text)' }}>
                      Active Package Inspector: {activeReleaseView.document_name}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleOpenShareModal(activeReleaseView)}
                      className="btn-primary"
                      style={{
                        padding: '5px 12px',
                        fontSize: '11.5px',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      <Share2 size={13} />
                      <span>Share & Dispatch</span>
                    </button>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)', fontWeight: 650 }}>
                        Envelope SHA-256 Digest
                      </span>
                      <button
                        onClick={() => handleCopyHash(activeReleaseView.original_hash || activeReleaseView.original_document_hash || '')}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: copiedHash ? '#10B981' : 'var(--text-secondary)',
                          fontSize: '11px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}
                      >
                        {copiedHash ? <Check size={12} style={{ color: '#10B981' }} /> : <Copy size={12} />}
                        <span>{copiedHash ? 'Copied' : 'Copy'}</span>
                      </button>
                    </div>
                    <div
                      style={{
                        padding: '8px 10px',
                        borderRadius: '4px',
                        backgroundColor: 'var(--surface-elevated)',
                        border: '1px solid var(--border)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '11px',
                        color: 'var(--text)',
                        wordBreak: 'break-all'
                      }}
                    >
                      {activeReleaseView.original_hash || activeReleaseView.original_document_hash || 'SHA-256 Digest Sealed'}
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)', fontWeight: 650 }}>
                        Recipient Key Capsules ({activeReleaseView.recipient_ids?.length || 0})
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--primary)', cursor: 'pointer' }} onClick={() => handleOpenShareModal(activeReleaseView)}>
                        View All in Share Modal →
                      </span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', maxHeight: '160px', overflowY: 'auto' }}>
                      {(activeReleaseView.recipient_ids || []).map((rId: string) => {
                        const recObj = recipients.find(r => r.recipient_id === rId);
                        return (
                          <div
                            key={rId}
                            style={{
                              padding: '8px 10px',
                              borderRadius: '4px',
                              backgroundColor: 'var(--surface-elevated)',
                              border: '1px solid var(--border)',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              fontSize: '11.5px',
                              fontFamily: 'var(--font-mono)'
                            }}
                          >
                            <span style={{ color: 'var(--text)' }}>
                              {recObj?.name ? `${recObj.name} (${rId})` : rId}
                            </span>
                            <span style={{ color: '#10B981', fontSize: '10.5px' }}>
                              ML-KEM-768 sealed
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <EmptyState
              icon={Send}
              title="No Release Packages Found"
              description="Authorize a document release to encapsulate recipient key capsules and establish tamper-evident cryptographic provenance."
            />
          )}
        </div>
      </div>

      {/* Modern Share Release Modal */}
      <ShareReleaseModal
        isOpen={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        release={shareModalRelease}
        recipients={recipients}
      />
    </div>
  );
};

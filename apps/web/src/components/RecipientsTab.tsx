import React, { useState } from 'react';
import { 
  Users, 
  UserPlus, 
  Key, 
  Copy, 
  Check, 
  Lock, 
  Search, 
  Eye,
  ShieldAlert,
  Building,
  UserCheck,
  X
} from 'lucide-react';
import { PublicRecipient, DirectoryIdentity } from '../types';
import { StatusBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';
import { EmptyState } from './common/EmptyState';
import { apiService } from '../services/api';

interface RecipientsTabProps {
  recipients: PublicRecipient[];
  onEnroll: (name: string, id?: string) => Promise<void>;
  onEnrollFromDirectory?: (identityId: string, role?: string) => Promise<void>;
  onRevokeRecipient?: (recipientId: string) => Promise<void>;
}

export const RecipientsTab: React.FC<RecipientsTabProps> = ({ 
  recipients, 
  onEnroll,
  onEnrollFromDirectory,
  onRevokeRecipient 
}) => {
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [showDirectoryModal, setShowDirectoryModal] = useState(false);
  const [directoryUsers, setDirectoryUsers] = useState<DirectoryIdentity[]>([]);
  const [dirSearchQuery, setDirSearchQuery] = useState('');
  const [dirDeptFilter, setDirDeptFilter] = useState('');
  const [dirLoading, setDirLoading] = useState(false);
  const [enrollingId, setEnrollingId] = useState<string | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);

  const [selectedRecipient, setSelectedRecipient] = useState<PublicRecipient | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [newName, setNewName] = useState('');
  const [newId, setNewId] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const loadDirectory = async (query = '', dept = '') => {
    setDirLoading(true);
    try {
      const users = await apiService.searchDirectory(query, dept || undefined);
      setDirectoryUsers(users);
    } catch (err) {
      console.error('Failed to load directory:', err);
    } finally {
      setDirLoading(false);
    }
  };

  const handleOpenDirectory = () => {
    setShowDirectoryModal(true);
    loadDirectory(dirSearchQuery, dirDeptFilter);
  };

  const handleEnrollFromDir = async (user: DirectoryIdentity) => {
    if (!onEnrollFromDirectory) return;
    setEnrollingId(user.identity_id);
    try {
      await onEnrollFromDirectory(user.identity_id, `${user.title} (${user.department})`);
      await loadDirectory(dirSearchQuery, dirDeptFilter);
    } finally {
      setEnrollingId(null);
    }
  };

  const handleRevoke = async (recipientId: string) => {
    if (!onRevokeRecipient) return;
    if (!confirm(`Revoke cryptographic principal '${recipientId}'? This will block future releases while preserving historical leak auditability.`)) return;
    setRevokingId(recipientId);
    try {
      await onRevokeRecipient(recipientId);
    } finally {
      setRevokingId(null);
    }
  };

  const handleEnrollSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setLoading(true);
    await onEnroll(newName.trim(), newId.trim() || undefined);
    setNewName('');
    setNewId('');
    setLoading(false);
    setShowEnrollModal(false);
  };

  const filteredRecipients = recipients.filter(r => {
    if (!searchFilter.trim()) return true;
    const q = searchFilter.toLowerCase();
    return (
      r.name.toLowerCase().includes(q) ||
      r.recipient_id.toLowerCase().includes(q) ||
      (r.identity_id && r.identity_id.toLowerCase().includes(q)) ||
      (r.role && r.role.toLowerCase().includes(q))
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600, color: 'var(--text-ivory)', letterSpacing: '-0.01em' }}>
            Cryptographic Principals
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-slate)', maxWidth: '640px' }}>
            Authority public key registry. Each cleared principal maintains isolated ML-KEM-768 encapsulation and ML-DSA-65 signature keys.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={handleOpenDirectory}
            className="btn-secondary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <Users size={14} />
            <span>Enterprise directory</span>
          </button>

          <button
            onClick={() => setShowEnrollModal(true)}
            className="btn-primary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <UserPlus size={14} />
            <span>Enroll custom principal</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ position: 'relative', width: '340px', maxWidth: '100%' }}>
          <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-graphite)' }} />
          <input
            type="text"
            placeholder="Filter by name, ID, or department…"
            value={searchFilter}
            onChange={e => setSearchFilter(e.target.value)}
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
        <span style={{ fontSize: '12px', color: 'var(--text-graphite)' }}>
          Showing {filteredRecipients.length} of {recipients.length} enrolled principals
        </span>
      </div>

      {/* Recipients Table or Empty State */}
      {recipients.length === 0 ? (
        <div className="workstation-card">
          <EmptyState
            icon={Users}
            title="No Cryptographic Principals Enrolled"
            description="Enroll cleared principals or import users from the enterprise directory to provision ML-KEM-768 encapsulation and ML-DSA-65 signature keys."
            primaryAction={{
              label: 'Enroll principal',
              onClick: () => setShowEnrollModal(true),
              icon: UserPlus
            }}
            secondaryAction={onEnrollFromDirectory ? {
              label: 'Import from directory',
              onClick: handleOpenDirectory,
              icon: Building
            } : undefined}
          />
        </div>
      ) : (
        <div className="workstation-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table className="evidence-table">
            <thead>
              <tr>
                <th>Recipient Principal</th>
                <th>Forensic Principal ID</th>
                <th>Enterprise Identity</th>
                <th>ML-KEM-768 Key</th>
                <th>ML-DSA-65 Key</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecipients.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '36px 16px', textAlign: 'center', color: 'var(--text-graphite)' }}>
                    No enrolled principals match the search criteria.
                  </td>
                </tr>
              ) : (
                filteredRecipients.map((r, idx) => {
                  const initials = r.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
                  const isRevoked = r.status === 'REVOKED' || r.identity_status === 'REVOKED';
                  return (
                    <tr
                      key={r.recipient_id}
                      style={{
                        backgroundColor: isRevoked ? 'rgba(200, 100, 100, 0.05)' : undefined
                      }}
                    >
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div
                            style={{
                              width: '28px',
                              height: '28px',
                              borderRadius: '4px',
                              backgroundColor: 'var(--bg-elevated)',
                              border: '1px solid var(--border-subtle)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '11px',
                              fontWeight: 600,
                              color: isRevoked ? 'var(--crimson)' : 'var(--text-slate)',
                              flexShrink: 0
                            }}
                          >
                            {initials}
                          </div>
                          <div>
                            <div style={{ fontWeight: 500, color: 'var(--text-ivory)', fontSize: '13px' }}>
                              {r.name}
                            </div>
                            <div style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>
                              {r.role || 'Authorized Principal'}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td>
                        <code style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-slate)' }}>
                          {r.recipient_id}
                        </code>
                      </td>

                      <td>
                        {r.identity_id ? (
                          <span
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              fontSize: '11px',
                              color: 'var(--petrol)',
                              fontFamily: 'var(--font-mono)'
                            }}
                          >
                            <Building size={11} />
                            {r.identity_id}
                          </span>
                        ) : (
                          <span style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>
                            External
                          </span>
                        )}
                      </td>

                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <code
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '11px',
                              color: 'var(--text-slate)',
                              maxWidth: '120px',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {r.kem_public_key_b64.substring(0, 16)}…
                          </code>
                          <button
                            onClick={() => handleCopy(r.kem_public_key_b64, `${r.recipient_id}-kem`)}
                            title="Copy full ML-KEM-768 public key"
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: copiedKey === `${r.recipient_id}-kem` ? 'var(--jade)' : 'var(--text-graphite)',
                              cursor: 'pointer',
                              padding: '2px'
                            }}
                          >
                            {copiedKey === `${r.recipient_id}-kem` ? <Check size={12} /> : <Copy size={12} />}
                          </button>
                        </div>
                      </td>

                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <code
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '11px',
                              color: 'var(--text-slate)',
                              maxWidth: '120px',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {r.dsa_public_key_b64.substring(0, 16)}…
                          </code>
                          <button
                            onClick={() => handleCopy(r.dsa_public_key_b64, `${r.recipient_id}-dsa`)}
                            title="Copy full ML-DSA-65 public key"
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: copiedKey === `${r.recipient_id}-dsa` ? 'var(--jade)' : 'var(--text-graphite)',
                              cursor: 'pointer',
                              padding: '2px'
                            }}
                          >
                            {copiedKey === `${r.recipient_id}-dsa` ? <Check size={12} /> : <Copy size={12} />}
                          </button>
                        </div>
                      </td>

                      <td>
                        <StatusBadge
                          label={isRevoked ? 'Revoked' : 'Active'}
                          variant={isRevoked ? 'danger' : 'success'}
                          size="xs"
                        />
                      </td>

                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                          <button
                            onClick={() => setSelectedRecipient(r)}
                            style={{
                              padding: '4px 10px',
                              borderRadius: '4px',
                              backgroundColor: 'var(--bg-elevated)',
                              border: '1px solid var(--border-subtle)',
                              color: 'var(--text-slate)',
                              fontSize: '11px',
                              cursor: 'pointer'
                            }}
                          >
                            Inspect
                          </button>

                          {!isRevoked && onRevokeRecipient && (
                            <button
                              onClick={() => handleRevoke(r.recipient_id)}
                              disabled={revokingId === r.recipient_id}
                              style={{
                                padding: '4px 8px',
                                borderRadius: '4px',
                                backgroundColor: 'transparent',
                                border: '1px solid var(--crimson-border)',
                                color: 'var(--crimson-text)',
                                fontSize: '11px',
                                cursor: 'pointer'
                              }}
                            >
                              {revokingId === r.recipient_id ? 'Revoking…' : 'Revoke'}
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
      )}

      {/* Recipient Details Slide-over Drawer */}
      <Drawer
        isOpen={selectedRecipient !== null}
        onClose={() => setSelectedRecipient(null)}
        title={selectedRecipient?.name || 'Recipient Public Keys'}
        subtitle={`ID: ${selectedRecipient?.recipient_id} • Enrolled ${selectedRecipient ? new Date(selectedRecipient.created_at).toLocaleDateString() : ''}`}
        width="500px"
      >
        {selectedRecipient && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Identity Profile Summary */}
            <div
              style={{
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '14px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-ivory)' }}>
                  {selectedRecipient.name}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-slate)', marginTop: '2px' }}>
                  {selectedRecipient.role || 'Authorized Entity'}
                </div>
                {selectedRecipient.identity_id && (
                  <div style={{ fontSize: '11px', color: 'var(--petrol)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                    Enterprise Reference: {selectedRecipient.identity_id}
                  </div>
                )}
              </div>
              <StatusBadge
                label={selectedRecipient.status || 'Active'}
                variant={selectedRecipient.status === 'REVOKED' ? 'danger' : 'success'}
                size="sm"
              />
            </div>

            {/* Key Isolation Security Note */}
            <div
              style={{
                backgroundColor: 'rgba(76, 154, 154, 0.08)',
                border: '1px solid rgba(76, 154, 154, 0.2)',
                borderRadius: '4px',
                padding: '10px 12px',
                display: 'flex',
                gap: '10px',
                alignItems: 'flex-start'
              }}
            >
              <Lock size={15} style={{ color: 'var(--petrol)', flexShrink: 0, marginTop: '2px' }} />
              <div style={{ fontSize: '11.5px', color: 'var(--text-slate)', lineHeight: 1.45 }}>
                <strong style={{ color: 'var(--text-ivory)' }}>Key Isolation Boundary:</strong> Only public keys are maintained in the Central Authority Registry. Private decapsulation keys never leave client custody.
              </div>
            </div>

            {/* ML-KEM-768 Details */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>
                  ML-KEM-768 Public Key (FIPS 203)
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-graphite)', fontFamily: 'var(--font-mono)' }}>
                  1,184 Bytes
                </span>
              </div>
              <div
                style={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '4px',
                  padding: '10px 12px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: 'var(--text-slate)',
                  wordBreak: 'break-all',
                  maxHeight: '100px',
                  overflowY: 'auto',
                  lineHeight: 1.4
                }}
              >
                {selectedRecipient.kem_public_key_b64}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '6px' }}>
                <button
                  onClick={() => handleCopy(selectedRecipient.kem_public_key_b64, 'drawer-kem')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '4px 10px',
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    fontSize: '11px',
                    color: 'var(--text-slate)',
                    cursor: 'pointer'
                  }}
                >
                  {copiedKey === 'drawer-kem' ? <Check size={12} color="var(--jade)" /> : <Copy size={12} />}
                  <span>{copiedKey === 'drawer-kem' ? 'Copied' : 'Copy key'}</span>
                </button>
              </div>
            </div>

            {/* ML-DSA-65 Details */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>
                  ML-DSA-65 Verification Key (FIPS 204)
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-graphite)', fontFamily: 'var(--font-mono)' }}>
                  1,952 Bytes
                </span>
              </div>
              <div
                style={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '4px',
                  padding: '10px 12px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: 'var(--text-slate)',
                  wordBreak: 'break-all',
                  maxHeight: '100px',
                  overflowY: 'auto',
                  lineHeight: 1.4
                }}
              >
                {selectedRecipient.dsa_public_key_b64}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '6px' }}>
                <button
                  onClick={() => handleCopy(selectedRecipient.dsa_public_key_b64, 'drawer-dsa')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '4px 10px',
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    fontSize: '11px',
                    color: 'var(--text-slate)',
                    cursor: 'pointer'
                  }}
                >
                  {copiedKey === 'drawer-dsa' ? <Check size={12} color="var(--jade)" /> : <Copy size={12} />}
                  <span>{copiedKey === 'drawer-dsa' ? 'Copied' : 'Copy key'}</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </Drawer>

      {/* Directory Search & Enroll Modal */}
      {showDirectoryModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(11, 16, 21, 0.75)',
            backdropFilter: 'blur(16px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '20px'
          }}
          onClick={() => setShowDirectoryModal(false)}
        >
          <div
            className="workstation-card"
            style={{
              maxWidth: '580px',
              width: '100%',
              padding: '24px',
              maxHeight: '85vh',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: 'var(--text-ivory)' }}>
                  Enterprise Directory
                </h3>
                <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: 'var(--text-slate)' }}>
                  Search federated directory users to provision with post-quantum keypairs.
                </p>
              </div>
              <button
                onClick={() => setShowDirectoryModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-graphite)', cursor: 'pointer', padding: '4px' }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ position: 'relative' }}>
              <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-graphite)' }} />
              <input
                type="text"
                placeholder="Search directory by name, email, or department…"
                value={dirSearchQuery}
                onChange={e => {
                  setDirSearchQuery(e.target.value);
                  loadDirectory(e.target.value, dirDeptFilter);
                }}
                style={{
                  width: '100%',
                  height: '36px',
                  paddingLeft: '32px',
                  paddingRight: '12px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-ivory)',
                  fontSize: '12px',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', maxHeight: '380px' }}>
              {dirLoading ? (
                <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-graphite)', fontSize: '12px' }}>
                  Querying enterprise directory…
                </div>
              ) : directoryUsers.length === 0 ? (
                <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-graphite)', fontSize: '12px' }}>
                  No directory users found matching criteria.
                </div>
              ) : (
                directoryUsers.map(user => {
                  const alreadyEnrolled = recipients.some(
                    r => r.identity_id === user.identity_id || r.name.toLowerCase() === user.display_name.toLowerCase()
                  );
                  return (
                    <div
                      key={user.identity_id}
                      style={{
                        padding: '10px 12px',
                        borderRadius: '4px',
                        backgroundColor: 'var(--bg-elevated)',
                        border: '1px solid var(--border-subtle)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '12px'
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 500, fontSize: '13px', color: 'var(--text-ivory)' }}>
                          {user.display_name}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-slate)' }}>
                          {user.title} • {user.department}
                        </div>
                        <div style={{ fontSize: '10.5px', color: 'var(--text-graphite)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                          {user.email} • {user.identity_id}
                        </div>
                      </div>

                      <div>
                        {alreadyEnrolled ? (
                          <span
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              fontSize: '11px',
                              color: 'var(--jade-text)',
                              padding: '3px 8px',
                              borderRadius: '4px',
                              backgroundColor: 'var(--jade-bg)',
                              border: '1px solid var(--jade-border)'
                            }}
                          >
                            <UserCheck size={12} />
                            Enrolled
                          </span>
                        ) : (
                          <button
                            onClick={() => handleEnrollFromDir(user)}
                            disabled={enrollingId === user.identity_id}
                            className="btn-primary"
                            style={{ padding: '3px 10px', fontSize: '11px' }}
                          >
                            <Key size={12} />
                            <span>{enrollingId === user.identity_id ? 'Enrolling…' : 'Enroll'}</span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
              <button
                onClick={() => setShowDirectoryModal(false)}
                className="btn-secondary"
                style={{ padding: '6px 14px', fontSize: '12px' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manual / Custom Enroll Modal */}
      {showEnrollModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(11, 16, 21, 0.75)',
            backdropFilter: 'blur(16px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '20px'
          }}
          onClick={() => setShowEnrollModal(false)}
        >
          <div
            className="workstation-card"
            style={{
              maxWidth: '460px',
              width: '100%',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: 'var(--text-ivory)' }}>
                  Enroll Custom Principal
                </h3>
                <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: 'var(--text-slate)' }}>
                  Generates independent ML-KEM-768 and ML-DSA-65 post-quantum keypairs.
                </p>
              </div>
              <button
                onClick={() => setShowEnrollModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-graphite)', cursor: 'pointer', padding: '4px' }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleEnrollSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600, marginBottom: '6px' }}>
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Elena Rostova"
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
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

              <div>
                <label style={{ display: 'block', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600, marginBottom: '6px' }}>
                  Principal ID (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. rec_elena (auto-derived if empty)"
                  value={newId}
                  onChange={e => setNewId(e.target.value)}
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

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
                <button
                  type="button"
                  onClick={() => setShowEnrollModal(false)}
                  className="btn-secondary"
                  style={{ padding: '6px 14px', fontSize: '12px' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary"
                  style={{ padding: '6px 16px', fontSize: '12px' }}
                >
                  {loading ? 'Generating keys…' : 'Enroll principal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

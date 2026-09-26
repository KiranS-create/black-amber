import React, { useState } from 'react';
import { 
  Users, 
  UserPlus, 
  Key, 
  ShieldCheck, 
  Copy, 
  Check, 
  Lock, 
  Search,
  Info,
  ChevronRight,
  Eye
} from 'lucide-react';
import { PublicRecipient } from '../types';
import { StatusBadge, OriginBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';

interface RecipientsTabProps {
  recipients: PublicRecipient[];
  onEnroll: (name: string, id?: string) => Promise<void>;
}

export const RecipientsTab: React.FC<RecipientsTabProps> = ({ recipients, onEnroll }) => {
  const [showEnrollModal, setShowEnrollModal] = useState(false);
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
      (r.role && r.role.toLowerCase().includes(q))
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Registry Table Container */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        {/* Table Action Header */}
        <div
          style={{
            padding: 'var(--space-4) var(--space-6)',
            borderBottom: '1px solid var(--border)',
            backgroundColor: 'var(--surface-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 'var(--space-3)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <div style={{ position: 'relative', width: '280px' }}>
              <Search
                size={14}
                style={{
                  position: 'absolute',
                  left: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-tertiary)'
                }}
              />
              <input
                type="text"
                placeholder="Filter by name, ID, or department..."
                value={searchFilter}
                onChange={e => setSearchFilter(e.target.value)}
                style={{
                  width: '100%',
                  height: '34px',
                  paddingLeft: '32px',
                  paddingRight: '12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--surface)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  fontSize: 'var(--text-xs)',
                  outline: 'none'
                }}
              />
            </div>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
              Showing {filteredRecipients.length} of {recipients.length} enrolled
            </span>
          </div>

          <button
            onClick={() => setShowEnrollModal(true)}
            style={{
              height: '34px',
              padding: '0 14px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              border: 'none',
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'background var(--transition-fast)'
            }}
            onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary-hover)')}
            onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary)')}
          >
            <UserPlus size={14} />
            <span>+ Enroll Recipient</span>
          </button>
        </div>

        {/* Recipients Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 'var(--text-base)' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--surface)' }}>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Recipient</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Identifier</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Origin</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>ML-KEM-768 Capsule Key</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>ML-DSA-65 Signature Key</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Status</th>
                <th style={{ padding: '12px 18px', fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecipients.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                    No enrolled recipients match the search criteria.
                  </td>
                </tr>
              ) : (
                filteredRecipients.map((r, idx) => {
                  const initials = r.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
                  return (
                    <tr
                      key={r.recipient_id}
                      style={{
                        borderBottom: '1px solid var(--border)',
                        backgroundColor: idx % 2 === 0 ? 'transparent' : 'var(--surface-subtle)',
                        transition: 'background var(--transition-fast)'
                      }}
                      onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-hover)')}
                      onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor = idx % 2 === 0 ? 'transparent' : 'var(--surface-subtle)')}
                    >
                      <td style={{ padding: '14px 18px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div
                            style={{
                              width: '32px',
                              height: '32px',
                              borderRadius: 'var(--radius-full)',
                              backgroundColor: 'var(--surface-active)',
                              border: '1px solid var(--border)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '11px',
                              fontWeight: 700,
                              color: 'var(--text)',
                              flexShrink: 0
                            }}
                          >
                            {initials}
                          </div>
                          <div>
                            <div style={{ fontWeight: 600, color: 'var(--text)', fontSize: 'var(--text-base)' }}>
                              {r.name}
                            </div>
                            <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
                              {r.role || 'Authorized Principal'}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td style={{ padding: '14px 18px', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                        <code>{r.recipient_id}</code>
                      </td>

                      <td style={{ padding: '14px 18px' }}>
                        <OriginBadge origin={r.origin} />
                      </td>

                      <td style={{ padding: '14px 18px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <code
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '11px',
                              backgroundColor: 'var(--surface)',
                              border: '1px solid var(--border)',
                              padding: '2px 6px',
                              borderRadius: 'var(--radius-xs)',
                              maxWidth: '120px',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {r.kem_public_key_b64.substring(0, 16)}...
                          </code>
                          <button
                            onClick={() => handleCopy(r.kem_public_key_b64, `${r.recipient_id}-kem`)}
                            title="Copy full 1,184-byte ML-KEM-768 public key"
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: copiedKey === `${r.recipient_id}-kem` ? 'var(--success)' : 'var(--text-tertiary)',
                              cursor: 'pointer',
                              padding: '4px'
                            }}
                          >
                            {copiedKey === `${r.recipient_id}-kem` ? <Check size={13} /> : <Copy size={13} />}
                          </button>
                        </div>
                      </td>

                      <td style={{ padding: '14px 18px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <code
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '11px',
                              backgroundColor: 'var(--surface)',
                              border: '1px solid var(--border)',
                              padding: '2px 6px',
                              borderRadius: 'var(--radius-xs)',
                              maxWidth: '120px',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {r.dsa_public_key_b64.substring(0, 16)}...
                          </code>
                          <button
                            onClick={() => handleCopy(r.dsa_public_key_b64, `${r.recipient_id}-dsa`)}
                            title="Copy full 1,952-byte ML-DSA-65 public key"
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: copiedKey === `${r.recipient_id}-dsa` ? 'var(--success)' : 'var(--text-tertiary)',
                              cursor: 'pointer',
                              padding: '4px'
                            }}
                          >
                            {copiedKey === `${r.recipient_id}-dsa` ? <Check size={13} /> : <Copy size={13} />}
                          </button>
                        </div>
                      </td>

                      <td style={{ padding: '14px 18px' }}>
                        <StatusBadge
                          label={r.status || 'ACTIVE'}
                          variant="success"
                          size="xs"
                          dot
                        />
                      </td>

                      <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                        <button
                          onClick={() => setSelectedRecipient(r)}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '4px 10px',
                            backgroundColor: 'transparent',
                            border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-md)',
                            color: 'var(--text)',
                            fontSize: 'var(--text-xs)',
                            fontWeight: 600,
                            cursor: 'pointer',
                            transition: 'all var(--transition-fast)'
                          }}
                          onMouseEnter={e => {
                            (e.currentTarget as HTMLElement).style.borderColor = 'var(--primary)';
                            (e.currentTarget as HTMLElement).style.color = 'var(--primary-text)';
                          }}
                          onMouseLeave={e => {
                            (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)';
                            (e.currentTarget as HTMLElement).style.color = 'var(--text)';
                          }}
                        >
                          <Eye size={12} />
                          <span>Inspect</span>
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

      {/* Recipient Details Slide-over Drawer */}
      <Drawer
        isOpen={selectedRecipient !== null}
        onClose={() => setSelectedRecipient(null)}
        title={selectedRecipient?.name || 'Recipient Public Keys'}
        subtitle={`ID: ${selectedRecipient?.recipient_id} • Enrolled ${selectedRecipient ? new Date(selectedRecipient.created_at).toLocaleDateString() : ''}`}
        width="540px"
      >
        {selectedRecipient && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
            {/* Identity Summary Card */}
            <div
              style={{
                backgroundColor: 'var(--surface-subtle)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ fontWeight: 700, fontSize: 'var(--text-md)', color: 'var(--text)' }}>
                  {selectedRecipient.name}
                </div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                  {selectedRecipient.role || 'Authorized Entity'}
                </div>
              </div>
              <OriginBadge origin={selectedRecipient.origin} />
            </div>

            {/* Key Isolation Security Note */}
            <div
              style={{
                backgroundColor: 'var(--primary-subtle)',
                border: '1px solid var(--primary-border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-3) var(--space-4)',
                display: 'flex',
                gap: 'var(--space-3)',
                alignItems: 'flex-start'
              }}
            >
              <Lock size={16} style={{ color: 'var(--primary)', flexShrink: 0, marginTop: '2px' }} />
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--primary-text)', lineHeight: 1.4 }}>
                <strong>Key Isolation Boundary:</strong> Only public keys are stored in the Central Authority Registry. Private decapsulation keys never leave client custody.
              </div>
            </div>

            {/* ML-KEM-768 Details */}
            <div
              style={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--text)' }}>
                  ML-KEM-768 Public Key (FIPS 203)
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                  1,184 Bytes
                </span>
              </div>
              <div
                style={{
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-xs)',
                  padding: 'var(--space-3)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11.5px',
                  color: 'var(--text-secondary)',
                  wordBreak: 'break-all',
                  maxHeight: '120px',
                  overflowY: 'auto'
                }}
              >
                {selectedRecipient.kem_public_key_b64}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
                <button
                  onClick={() => handleCopy(selectedRecipient.kem_public_key_b64, 'drawer-kem')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '4px 10px',
                    backgroundColor: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '11.5px',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer'
                  }}
                >
                  {copiedKey === 'drawer-kem' ? <Check size={12} color="var(--success)" /> : <Copy size={12} />}
                  <span>{copiedKey === 'drawer-kem' ? 'Copied' : 'Copy Base64'}</span>
                </button>
              </div>
            </div>

            {/* ML-DSA-65 Details */}
            <div
              style={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--text)' }}>
                  ML-DSA-65 Verification Public Key (FIPS 204)
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                  1,952 Bytes
                </span>
              </div>
              <div
                style={{
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-xs)',
                  padding: 'var(--space-3)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11.5px',
                  color: 'var(--text-secondary)',
                  wordBreak: 'break-all',
                  maxHeight: '120px',
                  overflowY: 'auto'
                }}
              >
                {selectedRecipient.dsa_public_key_b64}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
                <button
                  onClick={() => handleCopy(selectedRecipient.dsa_public_key_b64, 'drawer-dsa')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '4px 10px',
                    backgroundColor: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '11.5px',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer'
                  }}
                >
                  {copiedKey === 'drawer-dsa' ? <Check size={12} color="var(--success)" /> : <Copy size={12} />}
                  <span>{copiedKey === 'drawer-dsa' ? 'Copied' : 'Copy Base64'}</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </Drawer>

      {/* Enroll Modal */}
      {showEnrollModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 110,
            padding: '20px'
          }}
          onClick={() => setShowEnrollModal(false)}
        >
          <div
            style={{
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border-strong)',
              borderRadius: 'var(--radius-lg)',
              maxWidth: '460px',
              width: '100%',
              padding: 'var(--space-6)',
              boxShadow: 'var(--shadow-lg)'
            }}
            onClick={e => e.stopPropagation()}
          >
            <h3 style={{ margin: '0 0 4px 0', fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)' }}>
              Enroll New Cryptographic Recipient
            </h3>
            <p style={{ margin: '0 0 var(--space-4) 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              Generates independent ML-KEM-768 and ML-DSA-65 post-quantum keypairs.
            </p>

            <form onSubmit={handleEnrollSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div>
                <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Maya Patel"
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
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

              <div>
                <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>
                  Recipient ID (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. maya (auto-derived if empty)"
                  value={newId}
                  onChange={e => setNewId(e.target.value)}
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

              <div
                style={{
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-3)',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  gap: '8px',
                  alignItems: 'flex-start'
                }}
              >
                <Info size={15} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--primary)' }} />
                <span>Generates post-quantum public keys registered directly in the authority key store.</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
                <button
                  type="button"
                  onClick={() => setShowEnrollModal(false)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'transparent',
                    border: '1px solid var(--border)',
                    color: 'var(--text-secondary)',
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    padding: '8px 18px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--primary)',
                    color: '#ffffff',
                    border: 'none',
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  {loading ? 'Generating...' : 'Enroll Recipient'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

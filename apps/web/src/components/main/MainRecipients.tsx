import React, { useState } from 'react';
import { PublicRecipient } from '../../types';
import { 
  Users, 
  UserPlus, 
  ShieldCheck, 
  Key, 
  Trash2, 
  Search, 
  Copy, 
  Check, 
  Cpu, 
  ExternalLink, 
  Sparkles, 
  ArrowRight,
  Flame,
  X,
  Lock,
  Building,
  Terminal,
  ShieldAlert
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

interface MainRecipientsProps {
  recipients: PublicRecipient[];
  onEnrollRecipient: (
    name: string, 
    id?: string, 
    role?: string, 
    terminalId?: string, 
    department?: string, 
    clearance?: string
  ) => Promise<void>;
  onDeleteRecipient: (recipientId: string) => Promise<void>;
  onOpenDecryptionPortal: (recipientId?: string) => void;
  onTestLeakAttribution: (recipient: PublicRecipient) => void;
}

export const MainRecipients: React.FC<MainRecipientsProps> = ({
  recipients,
  onEnrollRecipient,
  onDeleteRecipient,
  onOpenDecryptionPortal,
  onTestLeakAttribution
}) => {
  const { theme } = useTheme();
  const isLight = theme === 'light';

  const [searchTerm, setSearchTerm] = useState('');
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Form State
  const [formName, setFormName] = useState('');
  const [formId, setFormId] = useState('');
  const [formRole, setFormRole] = useState('');
  const [formDepartment, setFormDepartment] = useState('');
  const [formTerminal, setFormTerminal] = useState('');
  const [formClearance, setFormClearance] = useState('TOP SECRET // LEVEL 4');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [recipientToDelete, setRecipientToDelete] = useState<PublicRecipient | null>(null);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleEnrollSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) return;

    setIsSubmitting(true);
    try {
      const cleanId = (formId.trim() || formName.trim().toLowerCase().replace(/[^a-z0-9]/g, '_')).slice(0, 32);
      const cleanTerminal = formTerminal.trim() || `Field Terminal #ST-${Math.floor(100000 + Math.random() * 900000)}`;
      await onEnrollRecipient(
        formName.trim(),
        cleanId,
        formRole.trim() || 'Principal Intelligence Officer',
        cleanTerminal,
        formDepartment.trim() || 'Strategic Defense Operations',
        formClearance
      );

      // Reset form
      setFormName('');
      setFormId('');
      setFormRole('');
      setFormDepartment('');
      setFormTerminal('');
      setFormClearance('TOP SECRET // LEVEL 4');
      setShowEnrollModal(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredRecipients = recipients.filter(r => {
    const q = searchTerm.toLowerCase();
    return (
      r.name.toLowerCase().includes(q) ||
      r.recipient_id.toLowerCase().includes(q) ||
      (r.role && r.role.toLowerCase().includes(q)) ||
      (r.department && r.department.toLowerCase().includes(q)) ||
      (r.terminal_id && r.terminal_id.toLowerCase().includes(q))
    );
  });

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="main-title">Principals & Terminals</h1>
          <p className="main-subtitle">
            Sovereign post-quantum public key registry. Enroll authorized defense officers, map dedicated field terminal enclaves, and test attribution without limits.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setShowEnrollModal(true)}
            className="main-btn-primary"
            style={{ fontSize: '12px' }}
          >
            <UserPlus size={14} />
            <span>Enroll Officer & Terminal</span>
          </button>
        </div>
      </div>

      {/* Stats Counter Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
        <div className="main-card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
            Enrolled Principals
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--main-text-primary)', marginTop: '4px' }}>
            {recipients.length}
          </div>
          <div style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
            Individual cryptographic profiles active
          </div>
        </div>

        <div className="main-card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
            Field Terminals
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--main-accent)', marginTop: '4px' }}>
            {recipients.length} Enclaves
          </div>
          <div style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
            Isolated in-memory decapsulation units
          </div>
        </div>

        <div className="main-card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
            Post-Quantum Suite
          </div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--main-jade)', marginTop: '4px' }}>
            ML-KEM-768 + ML-DSA-65
          </div>
          <div style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
            NIST FIPS 203 & 204 verified
          </div>
        </div>
      </div>

      {/* Search & Action Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', width: '360px', maxWidth: '100%' }}>
          <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--main-text-tertiary)' }} />
          <input
            type="text"
            placeholder="Search by name, callsign, rank, terminal..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              height: '36px',
              paddingLeft: '34px',
              paddingRight: '12px',
              borderRadius: '8px',
              border: '1px solid var(--main-border)',
              background: 'var(--main-surface)',
              color: 'var(--main-text-primary)',
              fontSize: '12px',
              outline: 'none',
              boxSizing: 'border-box'
            }}
          />
        </div>
        <div style={{ fontSize: '12px', color: 'var(--main-text-tertiary)' }}>
          Showing {filteredRecipients.length} of {recipients.length} enrolled principals
        </div>
      </div>

      {/* Recipients Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        {filteredRecipients.map(r => {
          const terminalDisplay = r.terminal_id || `Field Terminal #ST-${r.recipient_id.toUpperCase()}`;
          const clearanceDisplay = r.clearance || 'TOP SECRET // LEVEL 4';
          const deptDisplay = r.department || 'Strategic Intelligence Division';

          return (
            <div 
              key={r.recipient_id}
              className="main-card glass-panel"
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                padding: '20px',
                borderRadius: '16px',
                border: '1px solid var(--main-border)',
                background: 'var(--main-surface)',
                gap: '14px',
                transition: 'all 0.2s ease'
              }}
            >
              <div>
                {/* Top Row: Clearance & Status */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span className="main-badge" style={{ fontSize: '10px', background: 'rgba(56, 189, 248, 0.12)', color: '#38BDF8', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
                    {clearanceDisplay}
                  </span>
                  <span className="main-badge main-badge-verified" style={{ fontSize: '10px' }}>
                    <ShieldCheck size={10} />
                    {r.status || 'ACTIVE'}
                  </span>
                </div>

                {/* Name & Role */}
                <h3 style={{ fontSize: '16px', fontWeight: 650, color: 'var(--main-text-primary)', margin: 0 }}>
                  {r.name}
                </h3>
                <div style={{ fontSize: '12px', color: 'var(--main-text-secondary)', marginTop: '2px', fontWeight: 500 }}>
                  {r.role || 'Authorized Principal'}
                </div>
                <div style={{ fontSize: '11.5px', color: 'var(--main-text-tertiary)', marginTop: '2px' }}>
                  {deptDisplay}
                </div>

                {/* Terminal Info */}
                <div style={{ 
                  marginTop: '12px', 
                  padding: '10px 12px', 
                  background: 'var(--main-surface-elevated)', 
                  borderRadius: '10px', 
                  border: '1px solid var(--main-border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Terminal size={13} style={{ color: 'var(--main-accent)' }} />
                    <span className="main-mono" style={{ fontSize: '11px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                      {terminalDisplay}
                    </span>
                  </div>
                  <span className="main-mono" style={{ fontSize: '10.5px', color: 'var(--main-text-tertiary)' }}>
                    ID: {r.recipient_id}
                  </span>
                </div>

                {/* PQC Public Key Fingerprint */}
                <div style={{ marginTop: '10px', fontSize: '11px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--main-text-tertiary)' }}>
                  <span className="main-mono" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '220px' }}>
                    KEM: {r.kem_public_key_b64 ? r.kem_public_key_b64.slice(0, 22) + '...' : 'ML-KEM-768'}
                  </span>
                  <button
                    onClick={() => handleCopy(r.kem_public_key_b64 || r.recipient_id, r.recipient_id)}
                    className="main-btn-ghost"
                    style={{ padding: '2px 6px', fontSize: '10.5px' }}
                    title="Copy Public Key"
                  >
                    {copiedKey === r.recipient_id ? <Check size={11} style={{ color: 'var(--main-jade)' }} /> : <Copy size={11} />}
                    <span>{copiedKey === r.recipient_id ? 'Copied' : 'Key'}</span>
                  </button>
                </div>
              </div>

              {/* Bottom Actions */}
              <div style={{ 
                paddingTop: '12px', 
                borderTop: '1px solid var(--main-border)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '8px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <button
                    onClick={() => onOpenDecryptionPortal(r.recipient_id)}
                    className="main-btn-secondary"
                    style={{ fontSize: '11.5px', padding: '5px 10px' }}
                    title="Simulate In-Memory Decryption for this Officer"
                  >
                    <Lock size={12} />
                    <span>Decrypt</span>
                  </button>

                  <button
                    onClick={() => onTestLeakAttribution(r)}
                    className="main-btn-primary"
                    style={{ fontSize: '11.5px', padding: '5px 12px', background: '#0284C7' }}
                    title="Simulate a leak and test 100% forensic attribution for this officer"
                  >
                    <Sparkles size={12} />
                    <span>Test Attribution</span>
                  </button>
                </div>

                <button
                  onClick={() => setRecipientToDelete(r)}
                  className="main-btn-ghost"
                  style={{ padding: '6px', color: '#EF4444' }}
                  title="Remove this principal"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal: Enroll Officer & Terminal */}
      {showEnrollModal && (
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
            borderRadius: '16px',
            width: '100%',
            maxWidth: '520px',
            padding: '24px',
            boxShadow: '0 24px 48px rgba(0, 0, 0, 0.45)',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: 'rgba(56, 189, 248, 0.15)',
                  color: '#38BDF8',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <UserPlus size={18} />
                </div>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 650, color: 'var(--main-text-primary)', margin: 0 }}>
                    Enroll Principal & Field Terminal
                  </h3>
                  <p style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', margin: '2px 0 0 0' }}>
                    Generate NIST PQC keypairs and register a dedicated hardware enclave.
                  </p>
                </div>
              </div>
              <button onClick={() => setShowEnrollModal(false)} className="main-btn-ghost" style={{ padding: '6px' }}>
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleEnrollSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Officer Full Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Commander Vikram Rao, Col. Anita Desai"
                  value={formName}
                  onChange={e => setFormName(e.target.value)}
                  style={{
                    width: '100%',
                    height: '36px',
                    padding: '0 12px',
                    borderRadius: '8px',
                    border: '1px solid var(--main-border)',
                    background: 'var(--main-surface-elevated)',
                    color: 'var(--main-text-primary)',
                    fontSize: '12.5px',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                    Principal ID / Callsign
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. vikram_rao (auto if blank)"
                    value={formId}
                    onChange={e => setFormId(e.target.value)}
                    style={{
                      width: '100%',
                      height: '36px',
                      padding: '0 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--main-border)',
                      background: 'var(--main-surface-elevated)',
                      color: 'var(--main-text-primary)',
                      fontSize: '12.5px',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                    Field Terminal ID
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Field Terminal #ST-8821"
                    value={formTerminal}
                    onChange={e => setFormTerminal(e.target.value)}
                    style={{
                      width: '100%',
                      height: '36px',
                      padding: '0 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--main-border)',
                      background: 'var(--main-surface-elevated)',
                      color: 'var(--main-text-primary)',
                      fontSize: '12.5px',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                    Rank / Role
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Director of Naval Comms"
                    value={formRole}
                    onChange={e => setFormRole(e.target.value)}
                    style={{
                      width: '100%',
                      height: '36px',
                      padding: '0 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--main-border)',
                      background: 'var(--main-surface-elevated)',
                      color: 'var(--main-text-primary)',
                      fontSize: '12.5px',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                    Department / Unit
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Tactical Operations Wing"
                    value={formDepartment}
                    onChange={e => setFormDepartment(e.target.value)}
                    style={{
                      width: '100%',
                      height: '36px',
                      padding: '0 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--main-border)',
                      background: 'var(--main-surface-elevated)',
                      color: 'var(--main-text-primary)',
                      fontSize: '12.5px',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--main-text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Security Clearance Level
                </label>
                <select
                  value={formClearance}
                  onChange={e => setFormClearance(e.target.value)}
                  style={{
                    width: '100%',
                    height: '36px',
                    padding: '0 12px',
                    borderRadius: '8px',
                    border: '1px solid var(--main-border)',
                    background: 'var(--main-surface-elevated)',
                    color: 'var(--main-text-primary)',
                    fontSize: '12.5px',
                    boxSizing: 'border-box'
                  }}
                >
                  <option value="TOP SECRET // LEVEL 4">TOP SECRET // LEVEL 4 (Strategic Directorate)</option>
                  <option value="SECRET // LEVEL 3">SECRET // LEVEL 3 (Operational Command)</option>
                  <option value="CONFIDENTIAL // LEVEL 2">CONFIDENTIAL // LEVEL 2 (Tactical Field)</option>
                  <option value="RESTRICTED // LEVEL 1">RESTRICTED // LEVEL 1 (Partner/External)</option>
                </select>
              </div>

              <div style={{ 
                padding: '12px', 
                background: 'rgba(56, 189, 248, 0.08)', 
                borderRadius: '8px', 
                border: '1px solid rgba(56, 189, 248, 0.2)',
                fontSize: '11.5px',
                color: 'var(--main-text-secondary)',
                lineHeight: 1.4
              }}>
                ✦ <strong>Auto-Provisioning:</strong> Enrolling provisions a unique <strong>ML-KEM-768</strong> decapsulation key and <strong>ML-DSA-65</strong> signature key with an isolated Tardos traitor-tracing codeword.
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
                <button
                  type="button"
                  onClick={() => setShowEnrollModal(false)}
                  className="main-btn-secondary"
                  style={{ padding: '8px 16px', fontSize: '12px' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !formName.trim()}
                  className="main-btn-primary"
                  style={{ padding: '8px 20px', fontSize: '12px' }}
                >
                  {isSubmitting ? 'Minting Keys...' : 'Authorize & Mint Keys'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Delete Recipient Confirmation */}
      {recipientToDelete && (
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
            borderRadius: '16px',
            width: '100%',
            maxWidth: '440px',
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
                <h3 style={{ fontSize: '15px', fontWeight: 650, color: 'var(--main-text-primary)', margin: 0 }}>
                  Revoke & Remove Principal
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--main-text-tertiary)', margin: '2px 0 0 0' }}>
                  De-provision post-quantum enclave credentials
                </p>
              </div>
            </div>

            <p style={{ fontSize: '12.5px', color: 'var(--main-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Are you sure you want to remove <strong>{recipientToDelete.name}</strong> ({recipientToDelete.recipient_id})? Their field terminal and keypair will be permanently de-registered.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setRecipientToDelete(null)}
                className="main-btn-secondary"
                style={{ padding: '7px 14px', fontSize: '12px' }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={async () => {
                  if (recipientToDelete) {
                    await onDeleteRecipient(recipientToDelete.recipient_id);
                    setRecipientToDelete(null);
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
                  cursor: 'pointer'
                }}
              >
                Confirm Revocation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

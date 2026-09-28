import React, { useState } from 'react';
import { 
  Building, 
  Search, 
  Users, 
  UserCheck, 
  Key, 
  Copy, 
  Check, 
  ShieldAlert
} from 'lucide-react';
import { DirectoryIdentity, PublicRecipient } from '../types';
import { StatusBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';
import { EmptyState } from './common/EmptyState';

interface DirectoryTabProps {
  identities: DirectoryIdentity[];
  recipients: PublicRecipient[];
  onEnrollFromDirectory: (identityId: string, role?: string) => Promise<void>;
  onRevokeRecipient: (recipientId: string) => Promise<void>;
  setActiveTab: (tab: any) => void;
}

export const DirectoryTab: React.FC<DirectoryTabProps> = ({
  identities,
  recipients,
  onEnrollFromDirectory,
  onRevokeRecipient,
  setActiveTab
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [providerFilter, setProviderFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedIdentity, setSelectedIdentity] = useState<DirectoryIdentity | null>(null);
  const [enrollingId, setEnrollingId] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const filteredIdentities = identities.filter(ident => {
    const matchesSearch = 
      ident.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ident.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ident.identity_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (ident.department && ident.department.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (ident.title && ident.title.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesProvider = providerFilter === 'ALL' || ident.provider.toLowerCase().includes(providerFilter.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || ident.status === statusFilter;

    return matchesSearch && matchesProvider && matchesStatus;
  });

  const getRecipientForIdentity = (ident: DirectoryIdentity) => {
    return recipients.find(r => 
      r.identity_id === ident.identity_id || 
      r.name.toLowerCase() === ident.display_name.toLowerCase()
    );
  };

  const handleEnroll = async (ident: DirectoryIdentity) => {
    setEnrollingId(ident.identity_id);
    try {
      await onEnrollFromDirectory(ident.identity_id, ident.title || 'Specialist');
    } catch (err) {
      console.error('Enrollment failed:', err);
    } finally {
      setEnrollingId(null);
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const boundRecipient = selectedIdentity ? getRecipientForIdentity(selectedIdentity) : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600, color: 'var(--text-ivory)', letterSpacing: '-0.01em' }}>
            Enterprise Directory
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-slate)', maxWidth: '640px' }}>
            Authoritative enterprise identities federated from Microsoft Entra ID, Okta, and Active Directory with isolated PQC keypairs.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('integrations')}
          className="btn-secondary"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <Building size={14} style={{ color: 'var(--petrol)' }} />
          <span>Directory integrations</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div style={{ position: 'relative', width: '340px', maxWidth: '100%' }}>
          <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-graphite)' }} />
          <input
            type="text"
            placeholder="Search by name, email, department, or ID…"
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

        {/* Filter Segmented Control */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px', backgroundColor: 'var(--bg-elevated)', padding: '3px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
          {[
            { id: 'ALL', label: 'All providers' },
            { id: 'entra', label: 'Entra ID' },
            { id: 'okta', label: 'Okta' },
            { id: 'local', label: 'Local AD' }
          ].map(p => (
            <button
              key={p.id}
              onClick={() => setProviderFilter(p.id)}
              style={{
                height: '28px',
                padding: '0 10px',
                borderRadius: '3px',
                border: 'none',
                backgroundColor: providerFilter === p.id ? 'var(--bg-surface)' : 'transparent',
                color: providerFilter === p.id ? 'var(--text-ivory)' : 'var(--text-slate)',
                fontSize: '11px',
                fontWeight: providerFilter === p.id ? 600 : 400,
                cursor: 'pointer',
                transition: 'background var(--transition-fast)'
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Directory Table or Empty State */}
      {identities.length === 0 ? (
        <div className="workstation-card">
          <EmptyState
            icon={Building}
            title="No Directory Identities Found"
            description="Federate enterprise identities from Microsoft Entra ID, Okta, or Active Directory to authorize individual post-quantum cryptographic keys."
            primaryAction={{
              label: 'Configure directory integrations',
              onClick: () => setActiveTab('integrations'),
              icon: Building
            }}
          />
        </div>
      ) : (
        <div className="workstation-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table className="evidence-table">
            <thead>
              <tr>
                <th>Identity</th>
                <th>Department & Role</th>
                <th>Email</th>
                <th>Identity Provider</th>
                <th>Account Status</th>
                <th>PQC Principal</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredIdentities.map(ident => {
                const rec = getRecipientForIdentity(ident);
                const isEnrolled = !!rec && rec.status !== 'REVOKED';
                const isRevoked = !!rec && rec.status === 'REVOKED';
                const isSelected = selectedIdentity?.identity_id === ident.identity_id;

                return (
                  <tr
                    key={ident.identity_id}
                    onClick={() => setSelectedIdentity(ident)}
                    style={{
                      backgroundColor: isSelected ? 'rgba(76, 154, 154, 0.08)' : undefined,
                      cursor: 'pointer'
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
                            color: 'var(--text-slate)',
                            fontWeight: 600,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '11px',
                            border: '1px solid var(--border-subtle)'
                          }}
                        >
                          {ident.display_name.substring(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <div style={{ fontWeight: 500, color: 'var(--text-ivory)', fontSize: '13px' }}>
                            {ident.display_name}
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--text-graphite)', fontFamily: 'var(--font-mono)' }}>
                            {ident.identity_id}
                          </div>
                        </div>
                      </div>
                    </td>

                    <td>
                      <div style={{ fontWeight: 500, color: 'var(--text-ivory)', fontSize: '12px' }}>
                        {ident.department || 'Operations'}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>
                        {ident.title || 'Specialist'}
                      </div>
                    </td>

                    <td style={{ color: 'var(--text-slate)', fontSize: '12px' }}>
                      {ident.email}
                    </td>

                    <td>
                      <span style={{ fontSize: '12px', color: 'var(--text-slate)' }}>
                        {ident.provider === 'local_enterprise_directory' ? 'Active Directory / LDAP' : ident.provider}
                      </span>
                    </td>

                    <td>
                      <StatusBadge
                        label={ident.status === 'ACTIVE' ? 'Active' : 'Suspended'}
                        variant={ident.status === 'ACTIVE' ? 'success' : 'warning'}
                        size="xs"
                      />
                    </td>

                    <td>
                      <StatusBadge
                        label={isEnrolled ? 'Enrolled (ML-KEM-768)' : (isRevoked ? 'Revoked' : 'Unprovisioned')}
                        variant={isEnrolled ? 'success' : (isRevoked ? 'danger' : 'neutral')}
                        size="xs"
                      />
                    </td>

                    <td style={{ textAlign: 'right' }}>
                      {isEnrolled ? (
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            setSelectedIdentity(ident);
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
                        >
                          Keys
                        </button>
                      ) : (
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            handleEnroll(ident);
                          }}
                          disabled={enrollingId === ident.identity_id}
                          className="btn-primary"
                          style={{
                            padding: '3px 10px',
                            fontSize: '11px'
                          }}
                        >
                          {enrollingId === ident.identity_id ? 'Enrolling…' : 'Enroll PQC'}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      )}

      {/* Identity Detail Drawer */}
      <Drawer
        isOpen={!!selectedIdentity}
        onClose={() => setSelectedIdentity(null)}
        title={selectedIdentity?.display_name || 'Identity Details'}
        subtitle={`Directory ID: ${selectedIdentity?.identity_id || ''}`}
        width="480px"
      >
        {selectedIdentity && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Identity Profile Details */}
            <div>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600, marginBottom: '10px' }}>
                Profile Attributes
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '10px 16px', fontSize: '12px' }}>
                <span style={{ color: 'var(--text-graphite)' }}>Display name</span>
                <span style={{ color: 'var(--text-ivory)', fontWeight: 500 }}>{selectedIdentity.display_name}</span>

                <span style={{ color: 'var(--text-graphite)' }}>Role / Title</span>
                <span style={{ color: 'var(--text-slate)' }}>{selectedIdentity.title}</span>

                <span style={{ color: 'var(--text-graphite)' }}>Department</span>
                <span style={{ color: 'var(--text-slate)' }}>{selectedIdentity.department}</span>

                <span style={{ color: 'var(--text-graphite)' }}>Email</span>
                <span style={{ color: 'var(--text-slate)', fontFamily: 'var(--font-mono)' }}>{selectedIdentity.email}</span>

                <span style={{ color: 'var(--text-graphite)' }}>Provider</span>
                <span style={{ color: 'var(--text-slate)' }}>{selectedIdentity.provider}</span>
              </div>
            </div>

            {/* Cryptographic Principal Binding */}
            {boundRecipient ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600 }}>
                  Cryptographic Keys (ML-KEM-768 / ML-DSA-65)
                </div>

                <div style={{ padding: '10px 12px', borderRadius: '4px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', fontSize: '12px' }}>
                  <div style={{ color: 'var(--text-graphite)', fontSize: '11px' }}>Principal Identifier</div>
                  <code style={{ fontSize: '12px', color: 'var(--text-ivory)', fontWeight: 500 }}>{boundRecipient.recipient_id}</code>
                </div>

                {/* ML-KEM-768 Public Key */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>ML-KEM-768 Public Key (1,184 B)</span>
                    <button
                      onClick={() => handleCopy(boundRecipient.kem_public_key_b64, 'kem')}
                      style={{ fontSize: '11px', color: copiedKey === 'kem' ? 'var(--jade)' : 'var(--text-graphite)', backgroundColor: 'transparent', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      {copiedKey === 'kem' ? <Check size={12} /> : <Copy size={12} />}
                      <span>{copiedKey === 'kem' ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <div style={{ padding: '8px 10px', borderRadius: '4px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '10.5px', color: 'var(--text-slate)', wordBreak: 'break-all' }}>
                    {boundRecipient.kem_public_key_b64}
                  </div>
                </div>

                {/* ML-DSA-65 Public Key */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>ML-DSA-65 Verification Key (1,952 B)</span>
                    <button
                      onClick={() => handleCopy(boundRecipient.dsa_public_key_b64, 'dsa')}
                      style={{ fontSize: '11px', color: copiedKey === 'dsa' ? 'var(--jade)' : 'var(--text-graphite)', backgroundColor: 'transparent', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      {copiedKey === 'dsa' ? <Check size={12} /> : <Copy size={12} />}
                      <span>{copiedKey === 'dsa' ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <div style={{ padding: '8px 10px', borderRadius: '4px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '10.5px', color: 'var(--text-slate)', wordBreak: 'break-all' }}>
                    {boundRecipient.dsa_public_key_b64}
                  </div>
                </div>

                {boundRecipient.status === 'ACTIVE' && (
                  <button
                    onClick={async () => {
                      await onRevokeRecipient(boundRecipient.recipient_id);
                      setSelectedIdentity(null);
                    }}
                    className="btn-danger"
                    style={{ marginTop: '8px', width: '100%', justifyContent: 'center' }}
                  >
                    Revoke cryptographic principal
                  </button>
                )}
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-slate)', lineHeight: 1.5 }}>
                  This enterprise identity has not yet been provisioned with post-quantum keypairs.
                </p>
                <button
                  onClick={async () => {
                    await handleEnroll(selectedIdentity);
                    setSelectedIdentity(null);
                  }}
                  className="btn-primary"
                  style={{ width: '100%', justifyContent: 'center' }}
                >
                  Generate PQC keypair & enroll principal
                </button>
              </div>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
};

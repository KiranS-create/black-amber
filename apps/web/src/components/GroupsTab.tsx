import React, { useState } from 'react';
import { 
  Network, 
  ShieldCheck, 
  Package, 
  Info,
  Building
} from 'lucide-react';
import { DirectoryGroup, DirectoryIdentity, PublicRecipient } from '../types';
import { StatusBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';
import { EmptyState } from './common/EmptyState';

interface GroupsTabProps {
  groups: DirectoryGroup[];
  identities: DirectoryIdentity[];
  recipients: PublicRecipient[];
  setActiveTab: (tab: any) => void;
  onSelectGroupForRelease?: (groupId: string) => void;
}

export const GroupsTab: React.FC<GroupsTabProps> = ({
  groups,
  identities,
  recipients,
  setActiveTab,
  onSelectGroupForRelease
}) => {
  const [selectedGroup, setSelectedGroup] = useState<DirectoryGroup | null>(null);

  // Group member mapping
  const getGroupMembers = (groupId: string): DirectoryIdentity[] => {
    switch (groupId) {
      case 'grp_cyber_secops':
        return identities.filter(i => (i.department && i.department.includes('Cyber')) || i.tags?.includes('incident_responder'));
      case 'grp_strategic_intel':
        return identities.filter(i => (i.department && (i.department.includes('Intelligence') || i.department.includes('Research'))));
      case 'grp_contractors':
        return identities.filter(i => (i.department && i.department.includes('Contractor')) || i.tags?.includes('contractor'));
      case 'grp_exec_leadership':
        return identities.filter(i => (i.department && (i.department.includes('Leadership') || i.department.includes('Legal'))));
      default:
        return identities.slice(0, 2);
    }
  };

  const selectedGroupMembers = selectedGroup ? getGroupMembers(selectedGroup.group_id) : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600, color: 'var(--text-ivory)', letterSpacing: '-0.01em' }}>
            Security Groups & Targeting
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-slate)', maxWidth: '640px' }}>
            Enterprise directory access roles with strict zero-shared-key isolation guarantees.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('releases')}
          className="btn-primary"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
        >
          <Package size={14} />
          <span>Create targeted release</span>
        </button>
      </div>

      {/* Architectural Guarantee Callout */}
      <div
        style={{
          backgroundColor: 'rgba(76, 154, 154, 0.08)',
          border: '1px solid rgba(76, 154, 154, 0.2)',
          borderRadius: '6px',
          padding: '14px 16px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px'
        }}
      >
        <ShieldCheck size={18} style={{ color: 'var(--petrol)', flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '12px', lineHeight: 1.5 }}>
          <strong style={{ color: 'var(--text-ivory)', fontSize: '13px' }}>
            Cryptographic Invariant: Zero Shared Group Keys
          </strong>
          <div style={{ color: 'var(--text-slate)', marginTop: '2px' }}>
            When releasing documents to a directory group, AegisTrace does not generate a collective group key. The release engine expands the group into its constituent enterprise principals, generating an independent <strong>ML-KEM-768 ciphertext capsule</strong> for every individual member. This ensures unfalsifiable attribution and non-repudiation during subsequent leak investigations.
          </div>
        </div>
      </div>

      {/* Groups Table or Empty State */}
      {groups.length === 0 ? (
        <div className="workstation-card">
          <EmptyState
            icon={Network}
            title="No Security Groups Configured"
            description="Enterprise directory security groups map access control lists to isolated cryptographic principal keypairs with zero shared keys."
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
                <th>Security Group</th>
                <th>Organization</th>
                <th>Principals</th>
                <th>Cryptographic Fan-Out</th>
                <th>Description</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {groups.map(grp => {
                const members = getGroupMembers(grp.group_id);
                const isSelected = selectedGroup?.group_id === grp.group_id;

                return (
                  <tr
                    key={grp.group_id}
                    onClick={() => setSelectedGroup(grp)}
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
                            border: '1px solid var(--border-subtle)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'var(--petrol)',
                            flexShrink: 0
                          }}
                        >
                          <Network size={14} />
                        </div>
                        <div>
                          <div style={{ fontWeight: 500, color: 'var(--text-ivory)', fontSize: '13px' }}>
                            {grp.name}
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--text-graphite)', fontFamily: 'var(--font-mono)' }}>
                            {grp.group_id}
                          </div>
                        </div>
                      </div>
                    </td>

                    <td style={{ color: 'var(--text-slate)', fontSize: '12px' }}>
                      {grp.organization_id}
                    </td>

                    <td>
                      <span style={{ fontWeight: 500, color: 'var(--text-ivory)', fontSize: '12px' }}>
                        {members.length} {members.length === 1 ? 'principal' : 'principals'}
                      </span>
                    </td>

                    <td>
                      <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', padding: '2px 8px', borderRadius: '4px', backgroundColor: 'var(--bg-elevated)', color: 'var(--petrol)', border: '1px solid var(--border-subtle)' }}>
                        O(1) payload + O(N) capsules
                      </span>
                    </td>

                    <td style={{ color: 'var(--text-slate)', fontSize: '12px', maxWidth: '320px' }}>
                      {grp.description || 'Enterprise role group'}
                    </td>

                    <td style={{ textAlign: 'right' }}>
                      <button
                        onClick={e => {
                          e.stopPropagation();
                          setSelectedGroup(grp);
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
                        Inspect members
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      )}

      {/* Right Drawer: Group Member Expansion */}
      <Drawer
        isOpen={!!selectedGroup}
        onClose={() => setSelectedGroup(null)}
        title={selectedGroup?.name || 'Group Details'}
        subtitle={`ID: ${selectedGroup?.group_id || ''}`}
        width="480px"
      >
        {selectedGroup && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div
              style={{
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '14px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px'
              }}
            >
              <div style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)' }}>
                Targeting Group Profile
              </div>
              <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-ivory)' }}>
                {selectedGroup.name}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-slate)' }}>
                {selectedGroup.description}
              </div>
            </div>

            {/* Individual Member Expansion */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)' }}>
                  Individual Member Capsules ({selectedGroupMembers.length})
                </span>
                <span style={{ fontSize: '11px', color: 'var(--jade-text)' }}>
                  Isolated keypairs
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {selectedGroupMembers.map(member => {
                  const rec = recipients.find(r => r.identity_id === member.identity_id || r.name.toLowerCase() === member.display_name.toLowerCase());
                  const isEnrolled = !!rec && rec.status !== 'REVOKED';

                  return (
                    <div
                      key={member.identity_id}
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
                        <div style={{ fontWeight: 500, color: 'var(--text-ivory)', fontSize: '12.5px' }}>
                          {member.display_name}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>
                          {member.title} • {member.department}
                        </div>
                      </div>

                      <StatusBadge
                        label={isEnrolled ? 'Capsule ready' : 'Not enrolled'}
                        variant={isEnrolled ? 'success' : 'neutral'}
                        size="xs"
                      />
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Action */}
            <button
              onClick={() => {
                if (onSelectGroupForRelease) onSelectGroupForRelease(selectedGroup.group_id);
                setActiveTab('releases');
                setSelectedGroup(null);
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
              <span>Target this group in release</span>
            </button>
          </div>
        )}
      </Drawer>
    </div>
  );
};

import React, { useState } from 'react';
import { 
  FileCheck, 
  Search, 
  Binary, 
  ShieldCheck, 
  Cpu, 
  Database,
  Copy, 
  Check, 
  ExternalLink,
  Filter,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { EvidenceRecord } from '../types';
import { StatusBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';
import { EmptyState } from './common/EmptyState';

interface EvidenceTabProps {
  records?: EvidenceRecord[];
  setActiveTab: (tab: any) => void;
}

export const EvidenceTab: React.FC<EvidenceTabProps> = ({ 
  records = [], 
  setActiveTab 
}) => {
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceRecord | null>(null);
  const [channelFilter, setChannelFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedHash, setCopiedHash] = useState(false);
  const [showTechDetails, setShowTechDetails] = useState(false);

  const filteredEvidence = records.filter(ev => {
    const matchesChannel = channelFilter === 'ALL' || ev.source_channel === channelFilter;
    const matchesSearch = 
      ev.evidence_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.channel_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.suspected_candidate_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.raw_proof.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesChannel && matchesSearch;
  });

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* 1. Page Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--space-4)',
          paddingBottom: 'var(--space-4)',
          borderBottom: '1px solid var(--border)'
        }}
      >
        <div>
          <h1
            style={{
              margin: 0,
              fontSize: 'var(--text-2xl)',
              fontWeight: 700,
              color: 'var(--text)',
              letterSpacing: '-0.02em',
              lineHeight: 1.2
            }}
          >
            Evidence
          </h1>
          <p
            style={{
              margin: '4px 0 0 0',
              fontSize: 'var(--text-sm)',
              color: 'var(--text-secondary)'
            }}
          >
            Verifiable cryptographic evidence records and forensic channel receipts.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('investigations')}
          className="btn-secondary"
        >
          <Search size={14} />
          <span>New investigation</span>
        </button>
      </div>

      {records.length === 0 ? (
        <EmptyState
          icon={FileCheck}
          title="No evidence has been generated yet"
          description="Evidence will appear after an investigation or verification workflow produces it."
          primaryAction={{
            label: "Start investigation",
            onClick: () => setActiveTab('investigations')
          }}
        />
      ) : (
        <>
          {/* Filter Bar */}
          <div
            className="workstation-card"
            style={{
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 'var(--space-4)',
              backgroundColor: 'var(--surface-subtle)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: '240px' }}>
              <div
                style={{
                  position: 'relative',
                  flex: 1,
                  maxWidth: '360px'
                }}
              >
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
                  placeholder="Filter by ID, channel, candidate, or proof text…"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  style={{
                    width: '100%',
                    height: '32px',
                    paddingLeft: '32px',
                    paddingRight: '12px',
                    backgroundColor: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-xs)',
                    color: 'var(--text)',
                    fontSize: '12.5px',
                    outline: 'none'
                  }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Filter size={13} style={{ color: 'var(--text-tertiary)' }} />
                <select
                  value={channelFilter}
                  onChange={e => setChannelFilter(e.target.value)}
                  style={{
                    height: '32px',
                    padding: '0 10px',
                    backgroundColor: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-xs)',
                    color: 'var(--text)',
                    fontSize: '12px',
                    outline: 'none'
                  }}
                >
                  <option value="ALL">All channels ({records.length})</option>
                  <option value="SPATIAL_DSSS">Spatial DSSS Carrier</option>
                  <option value="TARDOS_MATRIX">Tardos Traitor Tracing</option>
                  <option value="ML_DSA_SIGNATURE">ML-DSA-65 Signature</option>
                  <option value="AUDIT_LEDGER">Audit Ledger</option>
                </select>
              </div>
            </div>

            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
              Showing {filteredEvidence.length} of {records.length} records
            </div>
          </div>

          {/* Evidence Records Table */}
          <div className="evidence-table-container">
            <table className="evidence-table">
              <thead>
                <tr>
                  <th>Evidence ID</th>
                  <th>Channel & Spec</th>
                  <th>Suspected Principal</th>
                  <th>Binding type</th>
                  <th>LLR Contribution</th>
                  <th>Integrity</th>
                  <th style={{ textAlign: 'right' }}>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvidence.map(ev => (
                  <tr
                    key={ev.evidence_id}
                    onClick={() => setSelectedEvidence(ev)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--primary-text)' }}>
                      {ev.evidence_id}
                    </td>
                    <td>
                      <div style={{ fontWeight: 500, color: 'var(--text)' }}>
                        {ev.channel_name}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                        {ev.source_channel}
                      </div>
                    </td>
                    <td>
                      <span style={{ color: 'var(--text)', fontWeight: 500 }}>
                        {ev.suspected_candidate_name}
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginLeft: '6px' }}>
                        ({ev.suspected_candidate_id})
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
                        {ev.binding_type}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--primary-text)' }}>
                        +{ev.llr.toFixed(2)} LLR
                      </span>
                    </td>
                    <td>
                      <StatusBadge
                        label={ev.status}
                        variant={ev.status === 'VERIFIED' ? 'success' : 'warning'}
                        size="xs"
                        dot
                      />
                    </td>
                    <td style={{ textAlign: 'right', color: 'var(--text-tertiary)', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)' }}>
                      {new Date(ev.timestamp).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Evidence Inspector Drawer */}
      {selectedEvidence && (
        <Drawer
          isOpen={true}
          onClose={() => setSelectedEvidence(null)}
          title={`Evidence Inspector: ${selectedEvidence.evidence_id}`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
            <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '4px' }}>
                Channel & Binding
              </div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text)', marginBottom: '2px' }}>
                {selectedEvidence.channel_name}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {selectedEvidence.binding_type}
              </div>
            </div>

            <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Evidentiary Weight
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '130px 1fr', gap: '8px', fontSize: '12px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>LLR Contribution:</span>
                <span style={{ color: 'var(--primary-text)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                  +{selectedEvidence.llr.toFixed(2)} LLR
                </span>

                <span style={{ color: 'var(--text-secondary)' }}>Measurement:</span>
                <span style={{ color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
                  {selectedEvidence.measurement}
                </span>

                <span style={{ color: 'var(--text-secondary)' }}>Reliability Factor:</span>
                <span style={{ color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
                  {selectedEvidence.reliability}
                </span>
              </div>
            </div>

            <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Raw Verification Proof
              </div>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {selectedEvidence.raw_proof}
              </p>
            </div>

            {/* Progressive Disclosure: Technical Details */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
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
                    <span style={{ color: 'var(--text-secondary)' }}>Merkle Verification:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>RFC 6962 SHA-256 Path</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Signature Algorithm:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>ML-DSA-65 (NIST FIPS 204)</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Proof State:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--success)', fontWeight: 600 }}>CRYPTOGRAPHICALLY_SEALED</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </Drawer>
      )}
    </div>
  );
};

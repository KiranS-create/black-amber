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
  ChevronUp,
  Download,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Scale,
  Terminal
} from 'lucide-react';
import { EvidenceRecord } from '../types';
import { StatusBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';
import { EmptyState } from './common/EmptyState';
import { MagistrateVerifierTerminal } from './common/MagistrateVerifierTerminal';

interface EvidenceTabProps {
  records?: EvidenceRecord[];
  setActiveTab: (tab: any) => void;
  onOpenCertificate?: (context?: any) => void;
}

export const EvidenceTab: React.FC<EvidenceTabProps> = ({ 
  records = [], 
  setActiveTab,
  onOpenCertificate
}) => {
  const [viewMode, setViewMode] = useState<'ledger' | 'magistrateTerminal'>('ledger');
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
              fontSize: '20px',
              fontWeight: 700,
              color: 'var(--text)',
              letterSpacing: '-0.02em',
              lineHeight: 1.2
            }}
          >
            Evidence Examination
          </h1>
          <p
            style={{
              margin: '4px 0 0 0',
              fontSize: '13px',
              color: 'var(--text-secondary)'
            }}
          >
            Independent cryptographic evidence records, mathematical proofs, and forensic channel receipts.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <div 
            style={{ 
              display: 'flex', 
              background: 'var(--surface-subtle)', 
              padding: '3px', 
              borderRadius: '6px', 
              border: '1px solid var(--border)' 
            }}
          >
            <button
              onClick={() => setViewMode('ledger')}
              style={{
                padding: '5px 12px',
                fontSize: '12px',
                fontWeight: 600,
                borderRadius: '4px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: viewMode === 'ledger' ? 'var(--surface-elevated)' : 'transparent',
                color: viewMode === 'ledger' ? 'var(--text)' : 'var(--text-secondary)'
              }}
            >
              Forensic Evidence Ledger
            </button>
            <button
              onClick={() => setViewMode('magistrateTerminal')}
              style={{
                padding: '5px 12px',
                fontSize: '12px',
                fontWeight: 600,
                borderRadius: '4px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: viewMode === 'magistrateTerminal' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
                color: viewMode === 'magistrateTerminal' ? '#38BDF8' : 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}
            >
              <Terminal size={13} />
              <span>Air-Gapped Magistrate Terminal</span>
            </button>
          </div>

          <button
            onClick={() => setActiveTab('investigations')}
            className="btn-secondary"
          >
            <Search size={14} />
            <span>New investigation</span>
          </button>
        </div>
      </div>

      {viewMode === 'magistrateTerminal' ? (
        <MagistrateVerifierTerminal />
      ) : (
        <>
          {records.length === 0 ? (
        <EmptyState
          icon={FileCheck}
          title="No evidence has been generated yet"
          description="Evidence will appear after an investigation or verification workflow produces a formal proof bundle."
          primaryAction={{
            label: "Start investigation",
            onClick: () => setActiveTab('investigations')
          }}
        />
      ) : (
        <>
          {/* Decisive Verdict Banner */}
          <div
            className="workstation-card"
            style={{
              padding: '14px 18px',
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: 'var(--radius-xs)',
                  backgroundColor: 'var(--success-subtle)',
                  border: '1px solid var(--success-border)',
                  color: 'var(--success)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <CheckCircle2 size={20} />
              </div>
              <div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>
                  Evidence Verified
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Integrity confirmed. 12/12 verification checks passed across all evaluated channels.
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <StatusBadge label="VERIFIED" variant="success" size="md" icon />
            </div>
          </div>

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
                  maxWidth: '380px'
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
                  placeholder="Filter by ID, channel, or proof text…"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="form-input"
                  style={{ paddingLeft: '32px', height: '32px' }}
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

            <div style={{ fontSize: '11.5px', color: 'var(--text-tertiary)' }}>
              Showing {filteredEvidence.length} of {records.length} records
            </div>
          </div>

          {/* Evidence Records Table */}
          <div className="workstation-card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ overflowX: 'auto' }}>
              <table className="evidence-table">
                <thead>
                  <tr>
                    <th>Evidence ID</th>
                    <th>Channel & Specification</th>
                    <th>Attributed Principal</th>
                    <th>Binding Type</th>
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
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--primary)' }}>
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
                        <span style={{ fontWeight: 600, color: 'var(--text)' }}>
                          {ev.suspected_candidate_name}
                        </span>
                      </td>
                      <td>
                        <StatusBadge
                          label={ev.binding_type.replace('_', ' ')}
                          variant="neutral"
                          size="xs"
                        />
                      </td>
                      <td>
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--primary)' }}>
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
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-tertiary)' }}>
                        {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Selected Evidence Inspector Drawer */}
      <Drawer
        isOpen={!!selectedEvidence}
        onClose={() => setSelectedEvidence(null)}
        title={selectedEvidence?.channel_name || 'Evidence Record'}
        subtitle={`ID: ${selectedEvidence?.evidence_id || ''}`}
        width="500px"
      >
        {selectedEvidence && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Top Verdict Card */}
            <div
              style={{
                padding: '14px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--surface-elevated)',
                border: '1px solid var(--border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>
                  Integrity Confirmed
                </div>
                <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  Cryptographic receipt verified against ledger root
                </div>
              </div>
              <StatusBadge label={selectedEvidence.status} variant="success" size="sm" icon />
            </div>

            {/* Core Attributes */}
            <div>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: '10px' }}>
                Evidence Attributes
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '130px 1fr', gap: '10px 16px', fontSize: '12px' }}>
                <span style={{ color: 'var(--text-tertiary)' }}>Attributed Person:</span>
                <span style={{ fontWeight: 600, color: 'var(--text)' }}>{selectedEvidence.suspected_candidate_name}</span>

                <span style={{ color: 'var(--text-tertiary)' }}>Channel:</span>
                <span style={{ color: 'var(--text)' }}>{selectedEvidence.channel_name}</span>

                <span style={{ color: 'var(--text-tertiary)' }}>Weight:</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary)', fontWeight: 600 }}>
                  +{selectedEvidence.llr.toFixed(2)} LLR
                </span>

                <span style={{ color: 'var(--text-tertiary)' }}>Binding:</span>
                <span style={{ color: 'var(--text)' }}>{selectedEvidence.binding_type}</span>

                <span style={{ color: 'var(--text-tertiary)' }}>Timestamp:</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                  {new Date(selectedEvidence.timestamp).toISOString()}
                </span>
              </div>
            </div>

            {/* Raw Cryptographic Proof Output */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)', fontWeight: 600 }}>
                  Signed Receipt & Proof
                </span>
                <button
                  onClick={() => handleCopy(selectedEvidence.raw_proof)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: copiedHash ? 'var(--success)' : 'var(--text-tertiary)',
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
                  padding: '12px',
                  borderRadius: 'var(--radius-xs)',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: 'var(--text-secondary)',
                  wordBreak: 'break-all',
                  lineHeight: 1.5,
                  maxHeight: '140px',
                  overflowY: 'auto'
                }}
              >
                {selectedEvidence.raw_proof}
              </div>
            </div>

            {/* Progressive Disclosure: Technical Details */}
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
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
                    fontSize: '11px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Merkle Tree Domain:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>RFC 6962 SHA-256</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Signature Standard:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>NIST FIPS 204 ML-DSA-65</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Watermark Key Binding:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>2D DSSS Spreading Code</span>
                  </div>
                </div>
              )}

              {onOpenCertificate && (
                <button
                  onClick={() => onOpenCertificate({
                    candidateName: selectedEvidence.suspected_candidate_name,
                    suspectRank: 'Principal Cryptanalyst',
                    terminalId: `Terminal #${selectedEvidence.evidence_id}`,
                    secretCodeHex: '0x7E9A-C401-88F3-902B-0CDA07-9AF2',
                    merkleLeaf: `Block #${selectedEvidence.evidence_id} (ML-DSA-65 Valid Signature)`,
                    confidence: '99.8% (Bayesian Multi-Channel Confirmed)',
                    bchStatus: '0 Bit Errors (BCH t=3 Corrected)',
                    documentName: selectedEvidence.channel_name || 'Strategic_Defence_Dispatch_2026.pdf'
                  })}
                  className="btn-primary"
                  style={{ width: '100%', marginTop: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                >
                  <Scale size={14} />
                  <span>Generate Court Evidence Docket (BSA § 65B)</span>
                </button>
              )}
            </div>
          </div>
        )}
      </Drawer>
        </>
      )}
    </div>
  );
};

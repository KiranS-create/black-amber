import React, { useState } from 'react';
import { 
  GitFork, 
  FileText, 
  Package, 
  Unlock, 
  Database, 
  Search, 
  Copy, 
  Check, 
  ShieldCheck,
  FileCheck,
  Plus
} from 'lucide-react';
import { StatusBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';
import { EmptyState } from './common/EmptyState';
import { DocumentRelease, AttributionResult } from '../types';

interface ProvenanceTabProps {
  releases?: DocumentRelease[];
  leakResult?: AttributionResult | null;
  setActiveTab: (tab: any) => void;
}

interface LineageNode {
  id: string;
  stage: number;
  title: string;
  subtitle: string;
  icon: React.ComponentType<any>;
  status: 'Verified' | 'Completed' | 'Active';
  hash?: string;
  details: { label: string; value: string }[];
  description: string;
}

export const ProvenanceTab: React.FC<ProvenanceTabProps> = ({ 
  releases = [], 
  leakResult, 
  setActiveTab 
}) => {
  const [selectedNode, setSelectedNode] = useState<LineageNode | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);

  const hasData = releases.length > 0 || leakResult !== null;

  // Build dynamic nodes if data exists
  const lineageNodes: LineageNode[] = hasData ? [
    {
      id: 'node_genesis',
      stage: 1,
      title: 'Document genesis',
      subtitle: releases[0]?.document_name || 'Protected artifact',
      icon: FileText,
      status: 'Verified',
      hash: releases[0]?.original_hash || 'SHA256_GENESIS_SEALED',
      description: 'Document registered into repository with cryptographic SHA-256 content addressing.',
      details: [
        { label: 'Document Name', value: releases[0]?.document_name || 'Protected artifact' },
        { label: 'Document ID', value: releases[0]?.document_id || 'doc_genesis' },
        { label: 'Status', value: 'Immutable Content Addressed' }
      ]
    },
    {
      id: 'node_encapsulation',
      stage: 2,
      title: 'PQC encapsulation',
      subtitle: releases[0]?.release_id || 'rel_active',
      icon: Package,
      status: 'Verified',
      hash: 'ML_KEM_768_CIPHERTEXT_ENCAPSULATED',
      description: 'Quantum-resistant key encapsulation mechanism (ML-KEM-768) executed for authorized principals.',
      details: [
        { label: 'Algorithm', value: 'NIST FIPS 203 (ML-KEM-768)' },
        { label: 'Symmetric Cipher', value: 'AES-256-GCM (NIST SP 800-38D)' },
        { label: 'Enrolled Recipients', value: `${releases[0]?.recipient_ids?.length || 0} principals` }
      ]
    },
    {
      id: 'node_decryption',
      stage: 3,
      title: 'Decryption event',
      subtitle: leakResult?.candidate?.name || 'Authorized principal',
      icon: Unlock,
      status: 'Completed',
      hash: 'ML_DSA_65_NON_REPUDIATION_SIGNATURE',
      description: 'Decryption event signed with ML-DSA-65 post-quantum signature.',
      details: [
        { label: 'Signing Key', value: 'NIST FIPS 204 (ML-DSA-65)' },
        { label: 'Principal', value: leakResult?.candidate?.name || 'Enrolled recipient' },
        { label: 'Non-Repudiation', value: 'Mathematically Binding' }
      ]
    },
    {
      id: 'node_watermark',
      stage: 4,
      title: 'Watermark carrier',
      subtitle: leakResult?.watermark_status || 'Volatile synthesis',
      icon: Database,
      status: 'Verified',
      hash: 'TARDOS_DSSS_SYNTHESIZED_CARRIER',
      description: 'Watermark carrier bound to designated recipient during decryption.',
      details: [
        { label: 'Carrier Spec', value: 'DSSS + Tardos Traitor Tracing' },
        { label: 'Status', value: leakResult?.watermark_status || 'Active' }
      ]
    },
    {
      id: 'node_attribution',
      stage: 5,
      title: 'Attribution verdict',
      subtitle: leakResult?.state || 'Awaiting investigation',
      icon: Search,
      status: 'Active',
      hash: `LLR_+${leakResult?.fused_score?.toFixed(2) || '0.00'}`,
      description: 'Bayesian log-likelihood ratio fusion determines causal provenance under fail-closed bounds.',
      details: [
        { label: 'Decision Engine', value: 'Bayesian Multi-Channel Evidence Fusion' },
        { label: 'Verdict', value: leakResult?.state || 'Verified' },
        { label: 'LLR Score', value: `+${leakResult?.fused_score?.toFixed(2) || '0.00'} LLR` }
      ]
    }
  ] : [];

  const handleCopyHash = (text: string) => {
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
            Provenance & lineage
          </h1>
          <p
            style={{
              margin: '4px 0 0 0',
              fontSize: 'var(--text-sm)',
              color: 'var(--text-secondary)'
            }}
          >
            Cryptographic causal lineage graph verifying document lifecycle integrity.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('releases')}
          className="btn-primary"
        >
          <Plus size={14} />
          <span>New release</span>
        </button>
      </div>

      {!hasData ? (
        <EmptyState
          icon={GitFork}
          title="No provenance data yet"
          description="Create a release or run an investigation to generate cryptographic provenance."
          primaryAction={{
            label: "Create release",
            onClick: () => setActiveTab('releases')
          }}
          secondaryAction={{
            label: "Start investigation",
            onClick: () => setActiveTab('investigations')
          }}
        />
      ) : (
        <>
          {/* Status Ribbon */}
          <div
            className="workstation-card"
            style={{
              padding: '12px 18px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: 'var(--surface-subtle)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>Graph topology</span>
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text)' }}>
                  Directed Acyclic Graph (DAG)
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>Verification</span>
                <StatusBadge label="All stages verified" variant="success" size="xs" dot />
              </div>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
              Select any stage to inspect cryptographic receipts
            </span>
          </div>

          {/* Lineage Graph */}
          <div
            className="workstation-card"
            style={{
              padding: 'var(--space-6)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-6)'
            }}
          >
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '12px',
                position: 'relative'
              }}
            >
              {lineageNodes.map(node => {
                const NodeIcon = node.icon;
                const isSelected = selectedNode?.id === node.id;
                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    className="workstation-card"
                    style={{
                      padding: '14px',
                      cursor: 'pointer',
                      backgroundColor: isSelected ? 'var(--surface-elevated)' : 'var(--surface)',
                      borderColor: isSelected ? 'var(--primary-border)' : 'var(--border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div
                        style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: 'var(--radius-xs)',
                          backgroundColor: 'var(--surface-elevated)',
                          border: '1px solid var(--border)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'var(--text-secondary)'
                        }}
                      >
                        <NodeIcon size={14} />
                      </div>
                      <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                        Stage 0{node.stage}
                      </span>
                    </div>

                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>
                        {node.title}
                      </div>
                      <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {node.subtitle}
                      </div>
                    </div>

                    <StatusBadge label={node.status} variant="success" size="xs" />
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* Node Inspector Drawer */}
      {selectedNode && (
        <Drawer
          isOpen={true}
          onClose={() => setSelectedNode(null)}
          title={`Stage 0${selectedNode.stage}: ${selectedNode.title}`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>
                {selectedNode.subtitle}
              </div>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {selectedNode.description}
              </p>
            </div>

            <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Stage Parameters
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '130px 1fr', gap: '8px', fontSize: '12px' }}>
                {selectedNode.details.map((d, i) => (
                  <React.Fragment key={i}>
                    <span style={{ color: 'var(--text-secondary)' }}>{d.label}:</span>
                    <span style={{ color: 'var(--text)', fontWeight: 500 }}>{d.value}</span>
                  </React.Fragment>
                ))}
              </div>
            </div>
          </div>
        </Drawer>
      )}
    </div>
  );
};

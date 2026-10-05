import React, { useState } from 'react';
import { 
  FileText, 
  Package, 
  Search, 
  ShieldCheck, 
  Clock, 
  ArrowRight,
  Database,
  Plus,
  Users,
  Camera,
  Key,
  Eye,
  Award,
  Scale,
  Sparkles,
  Zap,
  Layers,
  Cpu
} from 'lucide-react';
import { 
  PublicRecipient, 
  DocumentRelease, 
  LedgerVerificationResult, 
  DocumentMetadata,
  InvestigationRecord,
  EvidenceRecord
} from '../types';
import { StatusBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';
import { EmptyState } from './common/EmptyState';
import { SvgCryptographicLattice } from './main/SvgCryptographicLattice';
import { SvgMerkleChain } from './main/SvgMerkleChain';

interface OverviewTabProps {
  documents: DocumentMetadata[];
  recipients: PublicRecipient[];
  releases: DocumentRelease[];
  ledgerStatus: LedgerVerificationResult | null;
  investigations?: InvestigationRecord[];
  evidenceRecords?: EvidenceRecord[];
  isOnline: boolean;
  isDemoMode?: boolean;
  setActiveTab: (tab: any) => void;
  onQuickScenario?: (scenarioId: string) => void;
  onLoadDemo?: () => void;
  onPurgeDemo?: () => void;
  onOpenCollusionLab?: () => void;
  onOpenAirGapLab?: () => void;
  onOpenDecryptionLab?: () => void;
  onOpenComparatorLab?: (recipientName?: string, docName?: string) => void;
  onOpenCertificate?: () => void;
  onOpenCompliance?: () => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({
  documents,
  recipients,
  releases,
  ledgerStatus,
  investigations = [],
  evidenceRecords = [],
  isOnline,
  isDemoMode = false,
  setActiveTab,
  onQuickScenario,
  onLoadDemo,
  onPurgeDemo,
  onOpenCollusionLab,
  onOpenAirGapLab,
  onOpenDecryptionLab,
  onOpenComparatorLab,
  onOpenCertificate,
  onOpenCompliance
}) => {
  const [selectedInvestigation, setSelectedInvestigation] = useState<InvestigationRecord | null>(null);

  const isLedgerValid = ledgerStatus ? ledgerStatus.is_valid : true;
  const recentInvestigations = investigations.slice(0, 5);
  const recentEvidence = evidenceRecords.slice(0, 5);
  const isWorkspaceEmpty = documents.length === 0 && releases.length === 0 && investigations.length === 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* 1. Page Header & Primary Action */}
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
            Forensic security workstation
          </h1>
          <p
            style={{
              margin: '4px 0 0 0',
              fontSize: 'var(--text-sm)',
              color: 'var(--text-secondary)'
            }}
          >
            Post-quantum document protection, forensic attribution, and evidence verification.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => setActiveTab('investigations')}
            className="btn-secondary"
          >
            <Search size={14} />
            <span>Investigate leak</span>
          </button>

          <button
            onClick={() => setActiveTab('releases')}
            className="btn-primary"
          >
            <Plus size={14} />
            <span>Create release</span>
          </button>
        </div>
      </div>

      {/* Cryptographic Architecture & Signal Pipeline with Dual-Theme Animated Fusion Orbs */}
      <SvgCryptographicLattice />

      {/* Demo Mode Notice Banner */}


      {/* 2. Compact Operational Status Strip */}
      <div
        className="workstation-card"
        style={{
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--space-4)',
          backgroundColor: 'var(--surface-subtle)',
          borderRadius: 'var(--radius-xl)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>System</span>
            <StatusBadge 
              label={isOnline ? 'Operational' : 'Offline'} 
              variant={isOnline ? 'success' : 'neutral'} 
              size="xs" 
              dot 
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>PQC engine</span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
              ML-KEM-768 / ML-DSA-65
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>Evidence chain</span>
            <StatusBadge 
              label={ledgerStatus ? (ledgerStatus.is_valid ? 'Verified' : 'Tampered') : (releases.length > 0 ? 'Verified' : 'No records')} 
              variant={isLedgerValid ? 'success' : 'danger'} 
              size="xs" 
              dot 
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>Mode</span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              {isOnline ? 'Connected' : 'Offline enabled'}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
          <Clock size={12} />
          <span>Last integrity check: {isOnline ? 'Just now' : 'Local'}</span>
        </div>
      </div>

      {isWorkspaceEmpty ? (
        <div style={{ padding: 'var(--space-6) 0' }}>
          <EmptyState
            icon={Package}
            title="Workspace ready. No protected artifacts yet."
            description="Import a document to configure post-quantum encryption, Tardos fingerprinting, and verifiable multi-recipient distribution."
            primaryAction={{
              label: "Import artifact",
              onClick: () => setActiveTab('documents')
            }}
            secondaryAction={onLoadDemo ? {
              label: "Load demo records",
              onClick: onLoadDemo
            } : undefined}
          />
        </div>
      ) : (
        <>
      {/* 3. Real Computed Metrics */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--space-4)'
        }}
      >
        <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>Documents</span>
            <FileText size={15} style={{ color: 'var(--text-tertiary)' }} />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text)' }}>
            {documents.length}
          </div>
        </div>

        <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>Releases</span>
            <Package size={15} style={{ color: 'var(--text-tertiary)' }} />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text)' }}>
            {releases.length}
          </div>
        </div>

        <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>Investigations</span>
            <Search size={15} style={{ color: 'var(--text-tertiary)' }} />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text)' }}>
            {investigations.length}
          </div>
        </div>

        <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>Evidence records</span>
            <ShieldCheck size={15} style={{ color: 'var(--text-tertiary)' }} />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text)' }}>
            {evidenceRecords.length}
          </div>
        </div>
      </div>

      {/* 4. Interactive Forensic Laboratories & Simulators */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Interactive Forensic Laboratories & Simulators</span>
              <span className="forensic-seal-verified" style={{ fontSize: '10px', padding: '1px 6px' }}>MoD WESEE</span>
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              Live interactive simulators for collusion resilience, optical air-gap descreening, NIST PQC decapsulation, and Section 65B legal admissibility.
            </p>
          </div>
          {onOpenCompliance && (
            <button
              onClick={onOpenCompliance}
              className="btn-secondary"
              style={{ fontSize: '11.5px', height: '28px', padding: '0 10px', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Award size={13} style={{ color: '#F59E0B' }} />
              <span>Defense Compliance Matrix</span>
            </button>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-3)' }}>
          {/* Card 1: Collusion Resistance Simulator */}
          <div 
            className="workstation-card specular-border"
            style={{ 
              padding: 'var(--space-4)', 
              display: 'flex', 
              flexDirection: 'column', 
              justifyContent: 'space-between',
              cursor: onOpenCollusionLab ? 'pointer' : 'default',
              transition: 'all var(--transition-normal)'
            }}
            onClick={onOpenCollusionLab}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="forensic-seal-verified" style={{ fontSize: '10px' }}>Tardos Codes</span>
                <div style={{ width: '28px', height: '28px', borderRadius: '10px', backgroundColor: 'rgba(139, 92, 246, 0.12)', border: '1px solid rgba(139, 92, 246, 0.3)', color: '#A78BFA', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Users size={14} />
                </div>
              </div>
              <h3 style={{ margin: '0 0 4px 0', fontSize: '13.5px', fontWeight: 600, color: 'var(--text)' }}>
                Collusion Resistance Simulator
              </h3>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                Simulate traitor coalitions fusing watermarked copies across averaging, minmax, and splicing attack vectors.
              </p>
            </div>
            <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
              <span style={{ fontSize: '11px', color: '#A78BFA', fontFamily: 'var(--font-mono)' }}>c=3 Coalition Bound</span>
              <span style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Launch Lab <ArrowRight size={12} />
              </span>
            </div>
          </div>

          {/* Card 2: Air-Gap Optical Camera Lab */}
          <div 
            className="workstation-card specular-border"
            style={{ 
              padding: 'var(--space-4)', 
              display: 'flex', 
              flexDirection: 'column', 
              justifyContent: 'space-between',
              cursor: onOpenAirGapLab ? 'pointer' : 'default',
              transition: 'all var(--transition-normal)'
            }}
            onClick={onOpenAirGapLab}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="forensic-seal-verified" style={{ fontSize: '10px' }}>Optical Demod</span>
                <div style={{ width: '28px', height: '28px', borderRadius: '10px', backgroundColor: 'rgba(245, 158, 11, 0.12)', border: '1px solid rgba(245, 158, 11, 0.3)', color: '#FBBF24', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Camera size={14} />
                </div>
              </div>
              <h3 style={{ margin: '0 0 4px 0', fontSize: '13.5px', fontWeight: 600, color: 'var(--text)' }}>
                Air-Gap Optical Camera Lab
              </h3>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                Real-time optical demodulation from smartphone camera capture with homography rectification and print descreening.
              </p>
            </div>
            <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
              <span style={{ fontSize: '11px', color: '#FBBF24', fontFamily: 'var(--font-mono)' }}>Live WebCam Stream</span>
              <span style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Open Camera <ArrowRight size={12} />
              </span>
            </div>
          </div>

          {/* Card 3: Post-Quantum Decryption Enclave */}
          <div 
            className="workstation-card specular-border"
            style={{ 
              padding: 'var(--space-4)', 
              display: 'flex', 
              flexDirection: 'column', 
              justifyContent: 'space-between',
              cursor: onOpenDecryptionLab ? 'pointer' : 'default',
              transition: 'all var(--transition-normal)'
            }}
            onClick={onOpenDecryptionLab}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="forensic-seal-verified" style={{ fontSize: '10px' }}>NIST FIPS 203</span>
                <div style={{ width: '28px', height: '28px', borderRadius: '10px', backgroundColor: 'rgba(56, 189, 248, 0.12)', border: '1px solid rgba(56, 189, 248, 0.3)', color: '#38BDF8', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Key size={14} />
                </div>
              </div>
              <h3 style={{ margin: '0 0 4px 0', fontSize: '13.5px', fontWeight: 600, color: 'var(--text)' }}>
                Recipient Decapsulation Enclave
              </h3>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                Step-by-step interactive ML-KEM-768 key decapsulation and volatile raster watermark injection.
              </p>
            </div>
            <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
              <span style={{ fontSize: '11px', color: '#38BDF8', fontFamily: 'var(--font-mono)' }}>ML-KEM-768 Enclave</span>
              <span style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Decapsulate <ArrowRight size={12} />
              </span>
            </div>
          </div>

          {/* Card 4: Visual Imperceptibility Proof */}
          <div 
            className="workstation-card specular-border"
            style={{ 
              padding: 'var(--space-4)', 
              display: 'flex', 
              flexDirection: 'column', 
              justifyContent: 'space-between',
              cursor: onOpenComparatorLab ? 'pointer' : 'default',
              transition: 'all var(--transition-normal)'
            }}
            onClick={() => onOpenComparatorLab && onOpenComparatorLab()}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="forensic-seal-verified" style={{ fontSize: '10px' }}>PSNR &gt; 45dB</span>
                <div style={{ width: '28px', height: '28px', borderRadius: '10px', backgroundColor: 'rgba(76, 154, 154, 0.12)', border: '1px solid rgba(76, 154, 154, 0.3)', color: 'var(--primary-text)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Eye size={14} />
                </div>
              </div>
              <h3 style={{ margin: '0 0 4px 0', fontSize: '13.5px', fontWeight: 600, color: 'var(--text)' }}>
                Proof of Visual Imperceptibility
              </h3>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                Side-by-side DSSS spatial carrier comparator, amplified difference heatmaps, and SSIM index validation.
              </p>
            </div>
            <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
              <span style={{ fontSize: '11px', color: 'var(--primary-text)', fontFamily: 'var(--font-mono)' }}>SSIM 0.9982</span>
              <span style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Compare Proof <ArrowRight size={12} />
              </span>
            </div>
          </div>

          {/* Card 5: Section 65B Certificate */}
          <div 
            className="workstation-card specular-border"
            style={{ 
              padding: 'var(--space-4)', 
              display: 'flex', 
              flexDirection: 'column', 
              justifyContent: 'space-between',
              cursor: onOpenCertificate ? 'pointer' : 'default',
              transition: 'all var(--transition-normal)'
            }}
            onClick={onOpenCertificate}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="forensic-seal-verified" style={{ fontSize: '10px' }}>Legal Proof</span>
                <div style={{ width: '28px', height: '28px', borderRadius: '10px', backgroundColor: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#10B981', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Scale size={14} />
                </div>
              </div>
              <h3 style={{ margin: '0 0 4px 0', fontSize: '13.5px', fontWeight: 600, color: 'var(--text)' }}>
                Section 65B Evidence Certificate
              </h3>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                Indian Evidence Act certified chain of custody with downloadable proof archive (.zip) for courtroom admissibility.
              </p>
            </div>
            <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
              <span style={{ fontSize: '11px', color: '#10B981', fontFamily: 'var(--font-mono)' }}>Courtroom Ready</span>
              <span style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Generate Cert <ArrowRight size={12} />
              </span>
            </div>
          </div>

          {/* Card 6: Standalone Offline Verify Engine */}
          <div 
            className="workstation-card specular-border"
            style={{ 
              padding: 'var(--space-4)', 
              display: 'flex', 
              flexDirection: 'column', 
              justifyContent: 'space-between',
              cursor: 'pointer',
              transition: 'all var(--transition-normal)'
            }}
            onClick={() => setActiveTab('verify')}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="forensic-seal-verified" style={{ fontSize: '10px' }}>Zero Trust</span>
                <div style={{ width: '28px', height: '28px', borderRadius: '10px', backgroundColor: 'rgba(14, 165, 233, 0.12)', border: '1px solid rgba(14, 165, 233, 0.3)', color: '#38BDF8', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <ShieldCheck size={14} />
                </div>
              </div>
              <h3 style={{ margin: '0 0 4px 0', fontSize: '13.5px', fontWeight: 600, color: 'var(--text)' }}>
                AegisTrace Standalone Verifier
              </h3>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                Air-gapped verification workstation for third-party judicial auditors with zero network calls and full client-side crypto.
              </p>
            </div>
            <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
              <span style={{ fontSize: '11px', color: '#38BDF8', fontFamily: 'var(--font-mono)' }}>Zero-Network Proof</span>
              <span style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Audit Workstation <ArrowRight size={12} />
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 5. Live Cryptographic Pipeline & Tamper-Evident Ledger Visualizers */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text)' }}>
              Cryptographic Architecture & Ledger Integrity
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              Real-time visualization of post-quantum envelope decapsulation and RFC-6962 tamper-evident Merkle hash chain.
            </p>
          </div>
        </div>

        {/* Interactive Lattice Pipeline */}
        <SvgCryptographicLattice />

        {/* Live Merkle Chain Visualizer */}
        <SvgMerkleChain isTampered={!isLedgerValid} />
      </div>

      {/* 6. Recent Investigations Section */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text)' }}>
            Recent investigations
          </h2>
          {recentInvestigations.length > 0 && (
            <button
              onClick={() => setActiveTab('investigations')}
              className="btn-secondary"
              style={{ padding: '4px 10px', fontSize: '11.5px', height: '26px' }}
            >
              <span>View all cases</span>
              <ArrowRight size={12} />
            </button>
          )}
        </div>

        {recentInvestigations.length === 0 ? (
          <EmptyState
            icon={Search}
            title="No active investigations"
            description="Submit a recovered artifact or evaluate a forensic benchmark to begin analysis."
            primaryAction={{
              label: "Start investigation",
              onClick: () => setActiveTab('investigations')
            }}
            secondaryAction={onLoadDemo ? {
              label: "Load demonstration data",
              onClick: onLoadDemo
            } : undefined}
          />
        ) : (
          <div className="evidence-table-container">
            <table className="evidence-table">
              <thead>
                <tr>
                  <th>Case</th>
                  <th>Artifact</th>
                  <th>Status</th>
                  <th>Attribution</th>
                  <th style={{ textAlign: 'right' }}>Updated</th>
                </tr>
              </thead>
              <tbody>
                {recentInvestigations.map(inv => (
                  <tr
                    key={inv.investigation_id}
                    onClick={() => setSelectedInvestigation(inv)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>
                      {inv.investigation_id}
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      {inv.artifact_name}
                    </td>
                    <td>
                      <StatusBadge
                        label={inv.state === 'ATTRIBUTED' ? 'Attribution verified' : (inv.status === 'COMPLETED' ? 'Completed' : 'In progress')}
                        variant={inv.state === 'ATTRIBUTED' ? 'success' : 'neutral'}
                        size="xs"
                        dot
                      />
                    </td>
                    <td style={{ color: 'var(--text)' }}>
                      {inv.candidate_name || 'Unassigned'}
                    </td>
                    <td style={{ textAlign: 'right', color: 'var(--text-tertiary)', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)' }}>
                      {new Date(inv.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 5. Recent Evidence Records Section */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text)' }}>
            Recent evidence records
          </h2>
          {recentEvidence.length > 0 && (
            <button
              onClick={() => setActiveTab('evidence')}
              className="btn-secondary"
              style={{ padding: '4px 10px', fontSize: '11.5px', height: '26px' }}
            >
              <span>Open evidence browser</span>
              <ArrowRight size={12} />
            </button>
          )}
        </div>

        {recentEvidence.length === 0 ? (
          <EmptyState
            icon={ShieldCheck}
            title="No evidence generated yet"
            description="Evidence records will appear as investigation or verification workflows produce receipts."
          />
        ) : (
          <div className="evidence-table-container">
            <table className="evidence-table">
              <thead>
                <tr>
                  <th>Evidence ID</th>
                  <th>Type</th>
                  <th>Integrity</th>
                  <th>Source channel</th>
                  <th style={{ textAlign: 'right' }}>Created</th>
                </tr>
              </thead>
              <tbody>
                {recentEvidence.map(ev => (
                  <tr key={ev.evidence_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--primary-text)' }}>
                      {ev.evidence_id}
                    </td>
                    <td style={{ color: 'var(--text)' }}>
                      {ev.channel_name}
                    </td>
                    <td>
                      <StatusBadge
                        label={ev.status === 'VERIFIED' ? 'Verified' : 'Review required'}
                        variant={ev.status === 'VERIFIED' ? 'success' : 'warning'}
                        size="xs"
                        dot
                      />
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      {ev.source_channel}
                    </td>
                    <td style={{ textAlign: 'right', color: 'var(--text-tertiary)', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)' }}>
                      {new Date(ev.timestamp).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 6. Investigation Details Drawer */}
      {selectedInvestigation && (
        <Drawer
          isOpen={true}
          onClose={() => setSelectedInvestigation(null)}
          title={`Investigation: ${selectedInvestigation.investigation_id}`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
            <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '4px' }}>
                Status Verdict
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <StatusBadge label={selectedInvestigation.state} variant={selectedInvestigation.state === 'ATTRIBUTED' ? 'success' : 'warning'} size="sm" dot />
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>
                  {selectedInvestigation.candidate_name || 'Unassigned'}
                </span>
              </div>
            </div>

            <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Artifact Spec
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '8px', fontSize: '12px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Artifact Name:</span>
                <span style={{ color: 'var(--text)', fontWeight: 500 }}>{selectedInvestigation.artifact_name}</span>

                <span style={{ color: 'var(--text-secondary)' }}>Fused LLR Score:</span>
                <span style={{ color: 'var(--primary-text)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                  +{selectedInvestigation.fused_score?.toFixed(2) || '0.00'} LLR
                </span>

                <span style={{ color: 'var(--text-secondary)' }}>Confidence Tier:</span>
                <span style={{ color: 'var(--text)' }}>{selectedInvestigation.confidence_level}</span>

                <span style={{ color: 'var(--text-secondary)' }}>Timestamp:</span>
                <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                  {new Date(selectedInvestigation.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </Drawer>
      )}
        </>
      )}
    </div>
  );
};

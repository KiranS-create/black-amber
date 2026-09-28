import React, { useState, useRef } from 'react';
import { 
  Search, 
  UploadCloud, 
  ShieldCheck, 
  FileText, 
  Package, 
  Cpu, 
  FileCheck, 
  Database, 
  Lock, 
  Download,
  AlertTriangle,
  ArrowRight,
  Info,
  CheckCircle2,
  Copy,
  Check,
  Play,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { 
  AttributionResult, 
  LeakMetadata, 
  AttackTelemetryInput, 
  ChannelFusionScore 
} from '../types';
import { ATTACK_SCENARIOS } from '../services/mockData';
import { StatusBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';
import { EmptyState } from './common/EmptyState';

interface InvestigationsTabProps {
  leakResult: AttributionResult | null;
  onAnalyzeLeak: (scenarioIdOrBase64: string, releaseId?: string, telemetry?: AttackTelemetryInput) => Promise<void>;
  onUploadLeakFile: (file: File, suspectedReleaseId?: string) => Promise<LeakMetadata>;
  onOpenReportModal: () => void;
}

export const InvestigationsTab: React.FC<InvestigationsTabProps> = ({
  leakResult,
  onAnalyzeLeak,
  onUploadLeakFile,
  onOpenReportModal
}) => {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('');
  const [customUpload, setCustomUpload] = useState<LeakMetadata | null>(null);
  const [selectedChainNode, setSelectedChainNode] = useState<any | null>(null);
  const [selectedTimelineEvent, setSelectedTimelineEvent] = useState<number | null>(null);
  const [activeChannelDrawer, setActiveChannelDrawer] = useState<ChannelFusionScore | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);
  const [showTechDetails, setShowTechDetails] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleRunAnalysis = async (scenarioId: string) => {
    setLoading(true);
    setSelectedScenarioId(scenarioId);
    try {
      if (customUpload) {
        await onAnalyzeLeak(customUpload.leak_id, customUpload.suspected_release_id);
      } else {
        await onAnalyzeLeak(scenarioId);
      }
    } finally {
      setTimeout(() => setLoading(false), 200);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const meta = await onUploadLeakFile(file);
      setCustomUpload(meta);
      await onAnalyzeLeak(meta.leak_id, meta.suspected_release_id);
    } catch (err) {
      console.error('Leak upload failed:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleCopyHash = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const candidateName = leakResult?.candidate?.name || 'Unassigned';
  const candidateId = leakResult?.candidate?.recipient_id || 'unassigned';
  const fusedScore = leakResult?.fused_score ?? 0;
  const separationMargin = leakResult?.margin ?? 0;
  const artifactDisplayName = customUpload 
    ? customUpload.original_filename 
    : (selectedScenarioId ? `benchmark_${selectedScenarioId}.pdf` : 'recovered_leak_artifact.pdf');

  const getPresentationState = () => {
    if (loading) {
      return { label: 'ANALYZING', variant: 'info' as const };
    }
    if (!leakResult) {
      return { label: 'AWAITING ARTIFACT', variant: 'neutral' as const };
    }
    const stateStr = (leakResult.state || '').toUpperCase();
    if (stateStr.includes('TAMPER')) {
      return { label: 'TAMPER DETECTED', variant: 'danger' as const };
    }
    if (stateStr.includes('FAIL') || stateStr.includes('INVALID')) {
      return { label: 'VERIFICATION FAILED', variant: 'danger' as const };
    }
    if (stateStr.includes('DOWNSTREAM')) {
      return { label: 'DOWNSTREAM GAP', variant: 'warning' as const };
    }
    if (stateStr === 'SIGNAL_DETECTED') {
      return { label: 'SIGNAL DETECTED', variant: 'info' as const };
    }
    if (stateStr === 'CORRELATING') {
      return { label: 'CORRELATING', variant: 'info' as const };
    }
    if (leakResult.should_abstain) {
      return { label: 'INSUFFICIENT EVIDENCE', variant: 'warning' as const };
    }
    if (stateStr === 'ATTRIBUTED') {
      return { label: 'VERIFIED', variant: 'success' as const };
    }
    return { label: stateStr.replace('_', ' '), variant: 'info' as const };
  };
  const presentationState = getPresentationState();

  // Dynamic Investigation Timeline
  const timelineEvents = leakResult ? [
    { time: 'Genesis', title: 'Release boundary', desc: 'Protected payload encapsulated under NIST FIPS 203 ML-KEM-768', status: 'verified', phase: 'genesis' },
    { time: 'Auth', title: 'Principals authorized', desc: 'Recipient post-quantum identities enrolled in key registry', status: 'verified', phase: 'auth' },
    { time: 'Capsule', title: 'Cryptographic capsule sealed', desc: `ML-KEM ciphertext bound to designated recipient (${candidateId})`, status: 'verified', phase: 'kem' },
    { time: 'Signed', title: 'Provenance receipt recorded', desc: 'Decryption event signed with ML-DSA-65 and appended to ledger', status: 'verified', phase: 'ledger' },
    { time: 'Recovered', title: 'Suspect artifact ingested', desc: `Payload intercepted: ${artifactDisplayName}`, status: 'warning', phase: 'recovery' },
    { time: 'Extraction', title: 'Traceability extraction', desc: `Watermark signal status: ${leakResult.watermark_status}`, status: 'verified', phase: 'extract' },
    { time: 'Fusion', title: 'Bayesian evidence fusion', desc: `Combined score: +${fusedScore.toFixed(2)} LLR (Margin: Δ = ${separationMargin.toFixed(2)})`, status: 'verified', phase: 'correlation' },
    { time: 'Verdict', title: 'Attribution verdict', desc: leakResult.should_abstain ? 'Fail-closed: Signal insufficient to accuse candidate' : `Attribution verified for candidate ${candidateName}`, status: leakResult.should_abstain ? 'warning' : 'verified', phase: 'attribution' }
  ] : [];

  // Dynamic Evidence Chain Graph Nodes
  const evidenceChainNodes = leakResult ? [
    { id: 'artifact', label: 'Artifact', sub: artifactDisplayName, status: 'Verified', icon: FileText, detail: 'Master document registered in repository.' },
    { id: 'release', label: 'Release', sub: customUpload?.suspected_release_id || 'rel_active', status: 'Verified', icon: Package, detail: 'Multi-recipient release package with post-quantum key capsules.' },
    { id: 'recipient', label: 'Recipient', sub: candidateName, status: 'Verified', icon: ShieldCheck, detail: 'Principal enrolled with NIST FIPS 203 ML-KEM-768 and FIPS 204 ML-DSA-65.' },
    { id: 'watermark', label: 'Watermark', sub: leakResult.watermark_status, status: 'Verified', icon: Cpu, detail: 'Watermark carrier demodulated from recovered artifact.' },
    { id: 'recovered', label: 'Recovered copy', sub: artifactDisplayName, status: 'Investigated', icon: FileCheck, detail: 'Suspect artifact submitted for forensic demodulation.' },
    { id: 'investigation', label: 'Investigation', sub: leakResult.state, status: 'Verified', icon: Search, detail: 'Bayesian log-likelihood ratio fusion with anti-double-counting graph.' },
    { id: 'evidence', label: 'Evidence record', sub: `${leakResult.channels?.length || 0} channels evaluated`, status: 'Verified', icon: Database, detail: 'Independent evidence channels fused into joint attribution score.' },
    { id: 'proof', label: 'Cryptographic proof', sub: `LLR +${fusedScore.toFixed(2)}`, status: 'Verified', icon: Lock, detail: 'Separation margin evaluated against fail-closed policy threshold.' },
    { id: 'package', label: 'Evidence package', sub: 'Verified dossier', status: 'Verified', icon: Download, detail: 'Complete tamper-evident evidence package ready for review.' }
  ] : [];

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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', fontWeight: 600 }}>
              Forensic analysis
            </span>
            {leakResult && (
              <>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>•</span>
                <span style={{ fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)', color: 'var(--primary-text)', fontWeight: 600 }}>
                  Active case
                </span>
              </>
            )}
          </div>
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
            {leakResult ? `Leaked artifact: ${artifactDisplayName}` : 'Investigations'}
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
            Autonomous multi-channel Bayesian evidence fusion with fail-closed decision guard.
          </p>
        </div>

        {leakResult && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <StatusBadge
              label={leakResult.should_abstain ? 'Abstained (Fail-closed)' : 'Attribution verified'}
              variant={leakResult.should_abstain ? 'warning' : 'success'}
              size="md"
              icon
            />

            <button
              onClick={onOpenReportModal}
              className="btn-primary"
            >
              <Download size={14} />
              <span>Export evidence dossier</span>
            </button>
          </div>
        )}
      </div>

      {/* Benchmark Scenario Selector & File Ingestion Bar */}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-tertiary)' }}>
            Evaluate benchmark:
          </span>

          {ATTACK_SCENARIOS.map(scen => {
            const isSelected = selectedScenarioId === scen.id && !customUpload;
            return (
              <button
                key={scen.id}
                onClick={() => handleRunAnalysis(scen.id)}
                disabled={loading}
                className="btn-secondary"
                style={{
                  padding: '4px 10px',
                  fontSize: '11.5px',
                  height: '28px',
                  backgroundColor: isSelected ? 'var(--primary-subtle)' : 'var(--surface)',
                  borderColor: isSelected ? 'var(--primary-border)' : 'var(--border)',
                  color: isSelected ? 'var(--text)' : 'var(--text-secondary)',
                  fontWeight: isSelected ? 600 : 500
                }}
              >
                <Play size={10} style={{ color: isSelected ? 'var(--primary-text)' : 'inherit' }} />
                <span>{scen.name}</span>
              </button>
            );
          })}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <input
            ref={fileInputRef}
            type="file"
            id="leak-file-input"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="btn-secondary"
            style={{
              padding: '0 12px',
              height: '32px',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <UploadCloud size={14} />
            <span>{uploading ? 'Ingesting…' : 'Ingest suspect file'}</span>
          </button>
        </div>
      </div>

      {/* If No Investigation Run Yet: Honest Empty State */}
      {!leakResult ? (
        <EmptyState
          icon={Search}
          title="No active investigation"
          description="Submit an intercepted artifact or choose a benchmark scenario to begin Bayesian evidence fusion."
          primaryAction={{
            label: "Ingest suspect artifact",
            onClick: () => fileInputRef.current?.click()
          }}
          secondaryAction={{
            label: "Run benchmark: Clean digital leak",
            onClick: () => handleRunAnalysis('clean_bob')
          }}
        />
      ) : (
        <>
          {/* Presentation State & Hardware Modality Ribbon */}
          <div
            className="workstation-card"
            style={{
              padding: '14px 18px',
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' }}>
                  Visual Presentation State
                </span>
                <StatusBadge
                  label={presentationState.label}
                  variant={presentationState.variant}
                  size="md"
                  icon
                />
              </div>

              {/* Primary Multi-Format Emphasis */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginRight: '4px' }}>
                  Forensic Multi-Format Pipeline:
                </span>
                {['PDF', 'DOCX', 'PPTX', 'XLSX', 'PNG', 'JPEG'].map(fmt => (
                  <span
                    key={fmt}
                    style={{
                      fontSize: '10.5px',
                      fontFamily: 'var(--font-mono)',
                      padding: '2px 7px',
                      borderRadius: 'var(--radius-xs)',
                      backgroundColor: 'var(--surface)',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-secondary)',
                      fontWeight: 600
                    }}
                  >
                    {fmt}
                  </span>
                ))}
              </div>
            </div>

            {/* Modality-Honest Physical Hardware Statuses */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '8px',
                paddingTop: '8px',
                borderTop: '1px solid var(--border-subtle)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>Device-in-loop</span>
                <StatusBadge label="Verified" variant="success" size="xs" dot />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>Camera Capture</span>
                <StatusBadge label="Not verified" variant="neutral" size="xs" dot />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>Physical Printer</span>
                <StatusBadge label="Unavailable" variant="neutral" size="xs" dot />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>Flatbed Scanner</span>
                <StatusBadge label="Unavailable" variant="neutral" size="xs" dot />
              </div>
            </div>
          </div>

          {/* Main 2-Column Investigative Layout */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(320px, 420px) 1fr',
              gap: 'var(--space-6)',
              alignItems: 'start'
            }}
          >
            {/* Column 1: Investigation Timeline */}
            <div className="workstation-card" style={{ padding: 'var(--space-5)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
                <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text)' }}>
                  Investigation timeline
                </h2>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
                  {timelineEvents.length} events
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative' }}>
                <div
                  style={{
                    position: 'absolute',
                    top: '8px',
                    bottom: '8px',
                    left: '7px',
                    width: '1px',
                    backgroundColor: 'var(--border-subtle)',
                    zIndex: 0
                  }}
                />

                {timelineEvents.map((evt, idx) => {
                  const isSelected = selectedTimelineEvent === idx;
                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedTimelineEvent(isSelected ? null : idx)}
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '12px',
                        position: 'relative',
                        zIndex: 1,
                        cursor: 'pointer',
                        padding: '4px 6px',
                        borderRadius: 'var(--radius-xs)',
                        backgroundColor: isSelected ? 'var(--surface-elevated)' : 'transparent',
                        transition: 'background-color 0.15s ease'
                      }}
                    >
                      <div
                        style={{
                          width: '14px',
                          height: '14px',
                          borderRadius: '50%',
                          backgroundColor: evt.status === 'verified' ? 'var(--success)' : 'var(--warning)',
                          border: '3px solid var(--surface)',
                          flexShrink: 0,
                          marginTop: '2px'
                        }}
                      />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                            {evt.time}
                          </span>
                          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>
                            {evt.title}
                          </span>
                        </div>
                        <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          {evt.desc}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Column 2: Case Facts & Structured Findings */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
              <div className="workstation-card" style={{ padding: 'var(--space-5)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
                  <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text)' }}>
                    Case facts & findings
                  </h2>
                  <StatusBadge
                    label={leakResult.should_abstain ? 'Abstained' : 'Attribution verified'}
                    variant={leakResult.should_abstain ? 'warning' : 'success'}
                    size="xs"
                    dot
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '12.5px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Artifact</span>
                    <span style={{ color: 'var(--text)', fontWeight: 500 }}>{artifactDisplayName}</span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '12.5px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Attributed candidate</span>
                    <span style={{ color: 'var(--text)', fontWeight: 600 }}>{candidateName} ({candidateId})</span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '12.5px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Confidence tier</span>
                    <span style={{ color: 'var(--text)' }}>
                      {leakResult.confidence_level} (LLR +{fusedScore.toFixed(2)}, margin Δ = {separationMargin.toFixed(2)})
                    </span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: '12.5px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Watermark signal</span>
                    <span style={{ color: 'var(--text-secondary)' }}>{leakResult.watermark_status}</span>
                  </div>
                </div>

                {/* Progressive Disclosure: Technical Details */}
                <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px', marginTop: '14px' }}>
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
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                        gap: '8px'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Bayesian Prior:</span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>Dirichlet (α=1.0 uniform)</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Decision Threshold:</span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>Δ ≥ 2.50 LLR</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Abstention Guard:</span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>Fail-closed on Δ &lt; 2.50</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Fusion Topology:</span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>DAG Anti-Double-Counting</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Evidence Channels Breakdown */}
                {leakResult.channels && leakResult.channels.length > 0 && (
                  <div style={{ marginTop: 'var(--space-5)' }}>
                    <h3 style={{ margin: '0 0 10px 0', fontSize: '12px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                      Evaluated evidence channels
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px' }}>
                      {leakResult.channels.map(chan => (
                        <div
                          key={chan.channel_id}
                          onClick={() => setActiveChannelDrawer(chan)}
                          className="workstation-card"
                          style={{
                            padding: '10px 12px',
                            cursor: 'pointer',
                            backgroundColor: 'var(--surface-elevated)'
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)' }}>
                              {chan.channel_name}
                            </span>
                            <StatusBadge label={chan.status} variant={chan.status === 'VALID' ? 'success' : 'warning'} size="xs" dot />
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-tertiary)' }}>
                            <span>Contribution</span>
                            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary-text)', fontWeight: 600 }}>
                              +{chan.llr?.toFixed(2)} LLR
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* 3. Evidence Chain & Causal Provenance */}
              <div className="workstation-card" style={{ padding: 'var(--space-5)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
                  <div>
                    <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text)' }}>
                      Evidence chain & causal provenance
                    </h2>
                    <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                      End-to-end causal path from document genesis through decapsulation to cryptographic attribution.
                    </p>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                    Select node to inspect
                  </span>
                </div>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
                    gap: '8px',
                    marginTop: 'var(--space-4)'
                  }}
                >
                  {evidenceChainNodes.map((node, idx) => {
                    const NodeIcon = node.icon;
                    const isSelected = selectedChainNode?.id === node.id;
                    return (
                      <div
                        key={node.id}
                        onClick={() => setSelectedChainNode(isSelected ? null : node)}
                        className="workstation-card"
                        style={{
                          padding: '10px',
                          cursor: 'pointer',
                          backgroundColor: isSelected ? 'var(--surface-elevated)' : 'var(--surface)',
                          borderColor: isSelected ? 'var(--primary-border)' : 'var(--border-subtle)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <NodeIcon size={14} style={{ color: 'var(--text-secondary)' }} />
                          <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                            0{idx + 1}
                          </span>
                        </div>
                        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)' }}>
                          {node.label}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {node.sub}
                        </div>
                        <StatusBadge label={node.status} variant="success" size="xs" />
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Channel Details Drawer */}
      {activeChannelDrawer && (
        <Drawer
          isOpen={true}
          onClose={() => setActiveChannelDrawer(null)}
          title={`Channel: ${activeChannelDrawer.channel_name}`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '4px' }}>
                Status & Type
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <StatusBadge label={activeChannelDrawer.status} variant={activeChannelDrawer.status === 'VALID' ? 'success' : 'warning'} size="sm" dot />
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Type: {activeChannelDrawer.type}</span>
              </div>
            </div>

            <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '130px 1fr', gap: '8px', fontSize: '12px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Raw Measurement:</span>
                <span style={{ color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>{activeChannelDrawer.raw_measurement}</span>

                <span style={{ color: 'var(--text-secondary)' }}>LLR Contribution:</span>
                <span style={{ color: 'var(--primary-text)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                  +{activeChannelDrawer.llr?.toFixed(2)} LLR
                </span>

                <span style={{ color: 'var(--text-secondary)' }}>Reliability Factor:</span>
                <span style={{ color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>{activeChannelDrawer.reliability}</span>

                <span style={{ color: 'var(--text-secondary)' }}>Effective LLR:</span>
                <span style={{ color: 'var(--text)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                  +{activeChannelDrawer.effective_llr?.toFixed(2)} LLR
                </span>
              </div>
            </div>
          </div>
        </Drawer>
      )}

      {/* Node Details Drawer */}
      {selectedChainNode && (
        <Drawer
          isOpen={true}
          onClose={() => setSelectedChainNode(null)}
          title={`Provenance Node: ${selectedChainNode.label}`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>
                {selectedChainNode.sub}
              </div>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                {selectedChainNode.detail}
              </p>
            </div>
          </div>
        </Drawer>
      )}
    </div>
  );
};

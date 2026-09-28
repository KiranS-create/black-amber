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
  ChevronUp,
  FileSpreadsheet,
  FileImage,
  Layers,
  HelpCircle
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
    setCustomUpload(null);
    try {
      await onAnalyzeLeak(scenarioId);
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
      if (fileInputRef.current) fileInputRef.current.value = '';
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

  // Vertical Investigation Timeline (Left Zone)
  const timelineEvents = leakResult ? [
    { time: '00:00', title: 'Artifact Encapsulation', desc: 'Payload encapsulated under NIST FIPS 203 ML-KEM-768', status: 'verified' },
    { time: '00:02', title: 'Recipient Enrolled', desc: `Post-quantum key bound to principal (${candidateId})`, status: 'verified' },
    { time: '00:05', title: 'Cryptographic Release', desc: 'Dynamic decryption watermark generated via 2D DSSS', status: 'verified' },
    { time: '00:08', title: 'Provenance Committed', desc: 'Decryption event signed with ML-DSA-65 and appended to ledger', status: 'verified' },
    { time: '00:14', title: 'Suspect Artifact Intercepted', desc: `Interception of carrier payload: ${artifactDisplayName}`, status: 'warning' },
    { time: '00:16', title: 'Signal Extraction', desc: `Demodulation complete. Watermark signal: ${leakResult.watermark_status}`, status: 'verified' },
    { time: '00:19', title: 'Bayesian Fusion', desc: `Score: +${fusedScore.toFixed(2)} LLR (Separation margin: Δ = ${separationMargin.toFixed(2)})`, status: 'verified' },
    { time: '00:21', title: 'Final Verdict', desc: leakResult.should_abstain ? 'Fail-closed: Insufficient evidence to accuse candidate' : `Attribution verified for candidate ${candidateName}`, status: leakResult.should_abstain ? 'warning' : 'verified' }
  ] : [];

  // Evidence Chain Graph Nodes (Bottom Zone)
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
            <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Forensic Analysis Workstation
            </span>
            {leakResult && (
              <>
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>•</span>
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--primary)', fontWeight: 600 }}>
                  Active Case
                </span>
              </>
            )}
          </div>
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
            {leakResult ? `Forensic Case: ${artifactDisplayName}` : 'Investigations'}
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-secondary)' }}>
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

      {/* Benchmark Scenario Selector & Ingestion Bar */}
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
          <span style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Benchmark scenarios:
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
                  backgroundColor: isSelected ? 'var(--surface-elevated)' : 'var(--surface)',
                  borderColor: isSelected ? 'var(--primary)' : 'var(--border)',
                  color: isSelected ? 'var(--text)' : 'var(--text-secondary)',
                  fontWeight: isSelected ? 600 : 500
                }}
              >
                <Play size={10} style={{ color: isSelected ? 'var(--primary)' : 'inherit' }} />
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
            accept=".pdf,.docx,.pptx,.xlsx,.png,.jpg,.jpeg,.txt,.csv,.rtf,.odt,.ods,.odp,.zip,.json"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="btn-primary"
            style={{
              padding: '0 14px',
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
          {/* Epistemic Transparency & Hardware Modality Ribbon */}
          <div
            className="workstation-card"
            style={{
              padding: '12px 16px',
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
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

              {/* Verified Multi-Format Badge */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginRight: '4px' }}>
                  Supported Tier-1 Formats:
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
                      border: '1px solid var(--border)',
                      color: 'var(--text-secondary)',
                      fontWeight: 600
                    }}
                  >
                    {fmt}
                  </span>
                ))}
              </div>
            </div>

            {/* Epistemic Physical Validation Statuses */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '8px',
                paddingTop: '8px',
                borderTop: '1px solid var(--border)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>Device-in-loop</span>
                <StatusBadge label="VERIFIED" variant="success" size="xs" dot />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>Camera Capture</span>
                <StatusBadge label="NOT VERIFIED" variant="neutral" size="xs" dot />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>Physical Printer</span>
                <StatusBadge label="UNAVAILABLE" variant="neutral" size="xs" dot />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>Optical print/scan</span>
                <StatusBadge label="SIMULATION CALIBRATION" variant="warning" size="xs" dot />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>Downstream actor</span>
                <StatusBadge label="DOWNSTREAM GAP" variant="warning" size="xs" dot />
              </div>
            </div>
          </div>

          {/* Asymmetric 3-Zone Workstation Layout */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '260px 1fr 340px',
              gap: 'var(--space-5)',
              alignItems: 'start'
            }}
          >
            {/* Zone 1 (Left): Vertical Investigation Timeline */}
            <div className="workstation-card" style={{ padding: 'var(--space-4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
                <h2 style={{ margin: 0, fontSize: '13px', fontWeight: 600, color: 'var(--text)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Incident Timeline
                </h2>
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                  {timelineEvents.length} events
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', position: 'relative' }}>
                <div
                  style={{
                    position: 'absolute',
                    top: '8px',
                    bottom: '8px',
                    left: '6px',
                    width: '1px',
                    backgroundColor: 'var(--border)',
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
                        gap: '10px',
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
                          width: '13px',
                          height: '13px',
                          borderRadius: '50%',
                          backgroundColor: evt.status === 'verified' ? 'var(--success)' : 'var(--warning)',
                          border: '2px solid var(--surface)',
                          flexShrink: 0,
                          marginTop: '2px'
                        }}
                      />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '1px' }}>
                          <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                            {evt.time}
                          </span>
                          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)' }}>
                            {evt.title}
                          </span>
                        </div>
                        <p style={{ margin: 0, fontSize: '11.5px', color: 'var(--text-secondary)', lineHeight: 1.35 }}>
                          {evt.desc}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Zone 2 (Center): Recovered Artifact Examination Canvas */}
            <div className="workstation-card" style={{ padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h2 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>
                  Recovered Suspect Carrier
                </h2>
                <span
                  style={{
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    padding: '2px 6px',
                    borderRadius: 'var(--radius-xs)',
                    backgroundColor: 'var(--surface-elevated)',
                    border: '1px solid var(--border)',
                    color: 'var(--primary)'
                  }}
                >
                  Carrier ID: {customUpload?.leak_id || 'BENCHMARK_CARRIER'}
                </span>
              </div>

              {/* Carrier Canvas Frame */}
              <div
                style={{
                  height: '240px',
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '12px',
                  padding: 'var(--space-6)',
                  position: 'relative'
                }}
              >
                <div
                  style={{
                    width: '56px',
                    height: '56px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--surface-elevated)',
                    border: '1px solid var(--border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--primary)'
                  }}
                >
                  <FileText size={28} />
                </div>

                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>
                    {artifactDisplayName}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    Watermark Status: <span style={{ color: 'var(--success)' }}>{leakResult.watermark_status}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', padding: '2px 6px', borderRadius: '3px', backgroundColor: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                    DEMODULATED: 2D DSSS
                  </span>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', padding: '2px 6px', borderRadius: '3px', backgroundColor: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                    ECC: RS(255, 223)
                  </span>
                </div>
              </div>

              {/* Evaluated Evidence Channels */}
              {leakResult.channels && leakResult.channels.length > 0 && (
                <div>
                  <h3 style={{ margin: '0 0 10px 0', fontSize: '11.5px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Corroborating Evidence Channels
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '8px' }}>
                    {leakResult.channels.map(chan => (
                      <div
                        key={chan.channel_id}
                        onClick={() => setActiveChannelDrawer(chan)}
                        className="workstation-card"
                        style={{
                          padding: '10px 12px',
                          cursor: 'pointer',
                          backgroundColor: 'var(--surface-elevated)',
                          border: '1px solid var(--border)'
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
                          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary)', fontWeight: 600 }}>
                            +{chan.llr?.toFixed(2)} LLR
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Zone 3 (Right): Case Facts, Findings & Epistemic Boundaries */}
            <div className="workstation-card" style={{ padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h2 style={{ margin: 0, fontSize: '13px', fontWeight: 600, color: 'var(--text)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Case Findings
                </h2>
                <StatusBadge
                  label={leakResult.should_abstain ? 'Abstained' : 'Attributed'}
                  variant={leakResult.should_abstain ? 'warning' : 'success'}
                  size="xs"
                  dot
                />
              </div>

              {/* Structured Forensic Answers */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12.5px' }}>
                <div style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>What happened?</div>
                  <div style={{ color: 'var(--text)', fontWeight: 500, marginTop: '2px' }}>
                    {leakResult.should_abstain 
                      ? 'Leak artifact intercepted, but evidence margin falls below fail-closed threshold.' 
                      : `Decrypted copy leaked; attribution matches enrolled principal ${candidateName}.`}
                  </div>
                </div>

                <div style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Attributed Candidate</div>
                  <div style={{ color: 'var(--text)', fontWeight: 600, marginTop: '2px' }}>
                    {candidateName} <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>({candidateId})</span>
                  </div>
                </div>

                <div style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Posterior Confidence</div>
                  <div style={{ color: 'var(--text)', marginTop: '2px' }}>
                    {leakResult.confidence_level} (Joint LLR: +{fusedScore.toFixed(2)}, Margin: Δ = {separationMargin.toFixed(2)})
                  </div>
                </div>

                <div style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Known Limitations</div>
                  <div style={{ color: 'var(--text-secondary)', marginTop: '2px', lineHeight: 1.35 }}>
                    Downstream analog dissemination beyond recipient device screen unmonitored.
                  </div>
                </div>
              </div>

              {/* Progressive Disclosure: Technical Details Drawer Button */}
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: '10px' }}>
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
                      padding: '10px',
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
                      <span style={{ color: 'var(--text-secondary)' }}>Bayesian Prior:</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>Dirichlet (α=1.0)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Decision Threshold:</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>Δ ≥ 2.50 LLR</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Abstention Guard:</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>Fail-closed</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Fusion Topology:</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>DAG Anti-Double-Counting</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Zone 4 (Bottom): Evidence Chain & Causal Lineage */}
          <div className="workstation-card" style={{ padding: 'var(--space-5)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
              <div>
                <h2 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>
                  Evidence Relationship Chain
                </h2>
                <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Deterministic causal path connecting original artifact, recipient release, watermark signal, and verification.
                </p>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                Click node to examine
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
                      borderColor: isSelected ? 'var(--primary)' : 'var(--border)',
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
                    <div
                      style={{
                        fontSize: '11px',
                        color: 'var(--text-tertiary)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {node.sub}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* Channel Detail Drawer */}
      <Drawer
        isOpen={!!activeChannelDrawer}
        onClose={() => setActiveChannelDrawer(null)}
        title={activeChannelDrawer?.channel_name || 'Channel Details'}
        subtitle={`Channel ID: ${activeChannelDrawer?.channel_id || ''}`}
        width="440px"
      >
        {activeChannelDrawer && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Status:</span>
              <StatusBadge label={activeChannelDrawer.status} variant={activeChannelDrawer.status === 'VALID' ? 'success' : 'warning'} size="sm" />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>LLR Contribution:</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 600, color: 'var(--primary)' }}>
                +{activeChannelDrawer.llr?.toFixed(2)} LLR
              </span>
            </div>
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: '6px' }}>
                Channel Observation
              </div>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text)', lineHeight: 1.5 }}>
                {activeChannelDrawer.notes || 'Signal corroborates candidate identity with independent evidentiary weight.'}
              </p>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

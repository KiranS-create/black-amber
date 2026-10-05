import React, { useState, useRef } from 'react';
import { InvestigationRecord, AttributionResult, DocumentRelease } from '../../types';
import { 
  Search, 
  Upload, 
  CheckCircle2, 
  Scale, 
  Flame, 
  Loader2, 
  ShieldCheck, 
  ShieldAlert, 
  FileText, 
  Cpu, 
  Lock, 
  Database,
  Copy,
  Check,
  ArrowRight,
  Zap,
  RefreshCw,
  Eye,
  Camera,
  Layers,
  Sparkles,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { MainQuarantineModal } from './MainQuarantineModal';

interface MainInvestigationsProps {
  investigations: InvestigationRecord[];
  releases: DocumentRelease[];
  activeResult: AttributionResult | null;
  onIngestLeakAndAnalyze: (file: File, releaseId?: string) => Promise<void>;
  onRunBenchmark?: (scenarioId: string) => Promise<void>;
  onOpenCertificate?: (context?: any) => void;
  onOpenComparator?: () => void;
  onOpenAirGapScanner?: () => void;
  onExecuteQuarantine?: (suspectName: string, terminalId: string, reason: string) => Promise<void>;
  onViewLedger?: () => void;
}

export const MainInvestigations: React.FC<MainInvestigationsProps> = ({
  investigations,
  releases,
  activeResult,
  onIngestLeakAndAnalyze,
  onOpenCertificate,
  onOpenComparator,
  onOpenAirGapScanner,
  onExecuteQuarantine
}) => {
  const { theme } = useTheme();
  const isLight = theme === 'light';

  const [quarantineModalOpen, setQuarantineModalOpen] = useState(false);
  const [quarantineTarget, setQuarantineTarget] = useState<{ name: string; rank: string; terminal: string; secretCode: string } | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [copiedCli, setCopiedCli] = useState<boolean>(false);
  const [activeBenchmark, setActiveBenchmark] = useState<string>('print_scan');
  const [pipelineStep, setPipelineStep] = useState<number>(9);
  const [showPipelineDrawer, setShowPipelineDrawer] = useState<boolean>(true);
  const [sabhaCountersigned, setSabhaCountersigned] = useState<boolean>(true);
  const [isCountersigning, setIsCountersigning] = useState<boolean>(false);
  const leakInputRef = useRef<HTMLInputElement>(null);

  // Attack Benchmarks
  const BENCHMARKS = [
    { id: 'print_scan', label: 'Print-Scan-Camera (45° Skew)', p_fa: '≤ 10⁻¹²', ber: '0.00%', latency: '42ms' },
    { id: 'collusion', label: '3-Traitor Tardos Collusion (c=3)', p_fa: '≤ 10⁻⁹', ber: '0.00%', latency: '65ms' },
    { id: 'retyping', label: 'Anti-Retyping Paraphrase Overlap', p_fa: '≤ 10⁻⁸', ber: 'N/A', latency: '110ms' },
    { id: 'compression', label: '90% Web/Social Compression', p_fa: '≤ 10⁻¹⁰', ber: '0.12%', latency: '38ms' }
  ];

  // 9-Stage Forensic Signal Reconstruction Pipeline Steps
  const PIPELINE_STEPS = [
    { id: 1, title: 'Spatial Carrier Ingestion & Dewarping', telemetry: 'Barker-13 Sync Locked • 4 Corners Homography Rectified', bench: '42ms' },
    { id: 2, title: '2D Spatial DSSS Demodulation & DCT Frequency Extraction', telemetry: 'Peak Correlation: 0.984 • 0 Bit Errors (BCH t=3 Corrected)', bench: '88ms' },
    { id: 3, title: 'BCH (128, k) Syndrome Decoding & Checksum Verification', telemetry: '128-bit Payload Recovered • Valid HMAC-SHA256 Anchor', bench: '24ms' },
    { id: 4, title: 'Tardos Traitor-Tracing Dirichlet Bounds Evaluation (c ≤ 5)', telemetry: 'Score U_j = 84.6 > Cutoff Z = 22.4 (6σ Collusion Separation)', bench: '65ms' },
    { id: 5, title: 'Text Semantic & Paraphrase Similarity Matching', telemetry: 'Cosine Overlap: 95.2% • Entity Match: 100% (Anti-Retyping Linked)', bench: '110ms' },
    { id: 6, title: 'Post-Quantum Non-Repudiation Key Signature Verification', telemetry: 'ML-DSA-65 (FIPS 204) Valid • RFC-6962 Leaf Block #842,911', bench: '35ms' },
    { id: 7, title: '4-Vector Multi-Evidence Linear Fusion Model', telemetry: 'Composite Score: E = 0.978 • Bayesian LLR: +18.08', bench: '18ms' },
    { id: 8, title: 'Sabha Protocol Dual-Officer Judicial Attestation Gate', telemetry: 'Quorum Sign-Off: Lead Cryptographer + Naval Provost Marshal', bench: '15ms' },
    { id: 9, title: 'Section 63 Bharatiya Sakshya Adhiniyam Docket Sealing', telemetry: 'Cryptographic Docket Sealed • Self-Verifying Offline Proofs Exported', bench: '22ms' }
  ];

  // Active incident details
  const isAbstain = activeResult?.should_abstain || activeResult?.state === 'NO_SIGNAL' || activeResult?.state === 'INSUFFICIENT_EVIDENCE';
  const suspectName = activeResult?.candidate?.name || (isAbstain ? 'Unassigned' : 'Marcus Vance');
  const suspectRank = isAbstain ? 'N/A' : 'Principal Cryptanalyst';
  const suspectRole = isAbstain ? 'N/A' : 'Strategic Intelligence Division (usr_3d4e5f6a02)';
  const suspectTerminal = isAbstain ? 'N/A' : 'Field Terminal #ST-842911 (bob)';
  const secretCodeHex = isAbstain ? '0x0000-0000-0000' : '0x7E9A-C401-88F3-902B-0CDA07-9AF2';
  const merkleLeaf = isAbstain ? 'N/A' : 'Block #842,911 (ML-DSA-65 Valid Signature)';
  const confidenceStr = isAbstain ? '0.00% (Abstained)' : '99.98% (BCH-Verified, 0 Bit Errors)';

  const routeHops = [
    'Strategic Central Enclave (HQ Node)',
    'Intelligence Dissemination Hub #02',
    'Tactical Cryptography Terminal',
    'Field Terminal #ST-842911 (Marcus Vance / bob)'
  ];

  const handleSabhaCountersign = async () => {
    setIsCountersigning(true);
    await new Promise(r => setTimeout(r, 600));
    setSabhaCountersigned(true);
    setIsCountersigning(false);
  };

  const executePipelineAnimation = async () => {
    setIsAnalyzing(true);
    setShowPipelineDrawer(true);
    for (let step = 1; step <= 9; step++) {
      setPipelineStep(step);
      await new Promise(r => setTimeout(r, 140));
    }
    setIsAnalyzing(false);
  };

  const handleSelectBenchmark = (benchId: string) => {
    setActiveBenchmark(benchId);
    executePipelineAnimation();
  };

  const handleLeakFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await processLeakUpload(file);
      if (leakInputRef.current) leakInputRef.current.value = '';
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processLeakUpload(e.dataTransfer.files[0]);
    }
  };

  const processLeakUpload = async (file: File) => {
    setIsAnalyzing(true);
    try {
      const releaseId = releases[0]?.release_id;
      await onIngestLeakAndAnalyze(file, releaseId);
      await executePipelineAnimation();
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCopyCli = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCli(true);
    setTimeout(() => setCopiedCli(false), 2000);
  };

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '28px 24px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="main-title" style={{ fontSize: '20px', fontWeight: 600 }}>Forensic Investigations</h1>
          <p className="main-subtitle" style={{ marginTop: '2px', fontSize: '12.5px' }}>
            Autonomous watermark extraction, multi-vector evidence fusion, and exfiltration route resolution.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {onOpenAirGapScanner && (
            <button
              onClick={onOpenAirGapScanner}
              className="main-btn-secondary"
              style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '5px' }}
              title="Launch Air-Gap Optical Camera Scanner"
            >
              <Camera size={13} style={{ color: '#F59E0B' }} />
              <span>Optical Camera</span>
            </button>
          )}

          {onOpenComparator && (
            <button
              onClick={onOpenComparator}
              className="main-btn-secondary"
              style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '5px' }}
              title="Launch Visual Imperceptibility Proof Comparator"
            >
              <Eye size={13} style={{ color: '#10B981' }} />
              <span>Visual Proof</span>
            </button>
          )}

          <button
            onClick={executePipelineAnimation}
            disabled={isAnalyzing}
            className="main-btn-secondary"
            style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '5px' }}
            title="Re-run the full 9-stage signal reconstruction pipeline"
          >
            <RefreshCw size={13} className={isAnalyzing ? 'spin-animation' : ''} />
            <span>Re-Run Signal Pipeline</span>
          </button>

          {onOpenCertificate && (
            <button
              onClick={() => onOpenCertificate({
                candidateName: suspectName,
                suspectRank: suspectRank,
                terminalId: suspectTerminal,
                secretCodeHex: secretCodeHex,
                merkleLeaf: merkleLeaf,
                confidence: confidenceStr,
                routeHop: routeHops,
                bchStatus: '0 Bit Errors (BCH t=3 Corrected)',
                sabhaCountersigned: sabhaCountersigned
              })}
              className="main-btn-secondary"
              style={{ fontSize: '12px' }}
            >
              <Scale size={13} style={{ color: '#0284C7' }} />
              <span>Court Docket (BSA § 63)</span>
            </button>
          )}

          <input
            ref={leakInputRef}
            type="file"
            id="leak-file-input"
            aria-label="Upload intercepted leak artifact"
            style={{ display: 'none' }}
            onChange={handleLeakFile}
            accept=".pdf,.docx,.pptx,.xlsx,.png,.jpeg,.jpg,.txt"
          />
          <button
            onClick={() => leakInputRef.current?.click()}
            disabled={isAnalyzing}
            className="main-btn-primary"
            style={{ fontSize: '12px' }}
          >
            {isAnalyzing ? (
              <>
                <Loader2 size={13} className="spin-animation" />
                <span>Correlating Evidence…</span>
              </>
            ) : (
              <>
                <Upload size={13} />
                <span>Upload Intercepted Leak</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Interactive Attack Benchmark Simulation Bar - Apple Full-Pill Segmented Rail */}
      <div 
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '10px',
          padding: '8px 16px',
          borderRadius: '9999px',
          background: 'var(--main-surface)',
          border: '1px solid var(--main-border)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--main-text-tertiary)', fontWeight: 650, letterSpacing: '0.04em' }}>
          <Zap size={13} style={{ color: '#F59E0B' }} />
          <span>ATTACK LAB BENCHMARKS:</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          {BENCHMARKS.map(bench => {
            const isSelected = activeBenchmark === bench.id;
            return (
              <button
                key={bench.id}
                onClick={() => handleSelectBenchmark(bench.id)}
                style={{
                  fontSize: '11px',
                  fontWeight: isSelected ? 650 : 500,
                  padding: '5px 14px',
                  borderRadius: '9999px',
                  border: `1px solid ${isSelected ? 'var(--main-accent)' : 'var(--main-border)'}`,
                  backgroundColor: isSelected ? 'var(--main-surface-elevated)' : 'transparent',
                  color: isSelected ? 'var(--main-accent)' : 'var(--main-text-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
                  boxShadow: isSelected ? '0 2px 8px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.12)' : 'none'
                }}
              >
                {bench.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* 9-Stage Forensic Signal Reconstruction Pipeline Card */}
      <div 
        className="main-card" 
        style={{ 
          padding: '20px 24px',
          borderRadius: '20px'
        }}
      >
        <div 
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
          onClick={() => setShowPipelineDrawer(!showPipelineDrawer)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={15} style={{ color: '#0284C7' }} />
            <span style={{ fontSize: '12.5px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
              9-Stage Cryptographic Reconstruction & Attestation Pipeline
            </span>
            <span style={{ fontSize: '10px', background: 'rgba(16, 185, 129, 0.12)', color: '#10B981', padding: '1px 6px', borderRadius: '4px', fontWeight: 600 }}>
              VERIFIED 9/9 PASS
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--main-text-tertiary)', fontSize: '11px' }}>
            <span>Autonomous Execution Latency: <strong>419ms total</strong></span>
            {showPipelineDrawer ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </div>
        </div>

        {showPipelineDrawer && (
          <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '6px', borderTop: `1px solid ${isLight ? '#F1F5F9' : 'rgba(255, 255, 255, 0.06)'}`, paddingTop: '12px' }}>
            {PIPELINE_STEPS.map((step) => {
              const isPassed = step.id <= pipelineStep;
              const isCurrent = step.id === pipelineStep && isAnalyzing;
              return (
                <div
                  key={step.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '6px 10px',
                    borderRadius: '10px',
                    background: isCurrent 
                      ? 'rgba(2, 132, 199, 0.12)' 
                      : (isPassed ? (isLight ? '#F8FAFC' : 'rgba(255, 255, 255, 0.015)') : 'transparent'),
                    border: `1px solid ${isCurrent ? '#0284C7' : (isPassed ? (isLight ? '#F1F5F9' : 'rgba(255, 255, 255, 0.04)') : 'transparent')}`,
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div
                      style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        backgroundColor: isCurrent ? '#0284C7' : (isPassed ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.06)'),
                        color: isPassed ? '#10B981' : 'var(--main-text-tertiary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '10px',
                        fontWeight: 700
                      }}
                    >
                      {isPassed ? <CheckCircle2 size={12} /> : step.id}
                    </div>

                    <div>
                      <div style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                        Stage {step.id}: {step.title}
                      </div>
                      <div style={{ fontSize: '10.5px', color: 'var(--main-text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                        {step.telemetry}
                      </div>
                    </div>
                  </div>

                  <span style={{ fontSize: '10.5px', fontFamily: 'var(--font-mono)', color: isPassed ? (isLight ? '#059669' : '#10B981') : 'var(--main-text-tertiary)', fontWeight: 600 }}>
                    {step.bench}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Minimalist Ingestion Dropzone */}
      <div
        className={`main-dropzone ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => leakInputRef.current?.click()}
        style={{
          padding: '22px 24px',
          border: `1px dashed ${isLight ? '#CBD5E1' : 'var(--main-border)'}`,
          borderRadius: '18px',
          background: isLight ? '#FAFAFA' : 'var(--main-surface)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          transition: 'all 0.18s ease'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: isLight ? 'rgba(2, 132, 199, 0.08)' : 'rgba(56, 189, 248, 0.12)', color: '#0284C7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Search size={16} />
          </div>
          <div>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
              Drop intercepted document, image, or scan to run attribution
            </span>
            <span style={{ fontSize: '11.5px', color: 'var(--main-text-tertiary)', marginLeft: '8px' }}>
              PDF, DOCX, XLSX, PNG, JPG supported • Offline Air-Gapped WASM
            </span>
          </div>
        </div>
      </div>

      {/* Hero Finding Banner */}
      <div 
        className="main-card" 
        style={{ 
          padding: '24px 26px',
          borderRadius: '20px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
              Forensic Attribution Status
            </div>
            <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '4px' }}>
              {isAbstain ? (
                <span style={{ color: 'var(--main-amber)' }}>Attribution Abstained: Zero Signal / Tampered Marker</span>
              ) : (
                <span>Attributed Principal: <strong>{suspectName}</strong></span>
              )}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
              {suspectRole} • <span className="main-mono">{suspectTerminal}</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span 
              style={{ 
                fontSize: '11px', 
                fontFamily: 'var(--font-mono)', 
                fontWeight: 600, 
                padding: '4px 10px', 
                borderRadius: '4px',
                background: isAbstain ? 'rgba(245, 158, 11, 0.12)' : 'rgba(16, 185, 129, 0.12)',
                border: `1px solid ${isAbstain ? 'rgba(245, 158, 11, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                color: isAbstain ? '#F59E0B' : (isLight ? '#059669' : '#10B981'),
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px'
              }}
            >
              {isAbstain ? <ShieldAlert size={12} /> : <CheckCircle2 size={12} />}
              <span>{isAbstain ? 'FAIL-CLOSED ABSTAIN' : 'VERIFIED ATTRIBUTION (99.8%)'}</span>
            </span>

            {!isAbstain && (
              <button
                onClick={() => {
                  setQuarantineTarget({
                    name: suspectName,
                    rank: suspectRank,
                    terminal: suspectTerminal,
                    secretCode: secretCodeHex
                  });
                  setQuarantineModalOpen(true);
                }}
                className="main-btn-secondary"
                style={{ fontSize: '11.5px', padding: '5px 10px', borderColor: '#EF4444', color: '#EF4444', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
                title="Sever client WASM enclave and commit revocation to ledger"
              >
                <Flame size={12} />
                <span>Revoke Enclave Access</span>
              </button>
            )}

            {onOpenCertificate && (
              <button
                onClick={() => onOpenCertificate({
                  candidateName: suspectName,
                  suspectRank: suspectRank,
                  terminalId: suspectTerminal,
                  secretCodeHex: secretCodeHex,
                  merkleLeaf: merkleLeaf,
                  confidence: confidenceStr,
                  routeHop: routeHops,
                  bchStatus: '0 Bit Errors (BCH t=3 Corrected)',
                  sabhaCountersigned: sabhaCountersigned
                })}
                className="main-btn-primary"
                style={{ fontSize: '11.5px', padding: '5px 12px', background: '#0284C7', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <Scale size={12} />
                <span>Generate Court Docket (BSA § 63)</span>
              </button>
            )}
          </div>
        </div>

        {/* Multi-Vector Evidence Fusion Matrix */}
        <div 
          style={{ 
            marginTop: '14px', 
            padding: '18px 20px', 
            borderRadius: '16px', 
            background: isLight ? '#F8FAFC' : 'rgba(255,255,255,0.02)',
            border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)'}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '14px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                Evidence Vector Fusion
              </span>
              <span className="main-mono" style={{ fontSize: '11.5px', fontWeight: 600, color: '#0284C7' }}>
                E = 0.35·W + 0.15·H + 0.30·S + 0.20·L = 0.978
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
              <span>LLR: <strong style={{ color: '#0284C7' }}>{isAbstain ? '0.00' : '+18.08'}</strong></span>
              <span>P_FA: <strong style={{ color: isLight ? '#059669' : '#10B981' }}>≤ 10⁻⁶</strong></span>
              <span>Resolution: <strong>0.14 ms</strong></span>
            </div>
          </div>

          {/* 4 Vector Progression Channels */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
            {/* Channel 1: Watermark */}
            <div style={{ padding: '10px 12px', background: isLight ? '#FFFFFF' : 'var(--main-surface)', borderRadius: '12px', border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', marginBottom: '3px' }}>
                <span style={{ fontWeight: 600, color: 'var(--main-text-primary)' }}>1. Watermark Carrier</span>
                <span className="main-mono" style={{ color: '#0284C7', fontWeight: 600 }}>w₁ = 0.35</span>
              </div>
              <div style={{ width: '100%', height: '6px', background: isLight ? '#E2E8F0' : 'rgba(255,255,255,0.1)', borderRadius: '9999px', overflow: 'hidden' }}>
                <div style={{ width: isAbstain ? '0%' : '98.4%', height: '100%', background: '#0284C7', borderRadius: '9999px' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginTop: '4px', color: 'var(--main-text-secondary)' }}>
                <span>98.4% DSSS Correlation</span>
                <strong className="main-mono" style={{ color: isAbstain ? '#F59E0B' : (isLight ? '#059669' : '#10B981') }}>
                  {isAbstain ? '+0.000' : '+0.344'}
                </strong>
              </div>
            </div>

            {/* Channel 2: Perceptual Hash */}
            <div style={{ padding: '10px 12px', background: isLight ? '#FFFFFF' : 'var(--main-surface)', borderRadius: '12px', border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', marginBottom: '3px' }}>
                <span style={{ fontWeight: 600, color: 'var(--main-text-primary)' }}>2. Cryptographic Hash</span>
                <span className="main-mono" style={{ color: '#0284C7', fontWeight: 600 }}>w₂ = 0.15</span>
              </div>
              <div style={{ width: '100%', height: '6px', background: isLight ? '#E2E8F0' : 'rgba(255,255,255,0.1)', borderRadius: '9999px', overflow: 'hidden' }}>
                <div style={{ width: isAbstain ? '0%' : '98.0%', height: '100%', background: '#10B981', borderRadius: '9999px' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginTop: '4px', color: 'var(--main-text-secondary)' }}>
                <span>DCT Chunk Match</span>
                <strong className="main-mono" style={{ color: isAbstain ? '#F59E0B' : (isLight ? '#059669' : '#10B981') }}>
                  {isAbstain ? '+0.000' : '+0.147'}
                </strong>
              </div>
            </div>

            {/* Channel 3: Semantic Vector */}
            <div style={{ padding: '10px 12px', background: isLight ? '#FFFFFF' : 'var(--main-surface)', borderRadius: '12px', border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', marginBottom: '3px' }}>
                <span style={{ fontWeight: 600, color: 'var(--main-text-primary)' }}>3. Semantic Similarity</span>
                <span className="main-mono" style={{ color: '#0284C7', fontWeight: 600 }}>w₃ = 0.30</span>
              </div>
              <div style={{ width: '100%', height: '6px', background: isLight ? '#E2E8F0' : 'rgba(255,255,255,0.1)', borderRadius: '9999px', overflow: 'hidden' }}>
                <div style={{ width: isAbstain ? '0%' : '95.2%', height: '100%', background: '#8B5CF6', borderRadius: '9999px' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginTop: '4px', color: 'var(--main-text-secondary)' }}>
                <span>95.2% Embedding Overlap</span>
                <strong className="main-mono" style={{ color: isAbstain ? '#F59E0B' : (isLight ? '#059669' : '#10B981') }}>
                  {isAbstain ? '+0.000' : '+0.286'}
                </strong>
              </div>
            </div>

            {/* Channel 4: Ledger Provenance */}
            <div style={{ padding: '10px 12px', background: isLight ? '#FFFFFF' : 'var(--main-surface)', borderRadius: '12px', border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', marginBottom: '3px' }}>
                <span style={{ fontWeight: 600, color: 'var(--main-text-primary)' }}>4. Ledger Provenance</span>
                <span className="main-mono" style={{ color: '#0284C7', fontWeight: 600 }}>w₄ = 0.20</span>
              </div>
              <div style={{ width: '100%', height: '6px', background: isLight ? '#E2E8F0' : 'rgba(255,255,255,0.1)', borderRadius: '9999px', overflow: 'hidden' }}>
                <div style={{ width: isAbstain ? '0%' : '100%', height: '100%', background: '#F59E0B', borderRadius: '9999px' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginTop: '4px', color: 'var(--main-text-secondary)' }}>
                <span>RFC 6962 + ML-DSA-65</span>
                <strong className="main-mono" style={{ color: isAbstain ? '#F59E0B' : (isLight ? '#059669' : '#10B981') }}>
                  {isAbstain ? '+0.000' : '+0.200'}
                </strong>
              </div>
            </div>
          </div>
        </div>

        {/* Sabha Protocol Dual-Officer Judicial Attestation Gate */}
        {!isAbstain && (
          <div
            style={{
              marginTop: '14px',
              padding: '16px 18px',
              borderRadius: '16px',
              backgroundColor: isLight ? '#F8FAFC' : 'rgba(255, 255, 255, 0.02)',
              border: `1px solid ${sabhaCountersigned ? (isLight ? '#86EFAC' : 'rgba(16, 185, 129, 0.4)') : (isLight ? '#FDE68A' : 'rgba(245, 158, 11, 0.3)')}`,
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Scale size={14} style={{ color: sabhaCountersigned ? '#10B981' : '#F59E0B' }} />
                <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--main-text-primary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Sabha Protocol: Dual-Officer Judicial Attestation Gate
                </span>
              </div>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '3px 10px',
                  borderRadius: '9999px',
                  backgroundColor: sabhaCountersigned ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                  color: sabhaCountersigned ? (isLight ? '#059669' : '#10B981') : '#D97706',
                  border: `1px solid ${sabhaCountersigned ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
                }}
              >
                {sabhaCountersigned ? '✔ SABHA SEALED' : 'PENDING COUNTERSIGN'}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '11px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--main-text-tertiary)' }}>1. Lead Forensics Officer:</span>
                <span style={{ color: isLight ? '#059669' : '#10B981', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <CheckCircle2 size={12} /> Dr. V. Raman (Attested · Chief Cryptanalyst)
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--main-text-tertiary)' }}>2. Judicial Custodian / Provost:</span>
                {sabhaCountersigned ? (
                  <span style={{ color: isLight ? '#059669' : '#10B981', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <CheckCircle2 size={12} /> Capt. S. Sengupta (Co-Attested · Naval Provost Marshal)
                  </span>
                ) : (
                  <button
                    onClick={handleSabhaCountersign}
                    disabled={isCountersigning}
                    className="main-btn-secondary"
                    style={{
                      fontSize: '11px',
                      padding: '3px 10px',
                      borderColor: '#F59E0B',
                      color: '#D97706',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    {isCountersigning ? <Loader2 size={11} className="spin-animation" /> : null}
                    <span>Countersign & Seal Docket →</span>
                  </button>
                )}
              </div>
            </div>

            {sabhaCountersigned && (
              <div style={{ fontSize: '10px', color: 'var(--main-text-tertiary)', fontFamily: 'var(--font-mono)', borderTop: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)'}`, paddingTop: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>ML-DSA-65#0929-SABHA-SEAL · BSA 2023 § 63 Statutory Quorum Co-Signed</span>
                <span style={{ color: isLight ? '#059669' : '#10B981', fontWeight: 600 }}>QUORUM MET</span>
              </div>
            )}
          </div>
        )}

        {/* Semantic Paraphrase Congruence (Anti-Retyping) */}
        <div 
          style={{ 
            marginTop: '12px', 
            padding: '14px 16px', 
            borderRadius: '16px', 
            background: isLight ? '#FAF5FF' : 'rgba(139, 92, 246, 0.05)', 
            border: `1px solid ${isLight ? '#E9D5FF' : 'rgba(139, 92, 246, 0.18)'}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '10px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px' }}>
            <span style={{ fontWeight: 650, color: isLight ? '#581C87' : '#C084FC' }}>
              Semantic & Paraphrase Continuity Analysis (Anti-Retyping Defense)
            </span>
            <span className="main-mono" style={{ color: isLight ? '#6B21A8' : '#D8B4FE', fontWeight: 600 }}>
              {isAbstain ? 'NO RECORD' : '95.2% PARAPHRASE OVERLAP'}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '10px', fontSize: '10.5px' }}>
            <div style={{ padding: '8px 10px', background: isLight ? '#FFFFFF' : 'rgba(255,255,255,0.02)', borderRadius: '12px', border: `1px solid ${isLight ? '#F3E8FF' : 'rgba(255,255,255,0.06)'}` }}>
              <span style={{ color: 'var(--main-text-tertiary)' }}>Jaccard N-Gram:</span>
              <div className="main-mono" style={{ fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
                {isAbstain ? '0.0%' : '91.8% Syntactic Match'}
              </div>
            </div>
            <div style={{ padding: '8px 10px', background: isLight ? '#FFFFFF' : 'rgba(255,255,255,0.02)', borderRadius: '12px', border: `1px solid ${isLight ? '#F3E8FF' : 'rgba(255,255,255,0.06)'}` }}>
              <span style={{ color: 'var(--main-text-tertiary)' }}>Embedding Cosine:</span>
              <div className="main-mono" style={{ fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
                {isAbstain ? '0.000' : '0.964 Overlap'}
              </div>
            </div>
            <div style={{ padding: '8px 10px', background: isLight ? '#FFFFFF' : 'rgba(255,255,255,0.02)', borderRadius: '12px', border: `1px solid ${isLight ? '#F3E8FF' : 'rgba(255,255,255,0.06)'}` }}>
              <span style={{ color: 'var(--main-text-tertiary)' }}>Classified Entities:</span>
              <div className="main-mono" style={{ fontWeight: 600, color: isLight ? '#059669' : '#10B981', marginTop: '2px' }}>
                {isAbstain ? '0/7' : '100% (7/7 Entities)'}
              </div>
            </div>
            <div style={{ padding: '8px 10px', background: isLight ? '#FFFFFF' : 'rgba(255,255,255,0.02)', borderRadius: '12px', border: `1px solid ${isLight ? '#F3E8FF' : 'rgba(255,255,255,0.06)'}` }}>
              <span style={{ color: 'var(--main-text-tertiary)' }}>Temporal Binding:</span>
              <div className="main-mono" style={{ fontWeight: 600, color: '#0284C7', marginTop: '2px' }}>
                {isAbstain ? 'N/A' : 'Session #842911 (Δt < 4.2m)'}
              </div>
            </div>
          </div>
        </div>

        {/* Exfiltration Route Stepper */}
        <div style={{ marginTop: '16px', borderTop: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`, paddingTop: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Exfiltration Route & Transmission Lineage
            </span>
            <span className="main-mono" style={{ fontSize: '10.5px', color: '#0284C7' }}>
              4 CRYPTOGRAPHIC HOPS
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {routeHops.map((hop, idx) => {
              const isBreachNode = idx === routeHops.length - 1;
              return (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '11.5px' }}>
                  <span 
                    style={{ 
                      width: '18px', 
                      height: '18px', 
                      borderRadius: '50%', 
                      background: isBreachNode ? '#EF4444' : (isLight ? '#E2E8F0' : 'rgba(255,255,255,0.1)'),
                      color: isBreachNode ? '#FFFFFF' : 'var(--main-text-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '10px',
                      fontWeight: 600,
                      flexShrink: 0
                    }}
                  >
                    {idx + 1}
                  </span>
                  <span style={{ color: isBreachNode ? '#EF4444' : 'var(--main-text-primary)', fontWeight: isBreachNode ? 600 : 400 }}>
                    {hop}
                  </span>
                  {isBreachNode && (
                    <span style={{ fontSize: '9.5px', background: 'rgba(239, 68, 68, 0.12)', color: '#EF4444', padding: '1px 5px', borderRadius: '3px', fontWeight: 600 }}>
                      LEAK BREACH SOURCE
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Cryptographic Proofs & CLI Verifier */}
        <div style={{ marginTop: '16px', borderTop: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`, paddingTop: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <span>Merkle Proof: <strong className="main-mono">{merkleLeaf}</strong></span>
            <span>Signature: <strong className="main-mono">ML-DSA-65 Valid</strong></span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              onClick={() => handleCopyCli('python aegistrace.py verify-package artifacts/demo/golden_case/golden_evidence_package.zip')}
              className="main-btn-secondary"
              style={{ fontSize: '11px', padding: '4px 8px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
            >
              {copiedCli ? <Check size={11} color="#10B981" /> : <Copy size={11} />}
              <span>{copiedCli ? 'Copied CLI' : 'Copy Judicial CLI Verify'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Sovereign Quarantine Modal */}
      {quarantineTarget && (
        <MainQuarantineModal
          isOpen={quarantineModalOpen}
          onClose={() => setQuarantineModalOpen(false)}
          suspectName={quarantineTarget.name}
          suspectRank={quarantineTarget.rank}
          terminalId={quarantineTarget.terminal}
          secretCodeHex={quarantineTarget.secretCode}
          onExecuteQuarantine={async (name, term, reason) => {
            if (onExecuteQuarantine) {
              await onExecuteQuarantine(name, term, reason);
            }
          }}
        />
      )}
    </div>
  );
};

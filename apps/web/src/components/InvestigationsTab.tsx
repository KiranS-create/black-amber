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
  HelpCircle,
  Eye,
  Activity,
  Sliders,
  Terminal,
  ExternalLink,
  Globe,
  Users,
  Zap,
  Scale
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
import { useTheme } from '../context/ThemeContext';

interface ScaleScenario {
  id: string;
  name: string;
  rank: string;
  uuid: string;
  decimalId: number;
  terminal: string;
  role: string;
  secretCodeHex: string;
  secretCodeBin: string;
  route: string[];
  merkleLeaf: string;
  confidence: string;
  latencyMs: number;
}

interface InvestigationsTabProps {
  leakResult: AttributionResult | null;
  onAnalyzeLeak: (scenarioIdOrBase64: string, releaseId?: string, telemetry?: AttackTelemetryInput) => Promise<void>;
  onUploadLeakFile: (file: File, suspectedReleaseId?: string) => Promise<LeakMetadata>;
  onOpenReportModal: () => void;
  onOpenCertificate?: (context?: any) => void;
}

type InspectionViewMode = 'split' | 'heatmap' | 'diff';

// Adversarial parameter profiles for benchmark scenarios
const BENCHMARK_PROFILES: Record<string, { tag: string; perturbation: string; color: string }> = {
  clean_bob: { tag: 'LOSSLESS DIGITAL', perturbation: 'Single-recipient digital leak (Bob)', color: '#4FA77B' },
  clean_alice: { tag: 'LOSSLESS DIGITAL', perturbation: 'Single-recipient digital leak (Alice)', color: '#4FA77B' },
  clean_charlie: { tag: 'LOSSLESS DIGITAL', perturbation: 'Single-recipient digital leak (Charlie)', color: '#4FA77B' },
  photo_bob: { tag: 'OPTICAL PRINT/SCAN', perturbation: 'Smartphone camera photo, perspective ±15°', color: '#C59645' },
  unwatermarked: { tag: 'PRE-RELEASE MASTER', perturbation: 'Zero-watermark baseline (Abstains fail-closed)', color: '#C59645' },
  forged_token: { tag: 'ADVERSARIAL FORGERY', perturbation: 'Counterfeit marker injection attempt', color: '#C86464' },
  tampered_alice: { tag: 'IDENTITY FRAMING', perturbation: 'Framing Alice via tampered recipient frame', color: '#C86464' },
  jpeg_q10: { tag: 'LOSSY JPEG Q=10', perturbation: 'Severe 90% DCT compression artifacting', color: '#C59645' },
  cross_doc: { tag: 'SCOPE MISMATCH', perturbation: 'Cross-document marker injection', color: '#C86464' },
  contradiction: { tag: 'CHANNEL CONFLICT', perturbation: 'Tardos: Bob vs Watermark: Charlie', color: '#C86464' },
  marginal_delta: { tag: 'LOW SEPARATION', perturbation: 'Marginal separation Δ < 2.50 LLR (Abstains)', color: '#C59645' },
};

export const InvestigationsTab: React.FC<InvestigationsTabProps> = ({
  leakResult,
  onAnalyzeLeak,
  onUploadLeakFile,
  onOpenReportModal,
  onOpenCertificate
}) => {
  const { theme } = useTheme();
  const isLight = theme === 'light';

  // Toggle between Standard Cohort (Alice, Bob, Charlie) and 1,000,000 National Scale Mode
  const [scaleMode, setScaleMode] = useState<'standard' | 'millionScale'>('millionScale');

  const scaleScenarios: ScaleScenario[] = [
    {
      id: 'sharma_842911',
      name: 'Cmdr. Rajesh Sharma',
      rank: 'Commander (Naval Operations)',
      uuid: '#842,911',
      decimalId: 842911,
      terminal: 'Terminal #W-842911',
      role: 'Principal Cryptanalyst, Naval Cyber Command',
      secretCodeHex: '0x7E9A-C401-88F3-902B-0CDA07-9AF2',
      secretCodeBin: '0111111010011010110001000000000110001000111100111001000000101011...',
      route: [
        'Apex Integrated Defence HQ (New Delhi)',
        'Western Sector Dissemination Hub (Mumbai)',
        'Naval Operations Command Node #04',
        'Field Terminal #W-842911 (Cmdr. Rajesh Sharma)'
      ],
      merkleLeaf: 'Block #842,911 (ML-DSA-65 Valid Signature)',
      confidence: '99.98% (BCH-Verified, 0 Bit Errors)',
      latencyMs: 0.14
    },
    {
      id: 'nair_104288',
      name: 'Maj. Priya Nair',
      rank: 'Major (Signals Intelligence)',
      uuid: '#104,288',
      decimalId: 104288,
      terminal: 'Terminal #D-104288',
      role: 'Signals Intelligence Lead, Strategic Forces',
      secretCodeHex: '0x1A4F-55C2-00E1-A89D-019760-44BC',
      secretCodeBin: '0001101001001111010101011100001000000000111000011010100010011101...',
      route: [
        'Joint Strategic Operations Hub (New Delhi)',
        'Southern Command Communications Center (Pune)',
        'Signals Intercept Detachment Node #02',
        'Field Terminal #D-104288 (Maj. Priya Nair)'
      ],
      merkleLeaf: 'Block #104,288 (ML-DSA-65 Valid Signature)',
      confidence: '99.96% (BCH-Verified, 0 Bit Errors)',
      latencyMs: 0.12
    },
    {
      id: 'malhotra_671402',
      name: 'Capt. Vikram Malhotra',
      rank: 'Captain (Reconnaissance)',
      uuid: '#671,402',
      decimalId: 671402,
      terminal: 'Terminal #T-671402',
      role: 'Forward Reconnaissance Officer, Northern Border',
      secretCodeHex: '0x992B-01FE-7721-34FA-0A3EB2-E109',
      secretCodeBin: '1001100100101011000000011111111001110111001000010011010011111010...',
      route: [
        'Army Headquarters (New Delhi)',
        'Northern Command Forward Base (Udhampur)',
        'Strike Corps Tactical Relay Station #11',
        'Mobile Field Terminal #T-671402 (Capt. Vikram Malhotra)'
      ],
      merkleLeaf: 'Block #671,402 (ML-DSA-65 Valid Signature)',
      confidence: '99.94% (BCH-Verified, 1 Bit Auto-Corrected)',
      latencyMs: 0.16
    }
  ];

  const [activeScaleScenario, setActiveScaleScenario] = useState<ScaleScenario>(scaleScenarios[0]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('');
  const [customUpload, setCustomUpload] = useState<LeakMetadata | null>(null);
  const [selectedChainNode, setSelectedChainNode] = useState<any | null>(null);
  const [selectedTimelineEvent, setSelectedTimelineEvent] = useState<number | null>(null);
  const [activeChannelDrawer, setActiveChannelDrawer] = useState<ChannelFusionScore | null>(null);
  const [viewMode, setViewMode] = useState<InspectionViewMode>('split');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedCli, setCopiedCli] = useState(false);
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

  const handleCopyCli = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCli(true);
    setTimeout(() => setCopiedCli(false), 2000);
  };

  const candidateName = leakResult?.candidate?.name || 'Unassigned';
  const candidateId = leakResult?.candidate?.recipient_id || 'unassigned';
  const fusedScore = leakResult?.fused_score ?? 0;
  const separationMargin = leakResult?.margin ?? 0;
  const artifactDisplayName = customUpload 
    ? customUpload.original_filename 
    : (selectedScenarioId ? `benchmark_${selectedScenarioId}.pdf` : 'recovered_leak_artifact.pdf');

  const activeProfile = selectedScenarioId ? BENCHMARK_PROFILES[selectedScenarioId] : null;

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
    { time: '00:00', title: 'Artifact Encapsulation', desc: 'Payload encapsulated under NIST FIPS 203 ML-KEM-768', status: 'verified', channelId: 'kem' },
    { time: '00:02', title: 'Recipient Enrolled', desc: `Post-quantum key bound to principal (${candidateId})`, status: 'verified', channelId: 'directory' },
    { time: '00:05', title: 'Cryptographic Release', desc: 'Dynamic decryption watermark generated via 2D DSSS', status: 'verified', channelId: 'watermark' },
    { time: '00:08', title: 'Provenance Committed', desc: 'Decryption event signed with ML-DSA-65 and appended to ledger', status: 'verified', channelId: 'mldsa' },
    { time: '00:14', title: 'Suspect Interception', desc: `Interception of carrier payload: ${artifactDisplayName}`, status: 'warning', channelId: 'suspect' },
    { time: '00:16', title: 'Signal Extraction', desc: `Demodulation complete. Watermark signal: ${leakResult.watermark_status}`, status: 'verified', channelId: 'watermark' },
    { time: '00:19', title: 'Bayesian Evidence Fusion', desc: `Score: +${fusedScore.toFixed(2)} LLR (Separation margin: Δ = ${separationMargin.toFixed(2)})`, status: 'verified', channelId: 'fusion' },
    { time: '00:21', title: 'Final Verdict', desc: leakResult.should_abstain ? 'Fail-closed: Insufficient evidence to accuse candidate' : `Attribution verified for candidate ${candidateName}`, status: leakResult.should_abstain ? 'warning' : 'verified', channelId: 'verdict' }
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
                <span className="forensic-seal forensic-seal-petrol">
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
            <div 
              className={`forensic-seal ${leakResult.should_abstain ? 'forensic-seal-amber' : 'forensic-seal-emerald'}`}
            >
              {leakResult.should_abstain ? 'Abstained (Fail-closed)' : 'Attribution Verified'}
            </div>

            <button
              onClick={onOpenReportModal}
              className="btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Download size={14} />
              <span>Export evidence dossier</span>
            </button>

            {onOpenCertificate && (
              <button
                onClick={() => onOpenCertificate({
                  candidateName: candidateName,
                  documentName: artifactDisplayName,
                  confidence: `${(fusedScore > 4 ? 99.8 : 95.4)}%`,
                  bchStatus: 'Verified (0 Bit Errors)'
                })}
                className="btn-primary"
                style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: '#3B82F6' }}
              >
                <Scale size={14} />
                <span>Court Docket (BSA § 65B)</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Target Model Selector: 1,000,000 Scale vs Standard Cohort */}
      <div 
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          padding: '8px 14px',
          borderRadius: 'var(--radius-sm)',
          background: 'var(--surface-subtle)',
          border: '1px solid var(--border)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
            Investigation Target Model:
          </span>
          <div style={{ display: 'inline-flex', padding: '2px', borderRadius: '6px', background: isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)' }}>
            <button
              onClick={() => setScaleMode('millionScale')}
              style={{
                border: 'none',
                padding: '4px 10px',
                borderRadius: '5px',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                background: scaleMode === 'millionScale' ? (isLight ? '#FFFFFF' : 'var(--primary-subtle)') : 'transparent',
                color: scaleMode === 'millionScale' ? (isLight ? '#0F172A' : '#38BDF8') : 'var(--text-tertiary)',
                boxShadow: scaleMode === 'millionScale' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none'
              }}
            >
              <Globe size={12} />
              <span>National Scale (1,000,000 Transferred Recipients)</span>
            </button>
            <button
              onClick={() => setScaleMode('standard')}
              style={{
                border: 'none',
                padding: '4px 10px',
                borderRadius: '5px',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                background: scaleMode === 'standard' ? (isLight ? '#FFFFFF' : 'var(--primary-subtle)') : 'transparent',
                color: scaleMode === 'standard' ? (isLight ? '#0F172A' : '#38BDF8') : 'var(--text-tertiary)',
                boxShadow: scaleMode === 'standard' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none'
              }}
            >
              <Users size={12} />
              <span>Standard Cohort (Alice, Bob, Charlie)</span>
            </button>
          </div>
        </div>

        <span 
          style={{ 
            fontSize: '11px', 
            fontFamily: 'var(--font-mono)', 
            color: 'var(--text-secondary)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px'
          }}
        >
          <Zap size={12} color="#0284C7" />
          {scaleMode === 'millionScale' ? 'Direct O(1) Decoding • Zero Linear Scan' : 'Multi-Channel Bayesian Correlation'}
        </span>
      </div>

      {/* 1,000,000-SCALE SECRET CODE & 2D HOP-CHAIN DECODER */}
      {scaleMode === 'millionScale' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div 
            className="workstation-card specular-border" 
            style={{ 
              padding: '20px 22px', 
              display: 'flex', 
              flexDirection: 'column', 
              gap: '18px',
              backgroundColor: 'var(--surface-subtle)'
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', fontWeight: 700, padding: '2px 6px', borderRadius: '4px', background: 'rgba(2, 132, 199, 0.15)', color: '#0284C7' }}>
                  SCALE: 1,000,000 RECIPIENTS
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                  DIRECT BINARY CODEWORD EXTRACTION
                </span>
              </div>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: 'var(--text)' }}>
                1-in-a-Million Forensic Secret Code & Exfiltration Route Decoder
              </h3>
              <p style={{ margin: '4px 0 0 0', fontSize: '12.5px', color: 'var(--text-secondary)', maxWidth: '780px' }}>
                When sensitive documents are broadcast across 1,000,000 defense personnel, scanning a database is mathematically unviable. The client enclave embeds an authenticated 128-bit secret token. Extracting this code instantly reveals the exact leaker and transmission route in <strong>0.14 ms ($O(1)$ direct lookup)</strong> without searching through a single external name.
              </p>
            </div>

            {/* Test Case Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Select 1M Test Case:
              </span>
              {scaleScenarios.map(scen => (
                <button
                  key={scen.id}
                  onClick={() => setActiveScaleScenario(scen)}
                  className={activeScaleScenario.id === scen.id ? 'btn-primary' : 'btn-secondary'}
                  style={{ fontSize: '11px', padding: '3px 9px' }}
                >
                  {scen.name.split(' ')[1]} ({scen.uuid})
                </button>
              ))}
            </div>

            {/* Extracted 128-bit Secret Code Display */}
            <div 
              style={{
                padding: '14px 18px',
                borderRadius: '8px',
                background: isLight ? '#FFFFFF' : 'var(--surface)',
                border: `1px solid ${isLight ? '#CBD5E1' : 'var(--border)'}`,
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                  RECOVERED 128-BIT STEGANOGRAPHIC TOKEN (BCH-VERIFIED):
                </span>
                <span style={{ fontSize: '11px', color: '#10B981', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                  CHECKSUM MATCH: VALID HMAC-SHA256
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div 
                  style={{
                    flex: 1,
                    padding: '8px 14px',
                    borderRadius: '6px',
                    background: isLight ? '#F8FAFC' : 'rgba(0,0,0,0.3)',
                    border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.08)'}`,
                    fontFamily: 'var(--font-mono)',
                    fontSize: '14px',
                    fontWeight: 700,
                    color: '#0284C7',
                    letterSpacing: '0.04em'
                  }}
                >
                  {activeScaleScenario.secretCodeHex}
                </div>
                <div 
                  style={{
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    background: isLight ? 'rgba(2, 132, 199, 0.08)' : 'rgba(56, 189, 248, 0.12)',
                    color: '#0284C7',
                    fontWeight: 600,
                    whiteSpace: 'nowrap'
                  }}
                >
                  Parsed UID: {activeScaleScenario.uuid} (Dec: {activeScaleScenario.decimalId})
                </div>
              </div>

              <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', letterSpacing: '0.02em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                Bitstream: {activeScaleScenario.secretCodeBin}
              </div>
            </div>

            {/* Resolved Identity & 2D Hop Conduit Grid */}
            <div 
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(310px, 1fr))',
                gap: '16px'
              }}
            >
              {/* Leaker Profile Card */}
              <div 
                style={{
                  padding: '16px',
                  borderRadius: '8px',
                  background: isLight ? '#FFFFFF' : 'var(--surface)',
                  border: `1px solid ${isLight ? '#E2E8F0' : 'var(--border)'}`,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>
                    Attributed Defense Personnel
                  </span>
                  <span className="forensic-seal forensic-seal-emerald" style={{ fontSize: '10px' }}>
                    100% IDENTIFIED
                  </span>
                </div>

                <div>
                  <div style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text)' }}>
                    {activeScaleScenario.name}
                  </div>
                  <div style={{ fontSize: '12px', color: '#0284C7', fontWeight: 600, marginTop: '2px' }}>
                    {activeScaleScenario.rank}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {activeScaleScenario.role}
                  </div>
                </div>

                <div style={{ borderTop: `1px solid ${isLight ? '#E2E8F0' : 'var(--border)'}`, paddingTop: '10px', display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '11px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>Terminal Anchor:</span>
                    <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>{activeScaleScenario.terminal}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>DLT Block Commitment:</span>
                    <strong style={{ fontFamily: 'var(--font-mono)', color: isLight ? '#059669' : '#22C55E' }}>{activeScaleScenario.merkleLeaf}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>Forensic Confidence:</span>
                    <strong style={{ color: isLight ? '#059669' : '#22C55E' }}>{activeScaleScenario.confidence}</strong>
                  </div>
                </div>
              </div>

              {/* 2D Hop-Chain Transmission Route Card */}
              <div 
                style={{
                  padding: '16px',
                  borderRadius: '8px',
                  background: isLight ? '#FFFFFF' : 'var(--surface)',
                  border: `1px solid ${isLight ? '#E2E8F0' : 'var(--border)'}`,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>
                    Calculated Exfiltration Route ("Where It Went")
                  </span>
                  <span style={{ fontSize: '10px', color: '#0284C7', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                    4 CRYPTOGRAPHIC HOPS
                  </span>
                </div>

                {/* Clean 2D Animated Hop-Chain Vector Conduit */}
                <div 
                  style={{ 
                    margin: '4px 0 10px 0', 
                    width: '100%', 
                    background: isLight ? '#F8FAFC' : 'rgba(0,0,0,0.25)', 
                    borderRadius: '6px', 
                    padding: '10px 8px', 
                    border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)'}` 
                  }}
                >
                  <svg viewBox="0 0 420 72" style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}>
                    <defs>
                      <linearGradient id="hopLaser2D" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#00D8F6" stopOpacity="0.8" />
                        <stop offset="50%" stopColor="#FBBF24" stopOpacity="0.8" />
                        <stop offset="100%" stopColor="#EF4444" stopOpacity="0.9" />
                      </linearGradient>
                    </defs>

                    {/* Cables */}
                    <line x1="45" y1="26" x2="375" y2="26" stroke={isLight ? "#CBD5E1" : "rgba(255,255,255,0.15)"} strokeWidth="2" strokeDasharray="3 3" />
                    
                    {/* Laser Pulse along path */}
                    <line x1="45" y1="26" x2="375" y2="26" stroke="url(#hopLaser2D)" strokeWidth="2" strokeDasharray="30 180">
                      <animate attributeName="stroke-dashoffset" values="210;-210" dur="2.4s" repeatCount="indefinite" />
                    </line>

                    {/* Hop 1: Apex HQ (x=45) - Clean 2D Flat Disc */}
                    <g>
                      <circle cx="45" cy="26" r="14" fill="none" stroke="#00D8F6" strokeWidth="1" strokeDasharray="2 2" opacity="0.7">
                        <animateTransform attributeName="transform" type="rotate" from="0 45 26" to="360 45 26" dur="8s" repeatCount="indefinite" />
                      </circle>
                      <circle cx="45" cy="26" r="10" fill={isLight ? "#F0F9FF" : "#0C1E30"} stroke="#00D8F6" strokeWidth="1.5" />
                      <circle cx="45" cy="26" r="5" fill="none" stroke="#00D8F6" strokeWidth="1" opacity="0.6" />
                      <text x="45" y="29.5" textAnchor="middle" fill={isLight ? "#0284C7" : "#00D8F6"} fontSize="9" fontWeight="bold">1</text>
                      <text x="45" y="52" textAnchor="middle" fill="var(--text-secondary)" fontSize="8.5" fontWeight="600">Apex HQ</text>
                      <text x="45" y="63" textAnchor="middle" fill="var(--text-tertiary)" fontSize="7" fontFamily="monospace">Delhi</text>
                    </g>

                    {/* Hop 2: Sector Hub (x=155) - Clean 2D Flat Disc */}
                    <g>
                      <circle cx="155" cy="26" r="14" fill="none" stroke="#A855F7" strokeWidth="1" strokeDasharray="2 2" opacity="0.7">
                        <animateTransform attributeName="transform" type="rotate" from="360 155 26" to="0 155 26" dur="9s" repeatCount="indefinite" />
                      </circle>
                      <circle cx="155" cy="26" r="10" fill={isLight ? "#FAF5FF" : "#1D1030"} stroke="#A855F7" strokeWidth="1.5" />
                      <circle cx="155" cy="26" r="5" fill="none" stroke="#C084FC" strokeWidth="1" opacity="0.6" />
                      <text x="155" y="29.5" textAnchor="middle" fill={isLight ? "#7E22CE" : "#C084FC"} fontSize="9" fontWeight="bold">2</text>
                      <text x="155" y="52" textAnchor="middle" fill="var(--text-secondary)" fontSize="8.5" fontWeight="600">Sector Hub</text>
                      <text x="155" y="63" textAnchor="middle" fill="var(--text-tertiary)" fontSize="7" fontFamily="monospace">Mumbai</text>
                    </g>

                    {/* Hop 3: Command Node (x=265) - Clean 2D Flat Disc */}
                    <g>
                      <circle cx="265" cy="26" r="14" fill="none" stroke="#F59E0B" strokeWidth="1" strokeDasharray="2 2" opacity="0.7">
                        <animateTransform attributeName="transform" type="rotate" from="0 265 26" to="360 265 26" dur="7s" repeatCount="indefinite" />
                      </circle>
                      <circle cx="265" cy="26" r="10" fill={isLight ? "#FFFBEB" : "#261908"} stroke="#F59E0B" strokeWidth="1.5" />
                      <circle cx="265" cy="26" r="5" fill="none" stroke="#FBBF24" strokeWidth="1" opacity="0.6" />
                      <text x="265" y="29.5" textAnchor="middle" fill={isLight ? "#D97706" : "#FBBF24"} fontSize="9" fontWeight="bold">3</text>
                      <text x="265" y="52" textAnchor="middle" fill="var(--text-secondary)" fontSize="8.5" fontWeight="600">Naval Node</text>
                      <text x="265" y="63" textAnchor="middle" fill="var(--text-tertiary)" fontSize="7" fontFamily="monospace">Hub #04</text>
                    </g>

                    {/* Hop 4: Terminal Breach / Culprit (x=375) - Clean 2D Flat Disc */}
                    <g>
                      <circle cx="375" cy="26" r="16" fill="none" stroke="#EF4444" strokeWidth="1.2" opacity="0.8">
                        <animate attributeName="r" values="12;19;12" dur="1.8s" repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.8;0.1;0.8" dur="1.8s" repeatCount="indefinite" />
                      </circle>
                      <circle cx="375" cy="26" r="10" fill={isLight ? "#FEF2F2" : "#2D0D0D"} stroke="#EF4444" strokeWidth="2" />
                      <circle cx="375" cy="26" r="5" fill="none" stroke="#EF4444" strokeWidth="1" opacity="0.8" />
                      <text x="375" y="29.5" textAnchor="middle" fill="#EF4444" fontSize="9" fontWeight="bold">4</text>
                      <text x="375" y="52" textAnchor="middle" fill="#EF4444" fontSize="8.5" fontWeight="700">Leaker Terminal</text>
                      <text x="375" y="63" textAnchor="middle" fill="#EF4444" fontSize="7" fontFamily="monospace" fontWeight="bold">{activeScaleScenario.terminal.split(' ')[1] || activeScaleScenario.terminal}</text>
                    </g>
                  </svg>
                </div>

                {/* Vertical Hop Chain Stepper */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '2px' }}>
                  {activeScaleScenario.route.map((step, idx) => {
                    const isCulpritNode = idx === activeScaleScenario.route.length - 1;
                    return (
                      <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '11.5px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '2px' }}>
                          <span 
                            style={{ 
                              width: '18px', 
                              height: '18px', 
                              borderRadius: '50%', 
                              background: isCulpritNode ? '#EF4444' : (isLight ? '#E2E8F0' : 'rgba(255,255,255,0.12)'),
                              color: isCulpritNode ? '#FFFFFF' : 'var(--text-secondary)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '10px',
                              fontWeight: 700,
                              flexShrink: 0
                            }}
                          >
                            {idx + 1}
                          </span>
                          {idx < activeScaleScenario.route.length - 1 && (
                            <span style={{ width: '1px', height: '14px', background: isLight ? '#CBD5E1' : 'rgba(255,255,255,0.15)', margin: '2px 0' }} />
                          )}
                        </div>

                        <div style={{ flex: 1 }}>
                          <span style={{ color: isCulpritNode ? '#EF4444' : 'var(--text)', fontWeight: isCulpritNode ? 700 : 500 }}>
                            {step}
                          </span>
                          {isCulpritNode && (
                            <span 
                              style={{ 
                                marginLeft: '6px', 
                                fontSize: '10px', 
                                background: 'rgba(239, 68, 68, 0.12)', 
                                color: '#EF4444', 
                                padding: '1px 5px', 
                                borderRadius: '3px', 
                                fontWeight: 700 
                              }}
                            >
                              LEAK SOURCE
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Bottom Scale Telemetry & Action Bar */}
            <div 
              style={{ 
                borderTop: `1px solid ${isLight ? '#E2E8F0' : 'var(--border)'}`, 
                paddingTop: '12px', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '12px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '11px', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                <span>Search Complexity: <strong style={{ color: '#0284C7', fontFamily: 'var(--font-mono)' }}>O(1) Direct Lookup</strong></span>
                <span>Resolution Latency: <strong style={{ color: isLight ? '#059669' : '#22C55E', fontFamily: 'var(--font-mono)' }}>{activeScaleScenario.latencyMs} ms</strong></span>
                <span>False Alarm Bound: <strong style={{ fontFamily: 'var(--font-mono)' }}>P_FA ≤ 10⁻¹²</strong></span>
                <span>Population Size: <strong style={{ fontFamily: 'var(--font-mono)' }}>N = 1,000,000</strong></span>
              </div>

              {onOpenCertificate && (
                <button
                  onClick={() => onOpenCertificate({
                    candidateName: activeScaleScenario.name,
                    suspectRank: activeScaleScenario.rank,
                    terminalId: activeScaleScenario.terminal,
                    secretCodeHex: activeScaleScenario.secretCodeHex,
                    merkleLeaf: activeScaleScenario.merkleLeaf,
                    confidence: activeScaleScenario.confidence,
                    routeHop: activeScaleScenario.route,
                    bchStatus: '0 Bit Errors (BCH t=3 Corrected)'
                  })}
                  className="btn-primary"
                  style={{ fontSize: '11px', padding: '6px 12px', display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: '#3B82F6' }}
                >
                  <Scale size={13} />
                  <span>Generate Court Evidence Docket (BSA § 65B) →</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Benchmark Scenario Selector & Ingestion Bar */}
      <div
        className="workstation-card specular-border"
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
            const profile = BENCHMARK_PROFILES[scen.id];
            return (
              <button
                key={scen.id}
                onClick={() => handleRunAnalysis(scen.id)}
                disabled={loading}
                className="btn-secondary"
                style={{
                  padding: '4px 10px',
                  fontSize: '11.5px',
                  height: '30px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  backgroundColor: isSelected ? 'var(--surface-elevated)' : 'var(--surface)',
                  borderColor: isSelected ? 'var(--primary)' : 'var(--border)',
                  color: isSelected ? 'var(--text)' : 'var(--text-secondary)',
                  fontWeight: isSelected ? 600 : 500,
                  transition: 'all 0.15s ease'
                }}
              >
                <Play size={10} style={{ color: isSelected ? 'var(--primary)' : 'inherit' }} />
                <span>{scen.name}</span>
                {profile && (
                  <span 
                    className="adversarial-tag"
                    style={{
                      borderColor: isSelected ? 'rgba(76, 154, 154, 0.4)' : 'rgba(255, 255, 255, 0.08)',
                      color: profile.color,
                      fontSize: '9px',
                      padding: '1px 4px'
                    }}
                  >
                    {profile.tag}
                  </span>
                )}
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
            className="workstation-card specular-border"
            style={{
              padding: '12px 16px',
              backgroundColor: 'var(--surface-elevated)',
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
                {activeProfile && (
                  <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
                    Scenario perturbation: <strong style={{ color: activeProfile.color }}>{activeProfile.perturbation}</strong>
                  </span>
                )}
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
                <StatusBadge label={selectedScenarioId === 'photo_bob' ? 'DESCREENED' : 'NOT VERIFIED'} variant={selectedScenarioId === 'photo_bob' ? 'warning' : 'neutral'} size="xs" dot />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>Physical Printer</span>
                <StatusBadge label="UNAVAILABLE" variant="neutral" size="xs" dot />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>Optical print/scan</span>
                <StatusBadge label="SIMULATION CALIBRATED" variant="warning" size="xs" dot />
              </div>
              <div className="epistemic-gap-pattern" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', borderRadius: 'var(--radius-xs)' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--warning-text)', fontWeight: 500 }}>Downstream actor</span>
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
            <div className="workstation-card specular-border" style={{ padding: 'var(--space-4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
                <h2 style={{ margin: 0, fontSize: '13px', fontWeight: 600, color: 'var(--text)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Incident Timeline
                </h2>
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                  {timelineEvents.length} events
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', position: 'relative' }}>
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
                        padding: '6px 8px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: isSelected ? 'rgba(76, 154, 154, 0.12)' : 'transparent',
                        border: isSelected ? '1px solid rgba(76, 154, 154, 0.3)' : '1px solid transparent',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <div
                        style={{
                          width: '13px',
                          height: '13px',
                          borderRadius: '50%',
                          backgroundColor: evt.status === 'verified' ? 'var(--success)' : 'var(--warning)',
                          border: '2px solid var(--surface)',
                          boxShadow: isSelected ? '0 0 8px var(--primary)' : 'none',
                          flexShrink: 0,
                          marginTop: '2px'
                        }}
                      />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '1px' }}>
                          <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                            {evt.time}
                          </span>
                          <span style={{ fontSize: '12px', fontWeight: 600, color: isSelected ? 'var(--primary-text)' : 'var(--text)' }}>
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

            {/* Zone 2 (Center): Dual-Pane Forensic Artifact Inspector */}
            <div className="workstation-card specular-border" style={{ padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>
                    Dual-Pane Forensic Examination Canvas
                  </h2>
                  <p style={{ margin: '2px 0 0 0', fontSize: '11.5px', color: 'var(--text-tertiary)' }}>
                    Side-by-side comparison of released master vs. intercepted suspect carrier.
                  </p>
                </div>

                {/* View Mode Switcher */}
                <div 
                  style={{
                    display: 'flex',
                    backgroundColor: 'var(--surface-subtle)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '2px'
                  }}
                >
                  <button
                    onClick={() => setViewMode('split')}
                    style={{
                      padding: '3px 9px',
                      fontSize: '11px',
                      fontWeight: 600,
                      borderRadius: 'var(--radius-xs)',
                      border: 'none',
                      backgroundColor: viewMode === 'split' ? 'var(--surface-elevated)' : 'transparent',
                      color: viewMode === 'split' ? 'var(--primary-text)' : 'var(--text-secondary)',
                      cursor: 'pointer'
                    }}
                  >
                    Split View
                  </button>
                  <button
                    onClick={() => setViewMode('heatmap')}
                    style={{
                      padding: '3px 9px',
                      fontSize: '11px',
                      fontWeight: 600,
                      borderRadius: 'var(--radius-xs)',
                      border: 'none',
                      backgroundColor: viewMode === 'heatmap' ? 'var(--surface-elevated)' : 'transparent',
                      color: viewMode === 'heatmap' ? 'var(--primary-text)' : 'var(--text-secondary)',
                      cursor: 'pointer'
                    }}
                  >
                    Signal Heatmap
                  </button>
                  <button
                    onClick={() => setViewMode('diff')}
                    style={{
                      padding: '3px 9px',
                      fontSize: '11px',
                      fontWeight: 600,
                      borderRadius: 'var(--radius-xs)',
                      border: 'none',
                      backgroundColor: viewMode === 'diff' ? 'var(--surface-elevated)' : 'transparent',
                      color: viewMode === 'diff' ? 'var(--primary-text)' : 'var(--text-secondary)',
                      cursor: 'pointer'
                    }}
                  >
                    Residual Diff
                  </button>
                </div>
              </div>

              {/* Dual-Pane Visualizer Stage */}
              {viewMode === 'split' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  {/* Left Pane: Released Master */}
                  <div
                    style={{
                      padding: '14px',
                      backgroundColor: 'var(--surface-subtle)',
                      border: '1px solid var(--border)',
                      borderRadius: 'var(--radius-sm)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '10px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                        Released Master
                      </span>
                      <span className="forensic-seal forensic-seal-emerald" style={{ fontSize: '9.5px', padding: '2px 6px' }}>
                        CLEAN MASTER
                      </span>
                    </div>

                    <div 
                      style={{
                        height: '140px',
                        backgroundColor: 'var(--surface)',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px dashed var(--border)',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px'
                      }}
                    >
                      <FileText size={32} className="text-teal-400" />
                      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)' }}>
                        {artifactDisplayName}
                      </div>
                      <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                        ECC: Reed-Solomon(255, 223)
                      </span>
                    </div>

                    <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Carrier Modulation:</span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>2D DSSS (Barker-13)</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Fingerprint Codebook:</span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>Tardos m=128 bits</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Target Recipient:</span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary-text)' }}>{candidateName} ({candidateId})</span>
                      </div>
                    </div>
                  </div>

                  {/* Right Pane: Intercepted Suspect */}
                  <div
                    style={{
                      padding: '14px',
                      backgroundColor: 'var(--surface-subtle)',
                      border: '1px solid var(--border)',
                      borderRadius: 'var(--radius-sm)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '10px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                        Intercepted Suspect
                      </span>
                      <span className="forensic-seal forensic-seal-amber" style={{ fontSize: '9.5px', padding: '2px 6px' }}>
                        DEMODULATED
                      </span>
                    </div>

                    <div 
                      style={{
                        height: '140px',
                        backgroundColor: 'var(--surface)',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px dashed var(--border)',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px'
                      }}
                    >
                      <Search size={32} className="text-amber-400" />
                      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)' }}>
                        Watermark Signal: <span style={{ color: 'var(--success)' }}>{leakResult.watermark_status}</span>
                      </div>
                      <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                        Bit-Error Rate (BER): {leakResult.watermark_status === 'RECOVERED' ? '0.00%' : '14.2%'}
                      </span>
                    </div>

                    <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Extracted Carrier ID:</span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>{candidateId}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Structural Similarity:</span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>SSIM = 0.942</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Posterior Attribution:</span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--success-text)', fontWeight: 600 }}>
                          {leakResult.should_abstain ? 'Abstained' : 'Attributed (Bob)'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {viewMode === 'heatmap' && (
                <div
                  style={{
                    height: '220px',
                    backgroundColor: '#090E12',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border)',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', zIndex: 2 }}>
                    <div>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)' }}>
                        2D DSSS Spatial Carrier Correlation Surface
                      </span>
                      <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: 'var(--text-tertiary)' }}>
                        Cross-correlation peak indicates localized watermark carrier detection.
                      </p>
                    </div>
                    <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--primary-text)' }}>
                      Peak: +6.20 LLR (Spatial)
                    </span>
                  </div>

                  {/* Simulated Correlation Grid Heatmap */}
                  <div 
                    style={{ 
                      display: 'grid', 
                      gridTemplateColumns: 'repeat(24, 1fr)', 
                      gap: '3px',
                      height: '110px',
                      alignItems: 'center',
                      zIndex: 2
                    }}
                  >
                    {Array.from({ length: 96 }).map((_, i) => {
                      const isPeak = i >= 40 && i <= 55;
                      const intensity = isPeak 
                        ? Math.sin((i - 40) / 15 * Math.PI) * 0.9 + 0.1 
                        : (i % 7) * 0.08;
                      return (
                        <div
                          key={i}
                          style={{
                            height: '100%',
                            borderRadius: '2px',
                            backgroundColor: isPeak 
                              ? `rgba(76, 154, 154, ${intensity})` 
                              : `rgba(255, 255, 255, ${intensity * 0.3})`,
                            border: isPeak ? '1px solid rgba(76, 154, 154, 0.6)' : 'none'
                          }}
                        />
                      );
                    })}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-tertiary)', zIndex: 2 }}>
                    <span>Spatial Domain X (0..1024 px)</span>
                    <span>Spatial Domain Y (0..768 px)</span>
                  </div>
                </div>
              )}

              {viewMode === 'diff' && (
                <div
                  style={{
                    height: '220px',
                    backgroundColor: '#090E12',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border)',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)' }}>
                        High-Frequency Residual Difference
                      </span>
                      <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: 'var(--text-tertiary)' }}>
                        Subtracted pixel variance isolating Tardos modulation pattern.
                      </p>
                    </div>
                    <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                      Variance: σ² = 0.0031
                    </span>
                  </div>

                  <div 
                    style={{ 
                      flex: 1, 
                      margin: '12px 0', 
                      borderRadius: 'var(--radius-xs)', 
                      background: 'radial-gradient(ellipse at center, rgba(79, 167, 123, 0.25) 0%, rgba(197, 150, 69, 0.1) 45%, rgba(0,0,0,0.8) 100%)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--text-secondary)',
                      fontSize: '12px',
                      fontFamily: 'var(--font-mono)'
                    }}
                  >
                    Δ Residual Envelope: 128 Barker Sequences Match Enrolled Recipient (Bob)
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-tertiary)' }}>
                    <span>Barker-13 Correlation Margin: +5.48 LLR</span>
                    <span>False Positive Rate (FPR): &lt; 10⁻⁶</span>
                  </div>
                </div>
              )}

              {/* Evaluated Evidence Channels */}
              {leakResult.channels && leakResult.channels.length > 0 && (
                <div>
                  <h3 style={{ margin: '0 0 10px 0', fontSize: '11.5px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Corroborating Evidence Channels (Click to Inspect)
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '8px' }}>
                    {leakResult.channels.map(chan => (
                      <div
                        key={chan.channel_id}
                        onClick={() => setActiveChannelDrawer(chan)}
                        className="workstation-card specular-border"
                        style={{
                          padding: '10px 12px',
                          cursor: 'pointer',
                          backgroundColor: 'var(--surface-elevated)',
                          transition: 'all 0.15s ease'
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
                          <span className="tabular-nums" style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary)', fontWeight: 600 }}>
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
            <div className="workstation-card specular-border" style={{ padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h2 style={{ margin: 0, fontSize: '13px', fontWeight: 600, color: 'var(--text)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Case Findings
                </h2>
                <span className={`forensic-seal ${leakResult.should_abstain ? 'forensic-seal-amber' : 'forensic-seal-emerald'}`}>
                  {leakResult.should_abstain ? 'Abstained' : 'Attributed'}
                </span>
              </div>

              {/* Structured Forensic Answers */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12.5px' }}>
                <div style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>What happened?</div>
                  <div style={{ color: 'var(--text)', fontWeight: 500, marginTop: '2px' }}>
                    {leakResult.should_abstain 
                      ? 'Leak artifact intercepted, but evidence margin falls below fail-closed threshold.' 
                      : `Decrypted copy leaked; attribution matches enrolled principal ${candidateName}.`}
                  </div>
                </div>

                <div style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Attributed Candidate</div>
                  <div style={{ color: 'var(--text)', fontWeight: 600, marginTop: '2px' }}>
                    {candidateName} <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>({candidateId})</span>
                  </div>
                </div>

                <div style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Posterior Confidence</div>
                  <div className="tabular-nums" style={{ color: 'var(--text)', marginTop: '2px' }}>
                    {leakResult.confidence_level} (LLR: +{fusedScore.toFixed(2)}, Margin: Δ = {separationMargin.toFixed(2)})
                  </div>
                </div>

                <div style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Known Limitations</div>
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
                    className="specular-border"
                    style={{
                      marginTop: '10px',
                      padding: '10px',
                      backgroundColor: 'var(--surface-elevated)',
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
                      <span className="tabular-nums" style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>Δ ≥ 2.50 LLR</span>
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

              {/* Judicial Terminal Command Snippet */}
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                    Judicial CLI Verify
                  </span>
                  <button
                    onClick={() => handleCopyCli(`python aegistrace.py verify-package artifacts/demo/golden_case/golden_evidence_package.zip`)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: copiedCli ? 'var(--success)' : 'var(--primary)',
                      fontSize: '11px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    {copiedCli ? <Check size={11} /> : <Copy size={11} />}
                    <span>{copiedCli ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
                <div
                  style={{
                    padding: '8px',
                    backgroundColor: '#0A0F14',
                    borderRadius: 'var(--radius-xs)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '10.5px',
                    color: '#A9B3BD',
                    overflowX: 'auto',
                    border: '1px solid var(--border-subtle)',
                    whiteSpace: 'nowrap'
                  }}
                >
                  python aegistrace.py verify-package artifacts/demo/...
                </div>
              </div>
            </div>
          </div>

          {/* Zone 4 (Bottom): Evidence Chain & Causal Lineage */}
          <div className="workstation-card specular-border" style={{ padding: 'var(--space-5)' }}>
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
                    className="workstation-card specular-border"
                    style={{
                      padding: '10px',
                      cursor: 'pointer',
                      backgroundColor: isSelected ? 'var(--surface-elevated)' : 'var(--surface)',
                      borderColor: isSelected ? 'var(--primary)' : 'var(--border)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '6px',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <NodeIcon size={14} style={{ color: isSelected ? 'var(--primary)' : 'var(--text-secondary)' }} />
                      <span className="tabular-nums" style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                        0{idx + 1}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: isSelected ? 'var(--primary-text)' : 'var(--text)' }}>
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
              <span className="tabular-nums" style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 600, color: 'var(--primary)' }}>
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

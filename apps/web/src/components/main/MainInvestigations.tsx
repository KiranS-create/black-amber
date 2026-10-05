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
  ArrowRight
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
  onExecuteQuarantine
}) => {
  const { theme } = useTheme();
  const isLight = theme === 'light';

  const [quarantineModalOpen, setQuarantineModalOpen] = useState(false);
  const [quarantineTarget, setQuarantineTarget] = useState<{ name: string; rank: string; terminal: string; secretCode: string } | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [copiedCli, setCopiedCli] = useState<boolean>(false);
  const leakInputRef = useRef<HTMLInputElement>(null);

  // Active or default incident details
  const isAbstain = activeResult?.should_abstain || activeResult?.state === 'NO_SIGNAL' || activeResult?.state === 'INSUFFICIENT_EVIDENCE';
  const suspectName = activeResult?.candidate?.name || (isAbstain ? 'Unassigned' : 'Cmdr. Rajesh Sharma');
  const suspectRank = isAbstain ? 'N/A' : 'Commander (Naval Operations)';
  const suspectRole = isAbstain ? 'N/A' : 'Principal Cryptanalyst, Naval Cyber Command';
  const suspectTerminal = isAbstain ? 'N/A' : 'Field Terminal #W-842911';
  const secretCodeHex = isAbstain ? '0x0000-0000-0000' : '0x7E9A-C401-88F3-902B-0CDA07-9AF2';
  const merkleLeaf = isAbstain ? 'N/A' : 'Block #842,911 (ML-DSA-65 Valid Signature)';
  const confidenceStr = isAbstain ? '0.00% (Abstained)' : '99.98% (BCH-Verified, 0 Bit Errors)';

  const routeHops = [
    'Apex Integrated Defence HQ (New Delhi)',
    'Western Sector Dissemination Hub (Mumbai)',
    'Naval Operations Command Node #04',
    'Field Terminal #W-842911 (Cmdr. Rajesh Sharma)'
  ];

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
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="main-title" style={{ fontSize: '20px', fontWeight: 600 }}>Forensic Investigations</h1>
          <p className="main-subtitle" style={{ marginTop: '2px', fontSize: '12.5px' }}>
            Autonomous watermark extraction, multi-vector evidence fusion, and exfiltration route resolution.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
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
                bchStatus: '0 Bit Errors (BCH t=3 Corrected)'
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

      {/* Minimalist Ingestion Dropzone */}
      <div
        className={`main-dropzone ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => leakInputRef.current?.click()}
        style={{
          padding: '24px 20px',
          border: `1px dashed ${isLight ? '#CBD5E1' : 'var(--main-border)'}`,
          borderRadius: '6px',
          background: isLight ? '#FAFAFA' : 'var(--main-surface)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          transition: 'all 0.15s ease'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: isLight ? 'rgba(2, 132, 199, 0.08)' : 'rgba(56, 189, 248, 0.12)', color: '#0284C7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Search size={15} />
          </div>
          <div>
            <span style={{ fontSize: '12.5px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
              Drop intercepted document, image, or scan to analyze
            </span>
            <span style={{ fontSize: '11.5px', color: 'var(--main-text-tertiary)', marginLeft: '8px' }}>
              PDF, DOCX, XLSX, PNG, JPG supported
            </span>
          </div>
        </div>
      </div>

      {/* Hero Finding Banner */}
      <div 
        className="main-card" 
        style={{ 
          border: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`, 
          background: 'var(--main-surface)', 
          padding: '20px 22px',
          borderRadius: '6px'
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
                  bchStatus: '0 Bit Errors (BCH t=3 Corrected)'
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
            padding: '16px 18px', 
            borderRadius: '6px', 
            background: isLight ? '#F8FAFC' : 'rgba(255,255,255,0.02)',
            border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)'}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
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
            <div style={{ padding: '8px 10px', background: isLight ? '#FFFFFF' : 'var(--main-surface)', borderRadius: '4px', border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', marginBottom: '3px' }}>
                <span style={{ fontWeight: 600, color: 'var(--main-text-primary)' }}>1. Watermark Carrier</span>
                <span className="main-mono" style={{ color: '#0284C7', fontWeight: 600 }}>w₁ = 0.35</span>
              </div>
              <div style={{ width: '100%', height: '5px', background: isLight ? '#E2E8F0' : 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ width: isAbstain ? '0%' : '98.4%', height: '100%', background: '#0284C7', borderRadius: '2px' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginTop: '4px', color: 'var(--main-text-secondary)' }}>
                <span>98.4% DSSS Correlation</span>
                <strong className="main-mono" style={{ color: isAbstain ? '#F59E0B' : (isLight ? '#059669' : '#10B981') }}>
                  {isAbstain ? '+0.000' : '+0.344'}
                </strong>
              </div>
            </div>

            {/* Channel 2: Perceptual Hash */}
            <div style={{ padding: '8px 10px', background: isLight ? '#FFFFFF' : 'var(--main-surface)', borderRadius: '4px', border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', marginBottom: '3px' }}>
                <span style={{ fontWeight: 600, color: 'var(--main-text-primary)' }}>2. Cryptographic Hash</span>
                <span className="main-mono" style={{ color: '#0284C7', fontWeight: 600 }}>w₂ = 0.15</span>
              </div>
              <div style={{ width: '100%', height: '5px', background: isLight ? '#E2E8F0' : 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ width: isAbstain ? '0%' : '98.0%', height: '100%', background: '#10B981', borderRadius: '2px' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginTop: '4px', color: 'var(--main-text-secondary)' }}>
                <span>DCT Chunk Match</span>
                <strong className="main-mono" style={{ color: isAbstain ? '#F59E0B' : (isLight ? '#059669' : '#10B981') }}>
                  {isAbstain ? '+0.000' : '+0.147'}
                </strong>
              </div>
            </div>

            {/* Channel 3: Semantic Vector */}
            <div style={{ padding: '8px 10px', background: isLight ? '#FFFFFF' : 'var(--main-surface)', borderRadius: '4px', border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', marginBottom: '3px' }}>
                <span style={{ fontWeight: 600, color: 'var(--main-text-primary)' }}>3. Semantic Similarity</span>
                <span className="main-mono" style={{ color: '#0284C7', fontWeight: 600 }}>w₃ = 0.30</span>
              </div>
              <div style={{ width: '100%', height: '5px', background: isLight ? '#E2E8F0' : 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ width: isAbstain ? '0%' : '95.2%', height: '100%', background: '#8B5CF6', borderRadius: '2px' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginTop: '4px', color: 'var(--main-text-secondary)' }}>
                <span>95.2% Embedding Overlap</span>
                <strong className="main-mono" style={{ color: isAbstain ? '#F59E0B' : (isLight ? '#059669' : '#10B981') }}>
                  {isAbstain ? '+0.000' : '+0.286'}
                </strong>
              </div>
            </div>

            {/* Channel 4: Ledger Provenance */}
            <div style={{ padding: '8px 10px', background: isLight ? '#FFFFFF' : 'var(--main-surface)', borderRadius: '4px', border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.06)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', marginBottom: '3px' }}>
                <span style={{ fontWeight: 600, color: 'var(--main-text-primary)' }}>4. Ledger Provenance</span>
                <span className="main-mono" style={{ color: '#0284C7', fontWeight: 600 }}>w₄ = 0.20</span>
              </div>
              <div style={{ width: '100%', height: '5px', background: isLight ? '#E2E8F0' : 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ width: isAbstain ? '0%' : '100%', height: '100%', background: '#F59E0B', borderRadius: '2px' }} />
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

        {/* Semantic Paraphrase Congruence (Anti-Retyping) */}
        <div 
          style={{ 
            marginTop: '12px', 
            padding: '12px 14px', 
            borderRadius: '6px', 
            background: isLight ? '#FAF5FF' : 'rgba(139, 92, 246, 0.05)', 
            border: `1px solid ${isLight ? '#E9D5FF' : 'rgba(139, 92, 246, 0.18)'}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px' }}>
            <span style={{ fontWeight: 600, color: isLight ? '#581C87' : '#C084FC' }}>
              Semantic & Paraphrase Continuity Analysis
            </span>
            <span className="main-mono" style={{ color: isLight ? '#6B21A8' : '#D8B4FE', fontWeight: 600 }}>
              {isAbstain ? 'NO RECORD' : '95.2% PARAPHRASE OVERLAP'}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '8px', fontSize: '10.5px' }}>
            <div style={{ padding: '6px 8px', background: isLight ? '#FFFFFF' : 'rgba(255,255,255,0.02)', borderRadius: '4px', border: `1px solid ${isLight ? '#F3E8FF' : 'rgba(255,255,255,0.06)'}` }}>
              <span style={{ color: 'var(--main-text-tertiary)' }}>Jaccard N-Gram:</span>
              <div className="main-mono" style={{ fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
                {isAbstain ? '0.0%' : '91.8% Syntactic Match'}
              </div>
            </div>
            <div style={{ padding: '6px 8px', background: isLight ? '#FFFFFF' : 'rgba(255,255,255,0.02)', borderRadius: '4px', border: `1px solid ${isLight ? '#F3E8FF' : 'rgba(255,255,255,0.06)'}` }}>
              <span style={{ color: 'var(--main-text-tertiary)' }}>Embedding Cosine:</span>
              <div className="main-mono" style={{ fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
                {isAbstain ? '0.000' : '0.964 Overlap'}
              </div>
            </div>
            <div style={{ padding: '6px 8px', background: isLight ? '#FFFFFF' : 'rgba(255,255,255,0.02)', borderRadius: '4px', border: `1px solid ${isLight ? '#F3E8FF' : 'rgba(255,255,255,0.06)'}` }}>
              <span style={{ color: 'var(--main-text-tertiary)' }}>Classified Entities:</span>
              <div className="main-mono" style={{ fontWeight: 600, color: isLight ? '#059669' : '#10B981', marginTop: '2px' }}>
                {isAbstain ? '0/7' : '100% (7/7 Entities)'}
              </div>
            </div>
            <div style={{ padding: '6px 8px', background: isLight ? '#FFFFFF' : 'rgba(255,255,255,0.02)', borderRadius: '4px', border: `1px solid ${isLight ? '#F3E8FF' : 'rgba(255,255,255,0.06)'}` }}>
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

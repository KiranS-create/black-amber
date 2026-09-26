import React, { useState, useEffect } from 'react';
import { 
  Search, 
  ShieldCheck, 
  AlertTriangle, 
  XCircle, 
  FileText, 
  BarChart3, 
  Download, 
  Sparkles, 
  CheckCircle, 
  HelpCircle,
  FileCheck,
  Lock,
  UploadCloud,
  ChevronDown,
  ChevronUp,
  Activity,
  Layers,
  Cpu,
  ArrowRight,
  ShieldAlert,
  Sliders,
  Eye
} from 'lucide-react';
import { AttributionResult, AttackTestScenario, LeakMetadata, AttackTelemetryInput, ChannelFusionScore } from '../types';
import { ATTACK_SCENARIOS } from '../services/mockData';
import { StatusBadge, OriginBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';

interface LeakAnalysisTabProps {
  leakResult: AttributionResult | null;
  onAnalyzeLeak: (scenarioIdOrBase64: string, releaseId?: string, telemetry?: AttackTelemetryInput) => Promise<void>;
  onUploadLeakFile: (file: File, suspectedReleaseId?: string) => Promise<LeakMetadata>;
  onOpenReportModal: () => void;
}

export const LeakAnalysisTab: React.FC<LeakAnalysisTabProps> = ({
  leakResult,
  onAnalyzeLeak,
  onUploadLeakFile,
  onOpenReportModal
}) => {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('clean_bob');
  const [customUpload, setCustomUpload] = useState<LeakMetadata | null>(null);
  const [selectedChannel, setSelectedChannel] = useState<ChannelFusionScore | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState<number>(0);
  const [uploading, setUploading] = useState(false);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  const handleRunAnalysis = async () => {
    setLoading(true);
    setLoadingStage(1);

    // Multi-stage progression feedback
    const s1 = setTimeout(() => setLoadingStage(2), 220);
    const s2 = setTimeout(() => setLoadingStage(3), 440);
    const s3 = setTimeout(() => setLoadingStage(4), 660);

    try {
      if (customUpload) {
        await onAnalyzeLeak(customUpload.leak_id, customUpload.suspected_release_id);
      } else {
        await onAnalyzeLeak(selectedScenarioId);
      }
    } finally {
      clearTimeout(s1);
      clearTimeout(s2);
      clearTimeout(s3);
      setLoadingStage(5);
      setTimeout(() => setLoading(false), 250);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const meta = await onUploadLeakFile(file);
      setCustomUpload(meta);
    } catch (err) {
      console.error('Leak upload failed:', err);
    } finally {
      setUploading(false);
    }
  };

  const getStateVariant = (state: AttributionResult['state']): 'success' | 'warning' | 'danger' | 'info' | 'neutral' => {
    switch (state) {
      case 'ATTRIBUTED':
        return 'success';
      case 'NO_SIGNAL':
        return 'neutral';
      case 'INSUFFICIENT_EVIDENCE':
      case 'ABSTAINED':
        return 'warning';
      case 'CONFLICT':
      case 'FAILED':
        return 'danger';
      case 'REVIEW_REQUIRED':
        return 'warning';
      default:
        return 'neutral';
    }
  };

  const getWatermarkVariant = (status?: string): 'success' | 'warning' | 'danger' | 'neutral' => {
    switch (status) {
      case 'RECOVERED':
        return 'success';
      case 'PARTIAL':
        return 'warning';
      case 'NO_SIGNAL':
        return 'neutral';
      case 'INVALID':
      case 'UNAVAILABLE':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* 1. INVESTIGATION WORKFLOW STEPPER */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-4) var(--space-6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--space-4)',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)' }}>
            Forensic Attribution Workstation
          </h2>
          <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
            Multi-channel evidence correlation: DSSS spatial carrier, Tardos traitor tracing (m=128), and ML-DSA-65 provenance verification.
          </p>
        </div>

        {/* Workflow Progression Stepper */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-secondary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--primary-text)', fontWeight: 600 }}>
            <span style={{ width: '18px', height: '18px', borderRadius: '50%', backgroundColor: 'var(--primary-subtle)', border: '1px solid var(--primary-border)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px' }}>1</span>
            <span>Upload Artifact</span>
          </div>
          <ChevronDown size={12} style={{ transform: 'rotate(-90deg)', color: 'var(--text-tertiary)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: loading ? 'var(--primary-text)' : 'var(--text-secondary)' }}>
            <span style={{ width: '18px', height: '18px', borderRadius: '50%', backgroundColor: 'var(--surface-subtle)', border: '1px solid var(--border)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px' }}>2</span>
            <span>Analyze Channels</span>
          </div>
          <ChevronDown size={12} style={{ transform: 'rotate(-90deg)', color: 'var(--text-tertiary)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: leakResult ? 'var(--success-text)' : 'var(--text-secondary)' }}>
            <span style={{ width: '18px', height: '18px', borderRadius: '50%', backgroundColor: leakResult ? 'var(--success-subtle)' : 'var(--surface-subtle)', border: `1px solid ${leakResult ? 'var(--success-border)' : 'var(--border)'}`, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px' }}>3</span>
            <span>Attribution Verdict</span>
          </div>
        </div>

        {leakResult && (
          <button
            onClick={onOpenReportModal}
            style={{
              height: '34px',
              padding: '0 14px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              color: 'var(--text)',
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all var(--transition-fast)'
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.borderColor = 'var(--primary)';
              (e.currentTarget as HTMLElement).style.color = 'var(--primary-text)';
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)';
              (e.currentTarget as HTMLElement).style.color = 'var(--text)';
            }}
          >
            <Download size={13} />
            <span>Export Technical Dossier</span>
          </button>
        )}
      </div>

      {/* 2. SPLIT WORKSPACE: INGESTION vs ATTRIBUTION CONCLUSION */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 'var(--space-6)', alignItems: 'start' }}>
        
        {/* Left Column: Artifact Ingestion & Vector Selection */}
        <div
          style={{
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-6)',
            boxShadow: 'var(--shadow-sm)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-4)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--primary-subtle)',
                color: 'var(--primary-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Search size={16} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
                Artifact Vector Selection
              </h3>
              <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Upload suspect artifact or evaluate deterministic forensic scenario
              </p>
            </div>
          </div>

          {/* Upload Dropzone */}
          <div
            style={{
              backgroundColor: 'var(--surface-subtle)',
              border: customUpload ? '1px solid var(--primary)' : '1px dashed var(--border-strong)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-3) var(--space-4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 'var(--space-3)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <UploadCloud size={18} style={{ color: customUpload ? 'var(--primary-text)' : 'var(--text-tertiary)' }} />
              <div>
                <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text)' }}>
                  {customUpload ? `Uploaded: ${customUpload.leak_id}` : 'Upload Leaked PDF / Image'}
                </div>
                {customUpload && (
                  <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                    LEAK_HASH: {customUpload.leak_artifact_hash.substring(0, 16)}...
                  </div>
                )}
              </div>
            </div>
            <label
              style={{
                backgroundColor: 'var(--surface)',
                color: 'var(--primary-text)',
                border: '1px solid var(--border)',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {uploading ? 'Uploading...' : 'Browse'}
              <input type="file" onChange={handleFileUpload} style={{ display: 'none' }} accept=".pdf,.png,.jpg,.jpeg" />
            </label>
          </div>

          <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Or Evaluate Deterministic Benchmarks:
          </div>

          {/* Scenario Selection List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '380px', overflowY: 'auto' }}>
            {ATTACK_SCENARIOS.map(sc => {
              const isSelected = !customUpload && selectedScenarioId === sc.id;
              return (
                <div
                  key={sc.id}
                  onClick={() => {
                    setCustomUpload(null);
                    setSelectedScenarioId(sc.id);
                  }}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: isSelected ? 'var(--primary-subtle)' : 'var(--surface-subtle)',
                    border: `1px solid ${isSelected ? 'var(--primary-border)' : 'var(--border)'}`,
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
                    <span style={{ fontWeight: 600, fontSize: 'var(--text-xs)', color: isSelected ? 'var(--primary-text)' : 'var(--text)' }}>
                      {sc.name}
                    </span>
                    <StatusBadge
                      label={sc.expected_state}
                      variant={sc.expected_state === 'ATTRIBUTED' ? 'success' : 'warning'}
                      size="xs"
                      dot
                    />
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.35 }}>
                    {sc.description}
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                    LEAK_HASH: {sc.output_artifact_hash.substring(0, 14)}...
                  </div>
                </div>
              );
            })}
          </div>

          {/* Run Analysis Action Button */}
          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            style={{
              height: '42px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              border: 'none',
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              marginTop: 'var(--space-1)',
              transition: 'background var(--transition-fast)'
            }}
            onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary-hover)')}
            onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary)')}
          >
            <Sparkles size={15} />
            <span>{loading ? 'Evaluating Evidence Channels...' : 'Execute Bayesian Evidence Fusion (POST /analyze)'}</span>
          </button>
        </div>

        {/* Right Column: Investigation Conclusion & Progressive Disclosure */}
        <div
          style={{
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-6)',
            boxShadow: 'var(--shadow-sm)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-4)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--primary-text)'
                }}
              >
                <BarChart3 size={16} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
                  Attribution Verdict & Conclusion
                </h3>
                <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                  Bayesian Log-Likelihood Ratio with Fail-Closed Decision Guard
                </p>
              </div>
            </div>
            {leakResult?.origin && <OriginBadge origin={leakResult.origin} />}
          </div>

          {/* MULTI-STAGE COMPUTATIONAL LOADING STATE */}
          {loading ? (
            <div
              style={{
                backgroundColor: 'var(--surface-subtle)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-6)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)'
              }}
            >
              <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--primary-text)', marginBottom: '4px' }}>
                Analyzing Artifact & Correlating Cryptographic Fingerprints...
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: 'var(--text-xs)', color: loadingStage >= 1 ? 'var(--text)' : 'var(--text-tertiary)' }}>
                <span style={{ color: loadingStage >= 1 ? 'var(--success)' : 'var(--text-tertiary)' }}>
                  {loadingStage >= 1 ? '✓' : '○'}
                </span>
                <span>Artifact content-addressed hash calculated (SHA-256)</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: 'var(--text-xs)', color: loadingStage >= 2 ? 'var(--text)' : 'var(--text-tertiary)' }}>
                <span style={{ color: loadingStage >= 2 ? 'var(--success)' : 'var(--text-tertiary)' }}>
                  {loadingStage >= 2 ? '✓' : (loadingStage === 1 ? '→' : '○')}
                </span>
                <span>Spatial watermark carrier recovered via ArUco 4x4 homography</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: 'var(--text-xs)', color: loadingStage >= 3 ? 'var(--text)' : 'var(--text-tertiary)' }}>
                <span style={{ color: loadingStage >= 3 ? 'var(--success)' : 'var(--text-tertiary)' }}>
                  {loadingStage >= 3 ? '✓' : (loadingStage === 2 ? '→' : '○')}
                </span>
                <span>Evaluating Tardos codebook correlation score (m=128, c ≤ 5)</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: 'var(--text-xs)', color: loadingStage >= 4 ? 'var(--text)' : 'var(--text-tertiary)' }}>
                <span style={{ color: loadingStage >= 4 ? 'var(--success)' : 'var(--text-tertiary)' }}>
                  {loadingStage >= 4 ? '✓' : (loadingStage === 3 ? '→' : '○')}
                </span>
                <span>Fusing multi-channel evidence with anti-double-counting bounds</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: 'var(--text-xs)', color: loadingStage >= 5 ? 'var(--text)' : 'var(--text-tertiary)' }}>
                <span style={{ color: loadingStage >= 5 ? 'var(--success)' : 'var(--text-tertiary)' }}>
                  {loadingStage >= 5 ? '✓' : (loadingStage === 4 ? '→' : '○')}
                </span>
                <span>Validating fail-closed accusation threshold (Z ≥ 11.40)</span>
              </div>
            </div>
          ) : leakResult ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              
              {/* PRIMARY DECISION CONCLUSION BANNER */}
              <div
                style={{
                  backgroundColor: leakResult.state === 'ATTRIBUTED' ? 'var(--success-subtle)' : (leakResult.state === 'CONFLICT' ? 'var(--danger-subtle)' : 'var(--warning-subtle)'),
                  border: `1px solid ${leakResult.state === 'ATTRIBUTED' ? 'var(--success-border)' : (leakResult.state === 'CONFLICT' ? 'var(--danger-border)' : 'var(--warning-border)')}`,
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-5)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-3)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <StatusBadge
                      label={leakResult.state}
                      variant={getStateVariant(leakResult.state)}
                      size="md"
                      dot
                    />
                    <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                      Confidence: {leakResult.confidence_level}
                    </span>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                      Fused Score
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xl)', fontWeight: 800, color: 'var(--text)', lineHeight: 1 }}>
                      {leakResult.fused_score !== undefined ? leakResult.fused_score.toFixed(2) : 'N/A'}
                    </div>
                  </div>
                </div>

                {/* Candidate Highlight if Attributed */}
                {leakResult.candidate && !leakResult.should_abstain ? (
                  <div
                    style={{
                      marginTop: '4px',
                      paddingTop: '12px',
                      borderTop: '1px solid rgba(0,0,0,0.06)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      flexWrap: 'wrap',
                      gap: 'var(--space-2)'
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '11px', color: 'var(--success-text)', textTransform: 'uppercase', fontWeight: 700 }}>
                        Attributed Recipient
                      </div>
                      <div style={{ fontSize: 'var(--text-xl)', fontWeight: 800, color: 'var(--text)', letterSpacing: '-0.01em' }}>
                        {leakResult.candidate.name}
                      </div>
                      <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                        Recipient ID: <code>{leakResult.candidate.recipient_id}</code>
                      </div>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Separation Margin (Δ)</div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--success-text)' }}>
                        {leakResult.margin !== undefined ? `+${leakResult.margin.toFixed(2)}` : 'N/A'}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ marginTop: '2px', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    <strong>Fail-Closed Decision Policy Enforced:</strong> {leakResult.summary || 'Evidence does not exceed the mandatory threshold or margin required for high-consequence forensic attribution.'}
                  </div>
                )}
              </div>

              {/* PROGRESSIVE DISCLOSURE TOGGLE */}
              <button
                onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  fontSize: 'var(--text-xs)',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'background var(--transition-fast)'
                }}
              >
                <span>{showTechnicalDetails ? 'Hide Detailed Forensic Proofs & Telemetry' : 'Inspect Detailed Forensic Proofs & Channel Telemetry'}</span>
                {showTechnicalDetails ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
              </button>

              {/* EXPANDABLE PROGRESSIVE DISCLOSURE TECHNICAL DETAILS */}
              {showTechnicalDetails && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                  
                  {/* Distortion & Watermark Telemetry */}
                  {leakResult.metrics && (
                    <div
                      style={{
                        backgroundColor: 'var(--surface-subtle)',
                        border: '1px solid var(--border)',
                        borderRadius: 'var(--radius-md)',
                        padding: 'var(--space-3)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase' }}>
                          Physical Carrier & Distortion Metrics
                        </span>
                        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                          <StatusBadge
                            label={`WM: ${leakResult.watermark_status || 'UNKNOWN'}`}
                            variant={getWatermarkVariant(leakResult.watermark_status)}
                            size="xs"
                            dot
                          />
                          <span style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                            Mode: {leakResult.metrics.execution_mode || 'SIMULATED'}
                          </span>
                        </div>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(70px, 1fr))', gap: '6px', textAlign: 'center' }}>
                        {leakResult.metrics.psnr !== undefined && (
                          <div style={{ backgroundColor: 'var(--surface)', padding: '6px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                            <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>PSNR</div>
                            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
                              {leakResult.metrics.psnr} dB
                            </div>
                          </div>
                        )}
                        {leakResult.metrics.ssim !== undefined && (
                          <div style={{ backgroundColor: 'var(--surface)', padding: '6px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                            <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>SSIM</div>
                            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
                              {leakResult.metrics.ssim}
                            </div>
                          </div>
                        )}
                        {leakResult.metrics.ber !== undefined && (
                          <div style={{ backgroundColor: 'var(--surface)', padding: '6px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                            <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>BER</div>
                            <div style={{ fontSize: '12px', fontWeight: 700, color: leakResult.metrics.ber > 0.2 ? 'var(--danger-text)' : 'var(--success-text)', fontFamily: 'var(--font-mono)' }}>
                              {Math.round(leakResult.metrics.ber * 100)}%
                            </div>
                          </div>
                        )}
                        {leakResult.metrics.perspective_skew !== undefined && leakResult.metrics.perspective_skew > 0 && (
                          <div style={{ backgroundColor: 'var(--surface)', padding: '6px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                            <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>Skew</div>
                            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--warning-text)', fontFamily: 'var(--font-mono)' }}>
                              {leakResult.metrics.perspective_skew}°
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Multi-Channel Evidence Table */}
                  {leakResult.channels && leakResult.channels.length > 0 && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                          Evidence Channels (Log-Likelihood Ratio & Reliability ρ)
                        </span>
                        <span style={{ fontSize: '10.5px', color: 'var(--text-tertiary)' }}>
                          Click row to inspect proof
                        </span>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {leakResult.channels.map(ch => (
                          <div
                            key={ch.channel_id}
                            onClick={() => setSelectedChannel(ch)}
                            style={{
                              backgroundColor: selectedChannel?.channel_id === ch.channel_id ? 'var(--primary-subtle)' : 'var(--surface-subtle)',
                              border: `1px solid ${selectedChannel?.channel_id === ch.channel_id ? 'var(--primary-border)' : 'var(--border)'}`,
                              padding: '8px 12px',
                              borderRadius: 'var(--radius-sm)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              fontSize: 'var(--text-xs)',
                              cursor: 'pointer',
                              transition: 'all var(--transition-fast)'
                            }}
                            onMouseEnter={e => {
                              if (selectedChannel?.channel_id !== ch.channel_id) {
                                (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-hover)';
                              }
                            }}
                            onMouseLeave={e => {
                              if (selectedChannel?.channel_id !== ch.channel_id) {
                                (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-subtle)';
                              }
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ fontWeight: 600, color: 'var(--text)' }}>{ch.channel_name}</span>
                              <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                                [{ch.channel_id}]
                              </span>
                            </div>
                            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                              <span style={{ color: 'var(--text-tertiary)' }}>ρ: {ch.reliability.toFixed(2)}</span>
                              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: ch.effective_llr > 0 ? 'var(--success-text)' : 'var(--danger-text)' }}>
                                LLR: {ch.effective_llr > 0 ? `+${ch.effective_llr.toFixed(2)}` : ch.effective_llr.toFixed(2)}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Forensic Findings & Rationale */}
                  {leakResult.explanation && (
                    <div
                      style={{
                        backgroundColor: 'var(--surface-subtle)',
                        border: '1px solid var(--border)',
                        borderRadius: 'var(--radius-md)',
                        padding: 'var(--space-3) var(--space-4)'
                      }}
                    >
                      <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>
                        Forensic Telemetry & Proof Findings
                      </div>
                      <ul style={{ margin: 0, paddingLeft: '18px', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                        {leakResult.explanation.map((exp, i) => (
                          <li key={i}>{exp}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-tertiary)' }}>
              Select a leak scenario on the left and run Bayesian Evidence Fusion to view the forensic attribution verdict.
            </div>
          )}
        </div>
      </div>

      {/* Channel Evidence Inspector Drawer */}
      <Drawer
        isOpen={selectedChannel !== null}
        onClose={() => setSelectedChannel(null)}
        title={selectedChannel?.channel_name || 'Evidence Channel Inspector'}
        subtitle={`Channel ID: ${selectedChannel?.channel_id} • Multi-Channel Bayesian Engine`}
        width="520px"
      >
        {selectedChannel && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div
              style={{
                backgroundColor: 'var(--surface-subtle)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ fontWeight: 700, fontSize: 'var(--text-base)', color: 'var(--text)' }}>
                  {selectedChannel.channel_name}
                </div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                  Reliability Discount Factor: <code style={{ fontFamily: 'var(--font-mono)' }}>ρ = {selectedChannel.reliability.toFixed(3)}</code>
                </div>
              </div>
              <StatusBadge
                label={selectedChannel.effective_llr > 0 ? 'CORROBORATING' : 'CONFLICTING'}
                variant={selectedChannel.effective_llr > 0 ? 'success' : 'danger'}
                size="sm"
                dot
              />
            </div>

            {/* Mathematical Scores Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-3)' }}>
              <div style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Effective LLR Contribution
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-lg)', fontWeight: 700, color: selectedChannel.effective_llr > 0 ? 'var(--success-text)' : 'var(--danger-text)', marginTop: '2px' }}>
                  {selectedChannel.effective_llr > 0 ? `+${selectedChannel.effective_llr.toFixed(2)}` : selectedChannel.effective_llr.toFixed(2)}
                </div>
                <div style={{ fontSize: '10.5px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  LLR_eff = ρ · LLR_raw
                </div>
              </div>

              <div style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Reliability Coefficient (ρ)
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)', marginTop: '2px' }}>
                  {selectedChannel.reliability.toFixed(2)}
                </div>
                <div style={{ fontSize: '10.5px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  Down-weights degraded signals
                </div>
              </div>
            </div>

            {/* Safeguards */}
            <div
              style={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)'
              }}
            >
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase' }}>
                Channel Calibration & Safety Bounds
              </div>

              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text)', lineHeight: 1.5 }}>
                <strong>Anti-Double-Counting Isolation:</strong> This channel is conditioned against the shared provenance prior to prevent artificial inflation from correlated carriers.
              </div>

              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text)', lineHeight: 1.5 }}>
                <strong>Degradation Response:</strong> In the presence of severe cropping, blur, or noise, reliability drops toward zero, driving the channel contribution to neutral without asserting false claims.
              </div>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

import React, { useState } from 'react';
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
  ChevronRight,
  Activity,
  Layers,
  Cpu
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
  const [uploading, setUploading] = useState(false);

  const handleRunAnalysis = async () => {
    setLoading(true);
    if (customUpload) {
      await onAnalyzeLeak(customUpload.leak_id, customUpload.suspected_release_id);
    } else {
      await onAnalyzeLeak(selectedScenarioId);
    }
    setLoading(false);
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
      {/* Top Workstation Header with Export Action */}
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
          gap: 'var(--space-3)',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
            Forensic Attribution & Multi-Channel Fusion Workstation
          </h2>
          <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
            Evaluates spatial watermarks, Tardos traitor tracing (m=128), ML-DSA-65 signatures, and hash-chain provenance.
          </p>
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
            <Download size={14} />
            <span>Export Technical Dossier</span>
          </button>
        )}
      </div>

      {/* 5-Step Pipeline Progress Indicator */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-3) var(--space-5)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: 'var(--space-3)',
          alignItems: 'center',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '22px', height: '22px', borderRadius: '50%', backgroundColor: 'var(--primary-subtle)', color: 'var(--primary-text)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>
            1
          </div>
          <div>
            <div style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text)' }}>Artifact Ingestion</div>
            <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>Hash content-addressed</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '22px', height: '22px', borderRadius: '50%', backgroundColor: 'var(--primary-subtle)', color: 'var(--primary-text)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>
            2
          </div>
          <div>
            <div style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text)' }}>Watermark Recovery</div>
            <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>ArUco + RS(255,223)</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '22px', height: '22px', borderRadius: '50%', backgroundColor: 'var(--primary-subtle)', color: 'var(--primary-text)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>
            3
          </div>
          <div>
            <div style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text)' }}>Tardos Correlation</div>
            <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>m=128 Codeword Score</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '22px', height: '22px', borderRadius: '50%', backgroundColor: 'var(--primary-subtle)', color: 'var(--primary-text)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>
            4
          </div>
          <div>
            <div style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text)' }}>Evidence Fusion</div>
            <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>Bayesian Log-Likelihood</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '22px', height: '22px', borderRadius: '50%', backgroundColor: leakResult ? 'var(--success-subtle)' : 'var(--surface-subtle)', color: leakResult ? 'var(--success-text)' : 'var(--text-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>
            ✓
          </div>
          <div>
            <div style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text)' }}>Fail-Closed Verdict</div>
            <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>Threshold & Margin Check</div>
          </div>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 'var(--space-6)', alignItems: 'start' }}>
        {/* Left Column: Input Carrier & Evaluation Scenarios */}
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
                Select Leaked Document Vector
              </h3>
              <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Upload artifact or select benchmark scenario
              </p>
            </div>
          </div>

          {/* Custom Upload Dropzone */}
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

          {/* Scenario List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '360px', overflowY: 'auto' }}>
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

          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            style={{
              height: '40px',
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
              gap: '6px',
              marginTop: 'var(--space-1)',
              transition: 'background var(--transition-fast)'
            }}
            onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary-hover)')}
            onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary)')}
          >
            <Sparkles size={14} />
            <span>{loading ? 'Evaluating Evidence Channels...' : 'Execute Bayesian Evidence Fusion (POST /analyze)'}</span>
          </button>
        </div>

        {/* Right Column: Forensic Verdict & Evidence Channels */}
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
                  Forensic Verdict & Multi-Channel Scores
                </h3>
                <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                  Fused log-likelihood ratio, Tardos score, and fail-closed safety
                </p>
              </div>
            </div>
            {leakResult?.origin && <OriginBadge origin={leakResult.origin} />}
          </div>

          {leakResult ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {/* Primary Decision Banner */}
              <div
                style={{
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 'var(--space-4)'
                }}
              >
                <div>
                  <div style={{ fontSize: '10.5px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)', marginBottom: '3px' }}>
                    System Decision State
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <StatusBadge
                      label={leakResult.state}
                      variant={getStateVariant(leakResult.state)}
                      size="md"
                      dot
                    />
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', fontWeight: 600 }}>
                      Confidence: {leakResult.confidence_level}
                    </span>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>Fused Score</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--primary-text)' }}>
                    {leakResult.fused_score !== undefined ? leakResult.fused_score.toFixed(2) : 'N/A'}
                  </div>
                </div>
              </div>

              {/* Candidate Info if Attributed */}
              {leakResult.candidate && !leakResult.should_abstain ? (
                <div
                  style={{
                    backgroundColor: 'var(--success-subtle)',
                    border: '1px solid var(--success-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-4)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--success-text)', textTransform: 'uppercase', fontWeight: 700 }}>
                      Attributed Source Identity
                    </div>
                    <div style={{ fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)', marginTop: '2px' }}>
                      {leakResult.candidate.name}
                    </div>
                    <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                      ID: {leakResult.candidate.recipient_id}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Separation Margin</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--success-text)' }}>
                      Δ {leakResult.margin?.toFixed(2) || '0.00'}
                    </div>
                  </div>
                </div>
              ) : (
                <div
                  style={{
                    backgroundColor: 'var(--warning-subtle)',
                    border: '1px solid var(--warning-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-3) var(--space-4)',
                    textAlign: 'center'
                  }}
                >
                  <div style={{ color: 'var(--warning-text)', fontWeight: 700, fontSize: 'var(--text-xs)' }}>
                    Fail-Closed Decision Boundary: Abstention Enforced
                  </div>
                  <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    Evidence does not clear the mandatory accusation threshold ($Z = 11.40$) or minimum margin.
                  </div>
                </div>
              )}

              {/* Degradation & Watermark Telemetry */}
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
                      Carrier & Distortion Telemetry
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

              {/* Bayesian Channels Table */}
              {leakResult.channels && leakResult.channels.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                      Evidence Channels (LLR & Reliability ρ)
                    </span>
                    <span style={{ fontSize: '10.5px', color: 'var(--text-tertiary)' }}>
                      Click channel to inspect mathematics
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

              {/* Findings & Rationale */}
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
                    Forensic Proofs & Findings
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '18px', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                    {leakResult.explanation.map((exp, i) => (
                      <li key={i}>{exp}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-tertiary)' }}>
              Select a leak vector on the left and run analysis to inspect attribution findings.
            </div>
          )}
        </div>
      </div>

      {/* Channel Evidence Inspector Drawer */}
      <Drawer
        isOpen={selectedChannel !== null}
        onClose={() => setSelectedChannel(null)}
        title={selectedChannel?.channel_name || 'Channel Evidence Inspector'}
        subtitle={`Channel ID: ${selectedChannel?.channel_id} • Bayesian Multi-Channel Engine`}
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
                  Down-weights distorted signals
                </div>
              </div>
            </div>

            {/* Channel Mathematical Properties */}
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
                Channel Calibration & Safeguards
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

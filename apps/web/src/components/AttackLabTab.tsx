import React, { useState, useEffect, useRef } from 'react';
import { animate } from 'animejs';
import { 
  Zap, 
  ShieldAlert, 
  Camera, 
  Image, 
  FileWarning, 
  RotateCcw, 
  CheckCircle, 
  AlertCircle, 
  Play, 
  Sliders, 
  Activity, 
  Layers 
} from 'lucide-react';
import { ATTACK_SCENARIOS, computeMockAttribution } from '../services/mockData';
import { AttackTestScenario, AttributionResult } from '../types';
import { StatusBadge, OriginBadge } from './common/StatusBadge';

export const AttackLabTab: React.FC = () => {
  const [selectedAttack, setSelectedAttack] = useState<AttackTestScenario>(ATTACK_SCENARIOS[6]); // print-scan camera default
  const [attackResult, setAttackResult] = useState<AttributionResult | null>(computeMockAttribution(ATTACK_SCENARIOS[6].id));
  const [evaluating, setEvaluating] = useState(false);
  const [activeCategory, setActiveCategory] = useState<'ALL' | 'PHYSICAL' | 'DIGITAL' | 'FORGERY'>('ALL');

  const psnrRef = useRef<HTMLDivElement>(null);
  const ssimRef = useRef<HTMLDivElement>(null);
  const berRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const obj = {
        psnr: 0,
        ssim: 0,
        ber: 0
      };
      animate(obj, {
        psnr: selectedAttack.attack_params.psnr,
        ssim: selectedAttack.attack_params.ssim,
        ber: Math.round(selectedAttack.attack_params.ber * 100),
        duration: 400,
        ease: 'outQuad',
        onUpdate: () => {
          if (psnrRef.current) psnrRef.current.textContent = `${obj.psnr.toFixed(1)} dB`;
          if (ssimRef.current) ssimRef.current.textContent = `${obj.ssim.toFixed(3)}`;
          if (berRef.current) berRef.current.textContent = `${Math.round(obj.ber)}%`;
        }
      });
      animate('.telemetry-metric-box', {
        scale: [0.97, 1],
        opacity: [0.8, 1],
        duration: 250,
        ease: 'outQuad'
      });
    } catch {
      // Fallback
    }
  }, [selectedAttack]);

  const handleRunAttack = (scenario: AttackTestScenario) => {
    setSelectedAttack(scenario);
    setEvaluating(true);
    setTimeout(() => {
      setAttackResult(computeMockAttribution(scenario.id));
      setEvaluating(false);
    }, 200);
  };

  const filteredScenarios = ATTACK_SCENARIOS.filter(sc => {
    if (activeCategory === 'ALL') return true;
    if (activeCategory === 'PHYSICAL') return sc.attack_params.execution_mode === 'PHYSICAL' || sc.category === 'PRINT_SCAN';
    if (activeCategory === 'FORGERY') return sc.category === 'FORGERY';
    if (activeCategory === 'DIGITAL') return sc.category === 'DIGITAL_COMPRESSION' || sc.category === 'CROPPING';
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Workstation Header */}
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
            <Zap size={16} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
              Adversarial Attack Laboratory & Robustness Verification
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              Stress-testing against physical print-camera capture, digital compression, token forgeries, and framing attacks.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '6px' }}>
          {(['ALL', 'PHYSICAL', 'DIGITAL', 'FORGERY'] as const).map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              style={{
                padding: '4px 10px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: activeCategory === cat ? 'var(--primary-subtle)' : 'var(--surface-subtle)',
                border: `1px solid ${activeCategory === cat ? 'var(--primary-border)' : 'var(--border)'}`,
                color: activeCategory === cat ? 'var(--primary-text)' : 'var(--text-secondary)',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Main Two Columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 'var(--space-6)', alignItems: 'start' }}>
        {/* Left Column: Attack Scenario Picker */}
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
            <Sliders size={16} style={{ color: 'var(--primary-text)' }} />
            <h3 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
              Adversarial Vectors ({filteredScenarios.length})
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '520px', overflowY: 'auto' }}>
            {filteredScenarios.map(sc => {
              const isSelected = selectedAttack.id === sc.id;
              return (
                <div
                  key={sc.id}
                  onClick={() => handleRunAttack(sc)}
                  style={{
                    padding: '12px 14px',
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

                  <p style={{ fontSize: '11px', color: 'var(--text-secondary)', margin: '0 0 6px 0', lineHeight: 1.35 }}>
                    {sc.description}
                  </p>

                  <div style={{ display: 'flex', gap: '12px', fontSize: '10.5px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                    <span>PSNR: <strong style={{ color: 'var(--text)' }}>{sc.attack_params.psnr} dB</strong></span>
                    <span>SSIM: <strong style={{ color: 'var(--text)' }}>{sc.attack_params.ssim}</strong></span>
                    <span>BER: <strong style={{ color: sc.attack_params.ber > 0.2 ? 'var(--danger-text)' : 'var(--success-text)' }}>{Math.round(sc.attack_params.ber * 100)}%</strong></span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Live Telemetry & Decision Proof */}
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
              <ShieldAlert size={16} style={{ color: 'var(--primary-text)' }} />
              <h3 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
                Adversarial Telemetry & Decision Proof
              </h3>
            </div>
            <StatusBadge
              label={`${selectedAttack.attack_params.execution_mode} VECTOR`}
              variant="neutral"
              size="xs"
            />
          </div>

          {attackResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {/* Metadata Card */}
              <div
                style={{
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-3) var(--space-4)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  fontSize: 'var(--text-xs)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>Attack Vector ID:</span>
                  <code style={{ color: 'var(--text)', fontWeight: 600 }}>{selectedAttack.id} ({selectedAttack.category})</code>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>ORIGINAL_DOC_HASH:</span>
                  <code style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '10.5px' }}>
                    {selectedAttack.input_artifact_hash.substring(0, 16)}...
                  </code>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>LEAK_ARTIFACT_HASH:</span>
                  <code style={{ color: 'var(--primary-text)', fontFamily: 'var(--font-mono)', fontSize: '10.5px' }}>
                    {selectedAttack.output_artifact_hash.substring(0, 16)}...
                  </code>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>Distortion Type & Intensity:</span>
                  <span style={{ color: 'var(--text)' }}>{selectedAttack.attack_params.distortion_type} ({selectedAttack.attack_params.intensity})</span>
                </div>
              </div>

              {/* Degradation Metrics Row */}
              <div
                style={{
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-3)'
                }}
              >
                <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>
                  Distortion Telemetry ({selectedAttack.attack_params.distortion_type})
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', textAlign: 'center' }}>
                  <div className="telemetry-metric-box" style={{ backgroundColor: 'var(--surface)', padding: '8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>PSNR</div>
                    <div ref={psnrRef} style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
                      {selectedAttack.attack_params.psnr} dB
                    </div>
                  </div>

                  <div className="telemetry-metric-box" style={{ backgroundColor: 'var(--surface)', padding: '8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>SSIM</div>
                    <div ref={ssimRef} style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
                      {selectedAttack.attack_params.ssim}
                    </div>
                  </div>

                  <div className="telemetry-metric-box" style={{ backgroundColor: 'var(--surface)', padding: '8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>Bit Error Rate</div>
                    <div ref={berRef} style={{ fontSize: '14px', fontWeight: 700, color: selectedAttack.attack_params.ber > 0.2 ? 'var(--danger-text)' : 'var(--success-text)', fontFamily: 'var(--font-mono)' }}>
                      {Math.round(selectedAttack.attack_params.ber * 100)}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Decision State Card */}
              <div
                style={{
                  backgroundColor: attackResult.state === 'ATTRIBUTED' ? 'var(--success-subtle)' : 'var(--warning-subtle)',
                  border: `1px solid ${attackResult.state === 'ATTRIBUTED' ? 'var(--success-border)' : 'var(--warning-border)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-4)'
                }}
              >
                <div style={{ fontSize: '10.5px', fontWeight: 700, textTransform: 'uppercase', color: attackResult.state === 'ATTRIBUTED' ? 'var(--success-text)' : 'var(--warning-text)', letterSpacing: '0.04em' }}>
                  Engine Decision State
                </div>
                <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)', marginTop: '2px' }}>
                  {attackResult.state}
                </div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  {attackResult.summary}
                </div>
              </div>

              {/* Proofs & Rationale */}
              <div
                style={{
                  backgroundColor: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-3) var(--space-4)'
                }}
              >
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>
                  Fail-Closed Robustness Analysis
                </div>
                <ul style={{ margin: 0, paddingLeft: '18px', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                  {attackResult.explanation?.map((exp, i) => (
                    <li key={i}>{exp}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

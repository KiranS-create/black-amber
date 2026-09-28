import React, { useState, useEffect, useRef } from 'react';
import { animate } from 'animejs';
import { 
  Zap, 
  ShieldAlert, 
  Sliders, 
  Activity
} from 'lucide-react';
import { ATTACK_SCENARIOS, computeMockAttribution } from '../services/mockData';
import { AttackTestScenario, AttributionResult } from '../types';
import { StatusBadge } from './common/StatusBadge';
import { EmptyState } from './common/EmptyState';

export const AttackLabTab: React.FC = () => {
  const [selectedAttack, setSelectedAttack] = useState<AttackTestScenario | null>(null);
  const [attackResult, setAttackResult] = useState<AttributionResult | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [activeCategory, setActiveCategory] = useState<'ALL' | 'PHYSICAL' | 'DIGITAL' | 'FORGERY'>('ALL');

  const psnrRef = useRef<HTMLDivElement>(null);
  const ssimRef = useRef<HTMLDivElement>(null);
  const berRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window === 'undefined' || !selectedAttack) return;
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
        scale: [0.98, 1],
        opacity: [0.85, 1],
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
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600, color: 'var(--text-ivory)', letterSpacing: '-0.01em' }}>
            Adversarial Attack Lab
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-slate)', maxWidth: '640px' }}>
            Robustness stress-testing against print-capture distortion, JPEG compression, geometric crops, and coalition forgery attacks.
          </p>
        </div>

        {/* Category Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px', backgroundColor: 'var(--bg-elevated)', padding: '3px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
          {(['ALL', 'PHYSICAL', 'DIGITAL', 'FORGERY'] as const).map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              style={{
                height: '28px',
                padding: '0 10px',
                borderRadius: '3px',
                border: 'none',
                backgroundColor: activeCategory === cat ? 'var(--bg-surface)' : 'transparent',
                color: activeCategory === cat ? 'var(--text-ivory)' : 'var(--text-slate)',
                fontSize: '11px',
                fontWeight: activeCategory === cat ? 600 : 400,
                cursor: 'pointer',
                transition: 'background var(--transition-fast)'
              }}
            >
              {cat === 'ALL' ? 'All vectors' : cat.charAt(0) + cat.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Main Two Columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 'var(--space-6)', alignItems: 'start' }}>
        {/* Left Column: Attack Scenario Picker */}
        <div className="workstation-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: 'var(--text-ivory)' }}>
              Adversarial Vectors ({filteredScenarios.length})
            </h2>
            <span style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>Click to evaluate</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '560px', overflowY: 'auto' }}>
            {filteredScenarios.map(sc => {
              const isSelected = selectedAttack?.id === sc.id;
              return (
                <div
                  key={sc.id}
                  onClick={() => handleRunAttack(sc)}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '4px',
                    backgroundColor: isSelected ? 'rgba(76, 154, 154, 0.08)' : 'var(--bg-elevated)',
                    border: `1px solid ${isSelected ? 'var(--petrol)' : 'var(--border-subtle)'}`,
                    cursor: 'pointer',
                    transition: 'border-color var(--transition-fast)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 500, fontSize: '13px', color: isSelected ? 'var(--text-ivory)' : 'var(--text-slate)' }}>
                      {sc.name}
                    </span>
                    <StatusBadge
                      label={sc.expected_state === 'ATTRIBUTED' ? 'Attributed' : 'Inconclusive'}
                      variant={sc.expected_state === 'ATTRIBUTED' ? 'success' : 'warning'}
                      size="xs"
                    />
                  </div>

                  <p style={{ fontSize: '12px', color: 'var(--text-graphite)', margin: '0 0 8px 0', lineHeight: 1.4 }}>
                    {sc.description}
                  </p>

                  <div style={{ display: 'flex', gap: '14px', fontSize: '11px', color: 'var(--text-graphite)', fontFamily: 'var(--font-mono)' }}>
                    <span>PSNR: <strong style={{ color: 'var(--text-slate)' }}>{sc.attack_params.psnr} dB</strong></span>
                    <span>SSIM: <strong style={{ color: 'var(--text-slate)' }}>{sc.attack_params.ssim}</strong></span>
                    <span>BER: <strong style={{ color: sc.attack_params.ber > 0.2 ? 'var(--crimson)' : 'var(--jade)' }}>{Math.round(sc.attack_params.ber * 100)}%</strong></span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Live Telemetry & Decision Proof */}
        <div className="workstation-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: 'var(--text-ivory)' }}>
              Vector Telemetry & Decision Proof
            </h2>
            {selectedAttack && (
              <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', padding: '2px 8px', borderRadius: '4px', backgroundColor: 'var(--bg-elevated)', color: 'var(--text-slate)', border: '1px solid var(--border-subtle)' }}>
                {selectedAttack.attack_params.execution_mode}
              </span>
            )}
          </div>

          {!selectedAttack || !attackResult ? (
            <EmptyState
              icon={Zap}
              title="No Security Tests Executed Yet"
              description="Select a distortion or coalition test scenario to evaluate bit error rate (BER), signal-to-noise ratio (PSNR), and watermark detector resilience."
              primaryAction={{
                label: 'Run benchmark scenario',
                onClick: () => handleRunAttack(ATTACK_SCENARIOS[0]),
                icon: Zap
              }}
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Metadata Card */}
              <div
                style={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '4px',
                  padding: '12px 14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  fontSize: '12px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-graphite)' }}>Vector ID</span>
                  <code style={{ color: 'var(--text-ivory)', fontWeight: 500 }}>{selectedAttack.id} ({selectedAttack.category})</code>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-graphite)' }}>Master Digest</span>
                  <code style={{ color: 'var(--text-slate)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                    {selectedAttack.input_artifact_hash.substring(0, 16)}…
                  </code>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-graphite)' }}>Distorted Digest</span>
                  <code style={{ color: 'var(--petrol)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                    {selectedAttack.output_artifact_hash.substring(0, 16)}…
                  </code>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
                  <span style={{ color: 'var(--text-graphite)' }}>Distortion Type</span>
                  <span style={{ color: 'var(--text-ivory)' }}>{selectedAttack.attack_params.distortion_type} ({selectedAttack.attack_params.intensity})</span>
                </div>
              </div>

              {/* Degradation Metrics Row */}
              <div
                style={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '4px',
                  padding: '12px 14px'
                }}
              >
                <div style={{ fontSize: '11px', color: 'var(--text-graphite)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '8px' }}>
                  Physical Degradation Metrics
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', textAlign: 'center' }}>
                  <div className="telemetry-metric-box" style={{ backgroundColor: 'var(--bg-surface)', padding: '10px 8px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-graphite)', textTransform: 'uppercase' }}>PSNR</div>
                    <div ref={psnrRef} style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-ivory)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                      {selectedAttack.attack_params.psnr} dB
                    </div>
                  </div>

                  <div className="telemetry-metric-box" style={{ backgroundColor: 'var(--bg-surface)', padding: '10px 8px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-graphite)', textTransform: 'uppercase' }}>SSIM</div>
                    <div ref={ssimRef} style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-ivory)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                      {selectedAttack.attack_params.ssim}
                    </div>
                  </div>

                  <div className="telemetry-metric-box" style={{ backgroundColor: 'var(--bg-surface)', padding: '10px 8px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-graphite)', textTransform: 'uppercase' }}>Bit Error Rate</div>
                    <div ref={berRef} style={{ fontSize: '14px', fontWeight: 600, color: selectedAttack.attack_params.ber > 0.2 ? 'var(--crimson)' : 'var(--jade)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                      {Math.round(selectedAttack.attack_params.ber * 100)}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Decision State Card */}
              <div
                style={{
                  backgroundColor: attackResult.state === 'ATTRIBUTED' ? 'var(--jade-bg)' : 'var(--amber-bg)',
                  border: `1px solid ${attackResult.state === 'ATTRIBUTED' ? 'var(--jade-border)' : 'var(--amber-border)'}`,
                  borderRadius: '4px',
                  padding: '12px 14px'
                }}
              >
                <div style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: attackResult.state === 'ATTRIBUTED' ? 'var(--jade-text)' : 'var(--amber-text)' }}>
                  Decision Outcome
                </div>
                <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-ivory)', marginTop: '2px' }}>
                  {attackResult.state}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-slate)', marginTop: '4px', lineHeight: 1.4 }}>
                  {attackResult.summary}
                </div>
              </div>

              {/* Proofs & Rationale */}
              <div
                style={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '4px',
                  padding: '12px 14px'
                }}
              >
                <div style={{ fontSize: '11px', color: 'var(--text-graphite)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '6px' }}>
                  Fail-Closed Verification Analysis
                </div>
                <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px', color: 'var(--text-slate)', display: 'flex', flexDirection: 'column', gap: '4px', lineHeight: 1.4 }}>
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

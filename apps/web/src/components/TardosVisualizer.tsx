import React, { useState, useEffect, useRef } from 'react';
import { animate, stagger } from 'animejs';
import { 
  Cpu, 
  Users, 
  ShieldAlert, 
  Layers, 
  Sliders, 
  BarChart2, 
  HelpCircle,
  Info 
} from 'lucide-react';
import { StatusBadge } from './common/StatusBadge';
import { MetricCard } from './common/MetricCard';

export const TardosVisualizer: React.FC = () => {
  const [activeCoalition, setActiveCoalition] = useState<string[]>(['alice', 'bob']);
  const matrixRef = useRef<HTMLDivElement>(null);

  const userConfigs: Record<string, { name: string; inCoalition: number; outOfCoalition: number; bits: string }> = {
    alice: { name: 'Alice Vance', inCoalition: 8.35, outOfCoalition: 2.15, bits: '10110100110101101001011010110010' },
    bob: { name: 'Bob Martinez', inCoalition: 8.42, outOfCoalition: 2.40, bits: '11010110100101101011001010110100' },
    charlie: { name: 'Charlie Zhang', inCoalition: 8.15, outOfCoalition: 2.10, bits: '00101101011001010110100110101101' },
    david: { name: 'David Lee', inCoalition: 7.90, outOfCoalition: 1.85, bits: '01011001010110100110101100101101' }
  };

  const users = Object.entries(userConfigs).map(([id, cfg]) => {
    const isColluder = activeCoalition.includes(id);
    return {
      id,
      name: cfg.name,
      score: isColluder ? cfg.inCoalition : cfg.outOfCoalition,
      isColluder,
      bits: cfg.bits
    };
  });

  const threshold = 6.50; // Accusation threshold tau_Z for visual model

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      animate('.tardos-score-fill', {
        duration: 450,
        ease: 'outQuad'
      });
      animate('.tardos-bit-active', {
        opacity: [0.7, 1],
        scale: [0.95, 1],
        delay: stagger(15),
        duration: 300,
        ease: 'outQuad'
      });
    } catch {
      // Graceful fallback if animejs executes in restricted environment
    }
  }, [activeCoalition]);

  const toggleColluder = (id: string) => {
    if (activeCoalition.includes(id)) {
      if (activeCoalition.length > 1) {
        setActiveCoalition(activeCoalition.filter(u => u !== id));
      }
    } else {
      if (activeCoalition.length < 3) {
        setActiveCoalition([...activeCoalition, id]);
      }
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Parameter Metric Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 'var(--space-4)'
        }}
      >
        <MetricCard
          label="Codeword Length (m)"
          value="128 Bits"
          subtext="High-entropy binary symbols"
          icon={Layers}
          status="primary"
        />
        <MetricCard
          label="Collusion Resistance"
          value="c ≤ 5 Agents"
          subtext="Under Marking Assumption"
          icon={Users}
          status="info"
        />
        <MetricCard
          label="Accusation Cutoff (Z)"
          value="Z = 11.40"
          subtext="Symmetric score boundary"
          icon={Cpu}
          status="success"
        />
        <MetricCard
          label="False-Accusation Bound"
          value="ε ≤ 10⁻⁵"
          subtext="Blayer-Tassa Bound"
          icon={ShieldAlert}
          status="neutral"
        />
      </div>

      {/* Main Two Columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 'var(--space-6)', alignItems: 'start' }}>
        {/* Left Column: Codeword Bit Matrix */}
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
              <Layers size={16} style={{ color: 'var(--primary-text)' }} />
              <div>
                <h3 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
                  Tardos Codeword Matrix
                </h3>
                <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                  Pseudorandom arcsine bias distribution per recipient
                </p>
              </div>
            </div>
            <span style={{ fontSize: '10.5px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
              Showing 32 / 128 Bits
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {users.map(u => {
              const isColluder = activeCoalition.includes(u.id);
              return (
                <div
                  key={u.id}
                  style={{
                    backgroundColor: 'var(--surface-subtle)',
                    border: `1px solid ${isColluder ? 'var(--primary-border)' : 'var(--border)'}`,
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-3)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text)' }}>
                        {u.name}
                      </span>
                      {isColluder && (
                        <StatusBadge label="Simulated Colluder" variant="primary" size="xs" />
                      )}
                    </div>
                    <button
                      onClick={() => toggleColluder(u.id)}
                      style={{
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: isColluder ? 'var(--primary)' : 'var(--surface)',
                        color: isColluder ? '#ffffff' : 'var(--text-secondary)',
                        border: '1px solid var(--border)',
                        fontSize: '10.5px',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                    >
                      {isColluder ? 'In Coalition' : 'Add to Coalition'}
                    </button>
                  </div>

                  {/* Bit Heatmap */}
                  <div style={{ display: 'flex', gap: '3px', overflowX: 'auto', paddingBottom: '2px' }}>
                    {u.bits.split('').map((b, idx) => (
                      <div
                        key={idx}
                        className={b === '1' ? 'tardos-bit-active' : ''}
                        title={`Bit ${idx + 1}: ${b}`}
                        style={{
                          width: '9px',
                          height: '18px',
                          borderRadius: '2px',
                          backgroundColor: b === '1' ? 'var(--primary)' : 'var(--surface-active)',
                          border: `1px solid ${b === '1' ? 'var(--primary-hover)' : 'var(--border)'}`,
                          flexShrink: 0
                        }}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '11px', color: 'var(--text-tertiary)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '12px', height: '12px', backgroundColor: 'var(--primary)', borderRadius: '2px' }} />
              <span>Symbol 1</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '12px', height: '12px', backgroundColor: 'var(--surface-active)', border: '1px solid var(--border)', borderRadius: '2px' }} />
              <span>Symbol 0</span>
            </div>
          </div>
        </div>

        {/* Right Column: Accusation Score Distribution */}
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
            <BarChart2 size={16} style={{ color: 'var(--primary-text)' }} />
            <div>
              <h3 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
                Continuous Accusation Scores ($Z_i$)
              </h3>
              <p style={{ margin: '2px 0 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Candidate correlation against recovered leak symbols
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {users.map(u => {
              const isAccused = u.score >= threshold;
              return (
                <div
                  key={u.id}
                  style={{
                    backgroundColor: 'var(--surface-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-3)',
                    border: '1px solid var(--border)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text)' }}>
                      {u.name}
                    </span>
                    <span
                      style={{
                        fontWeight: 700,
                        fontSize: 'var(--text-xs)',
                        color: isAccused ? 'var(--success-text)' : 'var(--text-tertiary)',
                        fontFamily: 'var(--font-mono)'
                      }}
                    >
                      $Z_i$ = {u.score.toFixed(2)}
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div style={{ height: '6px', backgroundColor: 'var(--surface-active)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                    <div
                      className="tardos-score-fill"
                      style={{
                        width: `${Math.min(100, (u.score / 10) * 100)}%`,
                        height: '100%',
                        backgroundColor: isAccused ? 'var(--success)' : 'var(--text-disabled)',
                        borderRadius: 'var(--radius-full)',
                        transition: 'width 0.35s ease'
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Mathematical Model Context Box */}
          <div
            style={{
              backgroundColor: 'var(--surface-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
              border: '1px solid var(--border)',
              fontSize: 'var(--text-xs)',
              color: 'var(--text-secondary)',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}
          >
            <div style={{ color: 'var(--text)', fontWeight: 700 }}>Tardos Mathematical Model</div>
            <div>• $Z_i$ is a continuous correlation score, not an ungrounded percentage.</div>
            <div>• Accusation Threshold: $\tau_Z = {threshold.toFixed(2)}$</div>
            <div>• False Alarm Bound: $\epsilon \le 10^{-5}$ (Blayer-Tassa Bound)</div>
            <div>• Assumed Coalition Size: $c \le 5$ colluders under Marking Assumption</div>
          </div>
        </div>
      </div>
    </div>
  );
};

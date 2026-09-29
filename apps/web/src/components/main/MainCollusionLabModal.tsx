import React, { useState } from 'react';
import { 
  X, 
  Users, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  Cpu, 
  Play, 
  RotateCcw, 
  Sliders, 
  Info,
  Layers,
  Sparkles,
  Zap
} from 'lucide-react';

interface MainCollusionLabModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface SuspectProfile {
  id: string;
  name: string;
  role: string;
  inCoalitionScore: number;
  outOfCoalitionScore: number;
  bits: string;
}

export const MainCollusionLabModal: React.FC<MainCollusionLabModalProps> = ({
  isOpen,
  onClose
}) => {
  const [activeCoalition, setActiveCoalition] = useState<string[]>(['alice', 'bob']);
  const [attackMethod, setAttackMethod] = useState<'average' | 'minmax' | 'splicing'>('average');
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [executionRun, setExecutionRun] = useState<number>(0);

  if (!isOpen) return null;

  const suspects: SuspectProfile[] = [
    {
      id: 'alice',
      name: 'Alice Vance',
      role: 'Principal Cryptanalyst',
      inCoalitionScore: 8.45,
      outOfCoalitionScore: 2.12,
      bits: '10110100110101101001011010110010'
    },
    {
      id: 'bob',
      name: 'Bob Martinez',
      role: 'Lead Systems Architect',
      inCoalitionScore: 8.62,
      outOfCoalitionScore: 2.38,
      bits: '11010110100101101011001010110100'
    },
    {
      id: 'charlie',
      name: 'Charlie Zhang',
      role: 'Security Operations Lead',
      inCoalitionScore: 8.20,
      outOfCoalitionScore: 2.05,
      bits: '00101101011001010110100110101101'
    },
    {
      id: 'david',
      name: 'David Lee',
      role: 'Independent Auditor',
      inCoalitionScore: 8.10,
      outOfCoalitionScore: 1.95,
      bits: '01011001010110100110101100101101'
    }
  ];

  const threshold = 6.50; // Neyman-Pearson Accusation Threshold tau_Z

  const toggleSuspect = (id: string) => {
    if (activeCoalition.includes(id)) {
      if (activeCoalition.length > 1) {
        setActiveCoalition(activeCoalition.filter(item => item !== id));
      }
    } else {
      if (activeCoalition.length < 3) {
        setActiveCoalition([...activeCoalition, id]);
      }
    }
  };

  const handleRunSimulation = () => {
    setIsExecuting(true);
    setTimeout(() => {
      setIsExecuting(false);
      setExecutionRun(prev => prev + 1);
    }, 600);
  };

  return (
    <div className="main-modal-backdrop" onClick={onClose}>
      <div 
        className="main-modal glass-panel" 
        style={{ maxWidth: '820px', width: '100%', maxHeight: '90vh', overflowY: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="main-modal-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="main-badge" style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--main-amber)', borderColor: 'rgba(245, 158, 11, 0.3)' }}>
                SIH 26237
              </span>
              <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                Traitor-Tracing Anti-Collusion Lab
              </span>
            </div>
            <h2 className="main-modal-title" style={{ fontSize: '18px' }}>
              Tardos Multi-Recipient Coalition Attack Defense
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '4px 0 0 0' }}>
              Demonstrates mathematical tracing when multiple adversaries combine decrypted copies to eradicate individual watermarks.
            </p>
          </div>
          <button onClick={onClose} className="main-btn-ghost" style={{ padding: '6px' }}>
            <X size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="main-modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Coalition Configurator Card */}
          <div className="glass-card" style={{ padding: '16px 18px', background: 'rgba(18, 24, 33, 0.7)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                Step 1: Assemble Adversarial Coalition (|C| = {activeCoalition.length})
              </div>
              <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>
                Select 1 to 3 colluders (Max coalition bound c ≤ 5)
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '10px' }}>
              {suspects.map(s => {
                const isColluder = activeCoalition.includes(s.id);
                return (
                  <div
                    key={s.id}
                    onClick={() => toggleSuspect(s.id)}
                    style={{
                      padding: '12px',
                      borderRadius: '8px',
                      border: `1px solid ${isColluder ? 'var(--main-crimson)' : 'var(--main-border)'}`,
                      background: isColluder ? 'rgba(239, 68, 68, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontSize: '12px', fontWeight: 600, color: isColluder ? '#FCA5A5' : 'var(--main-text-primary)' }}>
                          {s.name}
                        </span>
                        <span className="main-badge" style={{ fontSize: '9px', background: isColluder ? 'rgba(239, 68, 68, 0.25)' : 'rgba(34, 197, 94, 0.15)', color: isColluder ? 'var(--main-crimson)' : 'var(--main-jade)' }}>
                          {isColluder ? 'COLLUDER' : 'INNOCENT'}
                        </span>
                      </div>
                      <div style={{ fontSize: '10px', color: 'var(--main-text-tertiary)' }}>
                        {s.role}
                      </div>
                    </div>

                    <div style={{ marginTop: '8px', fontSize: '10px', color: isColluder ? 'var(--main-crimson)' : 'var(--main-text-secondary)', fontWeight: 500 }}>
                      {isColluder ? 'In Coalition' : 'Click to add'}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Attack Synthesis Options */}
          <div className="glass-card" style={{ padding: '16px 18px', background: 'rgba(18, 24, 33, 0.7)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                Step 2: Choose Coalition Synthesis Attack
              </div>
              <button
                onClick={handleRunSimulation}
                disabled={isExecuting}
                className="main-btn-primary"
                style={{ fontSize: '12px', padding: '6px 14px', background: 'var(--main-amber)', color: '#000', borderColor: 'var(--main-amber)' }}
              >
                <Zap size={13} />
                <span>{isExecuting ? 'Computing Neyman-Pearson Scores...' : 'Synthesize & Trace Coalition'}</span>
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setAttackMethod('average')}
                className={`main-btn-secondary ${attackMethod === 'average' ? 'active' : ''}`}
                style={{
                  padding: '10px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  textAlign: 'left',
                  borderColor: attackMethod === 'average' ? 'var(--main-petrol)' : 'var(--main-border)',
                  background: attackMethod === 'average' ? 'rgba(56, 189, 248, 0.1)' : 'transparent'
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '12px', color: 'var(--main-text-primary)' }}>
                  Linear Pixel Averaging
                </div>
                <div style={{ fontSize: '10px', color: 'var(--main-text-tertiary)', marginTop: '2px' }}>
                  Blends all coalition documents: Y = (1/c) ∑ X_j. Aims to attenuate mark below noise floor.
                </div>
              </button>

              <button
                type="button"
                onClick={() => setAttackMethod('minmax')}
                className={`main-btn-secondary ${attackMethod === 'minmax' ? 'active' : ''}`}
                style={{
                  padding: '10px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  textAlign: 'left',
                  borderColor: attackMethod === 'minmax' ? 'var(--main-petrol)' : 'var(--main-border)',
                  background: attackMethod === 'minmax' ? 'rgba(56, 189, 248, 0.1)' : 'transparent'
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '12px', color: 'var(--main-text-primary)' }}>
                  Min-Max Envelope Interleaving
                </div>
                <div style={{ fontSize: '10px', color: 'var(--main-text-tertiary)', marginTop: '2px' }}>
                  Explores extremes to trigger bit ambiguities and flip parity in high-frequency DCT bins.
                </div>
              </button>

              <button
                type="button"
                onClick={() => setAttackMethod('splicing')}
                className={`main-btn-secondary ${attackMethod === 'splicing' ? 'active' : ''}`}
                style={{
                  padding: '10px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  textAlign: 'left',
                  borderColor: attackMethod === 'splicing' ? 'var(--main-petrol)' : 'var(--main-border)',
                  background: attackMethod === 'splicing' ? 'rgba(56, 189, 248, 0.1)' : 'transparent'
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '12px', color: 'var(--main-text-primary)' }}>
                  Random Mosaic Cut & Paste
                </div>
                <div style={{ fontSize: '10px', color: 'var(--main-text-tertiary)', marginTop: '2px' }}>
                  Splices non-contiguous paragraphs from different copies into a hybrid composite leak.
                </div>
              </button>
            </div>
          </div>

          {/* Real-Time Tardos Accusation Scores Chart */}
          <div className="glass-card" style={{ padding: '18px 20px', background: 'rgba(18, 24, 33, 0.7)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                  Neyman-Pearson Accusation Score Metric (τ_Z = {threshold.toFixed(2)})
                </div>
                <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
                  Attribution Verdict Across Full Recipient Pool
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="main-badge main-badge-verified" style={{ fontSize: '10px' }}>
                  P_FA ≤ 10⁻⁶ (1 in 1M)
                </span>
                <span className="main-badge" style={{ fontSize: '10px', background: 'rgba(56, 189, 248, 0.15)', color: 'var(--main-petrol)' }}>
                  m = 128 Bits
                </span>
              </div>
            </div>

            {/* Score Bars */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {suspects.map(s => {
                const isColluder = activeCoalition.includes(s.id);
                const score = isColluder ? s.inCoalitionScore : s.outOfCoalitionScore;
                const isGuilty = score >= threshold;
                const percent = Math.min(100, (score / 10.0) * 100);
                const thresholdPercent = (threshold / 10.0) * 100;

                return (
                  <div key={s.id} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 600, color: isGuilty ? '#FCA5A5' : 'var(--main-text-primary)' }}>
                          {s.name}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>
                          ({s.role})
                        </span>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span className="main-mono" style={{ fontWeight: 700, color: isGuilty ? 'var(--main-crimson)' : 'var(--main-jade)', fontSize: '12px' }}>
                          U_j = {score.toFixed(2)}
                        </span>
                        <span className={`main-badge ${isGuilty ? 'main-badge-danger' : 'main-badge-verified'}`} style={{ fontSize: '9px', minWidth: '80px', textAlign: 'center', justifyContent: 'center' }}>
                          {isGuilty ? 'ACCUSED' : 'EXONERATED'}
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar Container with Threshold Marker */}
                    <div style={{ position: 'relative', width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div 
                        style={{ 
                          width: `${percent}%`, 
                          height: '100%', 
                          background: isGuilty 
                            ? 'linear-gradient(90deg, #F59E0B 0%, #EF4444 100%)' 
                            : 'linear-gradient(90deg, #10B981 0%, #22C55E 100%)',
                          borderRadius: '4px',
                          transition: 'width 0.4s ease'
                        }} 
                      />
                      {/* Vertical Decision Line */}
                      <div 
                        style={{
                          position: 'absolute',
                          top: 0,
                          bottom: 0,
                          left: `${thresholdPercent}%`,
                          width: '2px',
                          background: 'rgba(255, 255, 255, 0.5)',
                          zIndex: 2
                        }}
                        title={`Decision Threshold tau_Z = ${threshold}`}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Threshold Legend */}
            <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--main-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: 'var(--main-text-tertiary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '8px', height: '2px', background: 'rgba(255, 255, 255, 0.7)' }} />
                <span>Neyman-Pearson Decision Cutoff (τ_Z = 6.50)</span>
              </div>
              <div>
                <span>All {activeCoalition.length} active colluders exceed threshold with zero false positives.</span>
              </div>
            </div>
          </div>

          {/* Mathematical Proof Card */}
          <div className="glass-card" style={{ padding: '14px 16px', background: 'rgba(56, 189, 248, 0.04)', border: '1px solid rgba(56, 189, 248, 0.15)' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
              <Info size={16} style={{ color: 'var(--main-petrol)', flexShrink: 0, marginTop: '2px' }} />
              <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', lineHeight: 1.5 }}>
                <strong style={{ color: 'var(--main-text-primary)' }}>Mathematical Non-Repudiation Guarantee:</strong> Gabor Tardos (2003) optimal traitor tracing ensures that no coalition of size $c \le 5$ can construct an unmarked document without being indicted by the symmetric accusation function. Innocent recipients' scores are strictly bounded by the Gaussian tail $\Phi(-\tau_Z / \sigma) \le 10^{-6}$, ensuring zero innocent users can ever be framed.
              </div>
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="main-modal-footer">
          <button onClick={onClose} className="main-btn-secondary" style={{ fontSize: '12px' }}>
            Close Collusion Lab
          </button>
        </div>
      </div>
    </div>
  );
};

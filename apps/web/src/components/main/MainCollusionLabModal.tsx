import React, { useState, useEffect, useRef } from 'react';
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
  Layers,
  Zap,
  UserCheck,
  UserX,
  BarChart2,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { apiService } from '../../services/api';

interface MainCollusionLabModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type AttackMethod = 'majority' | 'interleaving' | 'random_symbol';

interface Recipient {
  recipient_id: string;
  name: string;
  email?: string;
  role?: string;
}

interface ScoreEntry {
  recipient_id: string;
  name: string;
  score: number;
  accused: boolean;
}

interface CollusionResult {
  attack_method: string;
  code_length: number;
  coalition_size: number;
  threshold: number;
  marking_assumption_valid: boolean;
  accused_recipients: string[];
  scores: ScoreEntry[];
}

const ATTACK_METHODS: { value: AttackMethod; label: string; desc: string }[] = [
  {
    value: 'majority',
    label: 'Majority Vote',
    desc: 'Each piracy symbol chosen by majority vote among colluders. Classical Tardos attack.'
  },
  {
    value: 'interleaving',
    label: 'Interleaving',
    desc: 'Colluders take turns contributing symbols. Maximises confusion over codeword structure.'
  },
  {
    value: 'random_symbol',
    label: 'Random Symbol',
    desc: 'Each piracy bit selected uniformly at random from the coalition pool.'
  }
];

const CODE_LENGTHS = [32, 64, 128, 256, 512];

export const MainCollusionLabModal: React.FC<MainCollusionLabModalProps> = ({
  isOpen,
  onClose
}) => {
  // Recipients
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [loadingRecipients, setLoadingRecipients] = useState(false);

  // Config
  const [selectedCoalition, setSelectedCoalition] = useState<string[]>([]);
  const [attackMethod, setAttackMethod] = useState<AttackMethod>('majority');
  const [codeLength, setCodeLength] = useState<number>(64);

  // Execution
  const [isExecuting, setIsExecuting] = useState(false);
  const [result, setResult] = useState<CollusionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Bar chart ref
  const chartRef = useRef<HTMLCanvasElement>(null);

  // Load recipients on open
  useEffect(() => {
    if (!isOpen) return;
    setLoadingRecipients(true);
    apiService.getRecipients().then((data) => {
      setRecipients(data || []);
      setLoadingRecipients(false);
    }).catch(() => {
      // Provide demo recipients if backend unavailable
      setRecipients([
        { recipient_id: 'alice_vance', name: 'Alice Vance', role: 'Principal Cryptanalyst' },
        { recipient_id: 'bob_martinez', name: 'Bob Martinez', role: 'Lead Systems Architect' },
        { recipient_id: 'charlie_okonkwo', name: 'Charlie Okonkwo', role: 'Senior Analyst' },
        { recipient_id: 'diana_reyes', name: 'Diana Reyes', role: 'Intelligence Officer' },
        { recipient_id: 'marcus_cole', name: 'Marcus Cole', role: 'Field Operative' }
      ]);
      setLoadingRecipients(false);
    });
  }, [isOpen]);

  // Draw bar chart when results arrive
  useEffect(() => {
    if (!result || !chartRef.current || result.scores.length === 0) return;
    const canvas = chartRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const W = canvas.offsetWidth;
    const H = canvas.offsetHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);

    const pad = { top: 20, right: 20, bottom: 50, left: 55 };
    const chartW = W - pad.left - pad.right;
    const chartH = H - pad.top - pad.bottom;

    // Background
    ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
    ctx.fillRect(0, 0, W, H);

    const scores = result.scores;
    const maxScore = Math.max(...scores.map(s => s.score), result.threshold * 1.4) * 1.1;
    const barW = (chartW / scores.length) * 0.65;
    const gap = (chartW / scores.length) * 0.35;

    // Grid lines
    ctx.strokeStyle = 'rgba(100,116,139,0.2)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = pad.top + chartH - (i / 5) * chartH;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(pad.left + chartW, y);
      ctx.stroke();
      // Y labels
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(((maxScore * i) / 5).toFixed(1), pad.left - 6, y + 4);
    }

    // Bars
    scores.forEach((s, i) => {
      const x = pad.left + i * (chartW / scores.length) + gap / 2;
      const barH = (s.score / maxScore) * chartH;
      const y = pad.top + chartH - barH;

      // Gradient fill
      const grad = ctx.createLinearGradient(x, y, x, pad.top + chartH);
      if (s.accused) {
        grad.addColorStop(0, 'rgba(239,68,68,0.95)');
        grad.addColorStop(1, 'rgba(185,28,28,0.4)');
      } else {
        grad.addColorStop(0, 'rgba(34,197,94,0.95)');
        grad.addColorStop(1, 'rgba(21,128,61,0.4)');
      }
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.roundRect(x, y, barW, barH, [4, 4, 0, 0]);
      ctx.fill();

      // Score label on top of bar
      ctx.fillStyle = s.accused ? '#fca5a5' : '#86efac';
      ctx.font = 'bold 10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(s.score.toFixed(2), x + barW / 2, y - 4);

      // Name label below
      ctx.fillStyle = '#94a3b8';
      ctx.font = '9px Inter, sans-serif';
      const shortName = s.name.split(' ')[0] || s.recipient_id.slice(0, 8);
      ctx.fillText(shortName, x + barW / 2, pad.top + chartH + 14);

      // Accused/innocent icon label
      ctx.fillStyle = s.accused ? '#ef4444' : '#22c55e';
      ctx.fillText(s.accused ? '⚑ ACCUSED' : '✓ CLEAR', x + barW / 2, pad.top + chartH + 28);
    });

    // Threshold line
    const threshY = pad.top + chartH - (result.threshold / maxScore) * chartH;
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 3]);
    ctx.beginPath();
    ctx.moveTo(pad.left, threshY);
    ctx.lineTo(pad.left + chartW, threshY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Threshold label
    ctx.fillStyle = '#f59e0b';
    ctx.font = 'bold 10px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`τ = ${result.threshold.toFixed(2)}`, pad.left + 4, threshY - 5);

  }, [result]);

  const toggleCoalitionMember = (id: string) => {
    setSelectedCoalition(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleRunAttack = async () => {
    if (selectedCoalition.length < 2) {
      setError('Select at least 2 coalition members to simulate a colluding group.');
      return;
    }
    setIsExecuting(true);
    setError(null);
    setResult(null);

    try {
      const data = await apiService.runCollusionAttack({
        coalition_recipient_ids: selectedCoalition,
        attack_method: attackMethod,
        code_length: codeLength
      });
      setResult(data);
    } catch (e: any) {
      setError('Execution failed: ' + (e?.message || 'Unknown error'));
    } finally {
      setIsExecuting(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setSelectedCoalition([]);
  };

  if (!isOpen) return null;

  const isLive = apiService.isOnline();

  return (
    <div className="main-modal-backdrop" onClick={onClose}>
      <div
        className="main-modal glass-panel"
        style={{
          maxWidth: '1020px',
          width: '100%',
          maxHeight: '92vh',
          overflowY: 'auto',
          borderRadius: '24px'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="main-modal-header"
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid var(--main-border)',
            background: 'var(--main-surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ padding: '8px', borderRadius: '12px', background: 'rgba(99,102,241,0.15)', color: '#818CF8' }}>
              <Layers size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 className="main-modal-title" style={{ fontSize: '18px', fontWeight: 700, margin: 0, letterSpacing: '-0.02em' }}>
                  Anti-Collusion Lab
                </h2>
                <span
                  style={{
                    padding: '2px 9px',
                    borderRadius: '9999px',
                    fontSize: '10px',
                    fontWeight: 650,
                    letterSpacing: '0.04em',
                    background: isLive ? 'rgba(34,197,94,0.15)' : 'rgba(251,191,36,0.15)',
                    color: isLive ? '#10B981' : '#F59E0B',
                    border: `1px solid ${isLive ? 'rgba(34,197,94,0.3)' : 'rgba(251,191,36,0.3)'}`
                  }}
                >
                  {isLive ? '● LIVE BACKEND' : '◎ OFFLINE SIM'}
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '2px 0 0 0' }}>
                Symmetric Tardos Fingerprinting · Coalition Traceability
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="main-btn-ghost"
            style={{ padding: '8px', borderRadius: '9999px' }}
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        <div style={{ padding: '24px', display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) 2fr', gap: '24px' }}>
          {/* LEFT: Configuration panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            {/* Recipients */}
            <div
              className="glass-card"
              style={{ padding: '16px', borderRadius: '18px', border: '1px solid var(--main-border)', background: 'var(--main-surface)' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Users size={16} style={{ color: '#818CF8' }} />
                <span style={{ fontSize: '13px', fontWeight: 650, color: 'var(--main-text-primary)' }}>Coalition Members</span>
                {selectedCoalition.length > 0 && (
                  <span style={{ marginLeft: 'auto', padding: '2px 8px', borderRadius: '9999px', fontSize: '11px', fontWeight: 600, background: 'rgba(99,102,241,0.15)', color: '#818CF8' }}>
                    {selectedCoalition.length} selected
                  </span>
                )}
              </div>

              {loadingRecipients ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: 'var(--main-text-secondary)', padding: '16px 0' }}>
                  <Loader2 size={16} className="animate-spin" />
                  <span style={{ fontSize: '12px' }}>Loading recipients…</span>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '250px', overflowY: 'auto', paddingRight: '4px' }}>
                  {recipients.map(r => {
                    const selected = selectedCoalition.includes(r.recipient_id);
                    return (
                      <button
                        key={r.recipient_id}
                        onClick={() => toggleCoalitionMember(r.recipient_id)}
                        style={{
                          width: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px',
                          padding: '8px 12px',
                          borderRadius: '12px',
                          textAlign: 'left',
                          transition: 'all 0.15s ease',
                          cursor: 'pointer',
                          background: selected
                            ? 'rgba(239,68,68,0.12)'
                            : 'var(--main-surface-hover)',
                          border: `1px solid ${selected ? 'rgba(239,68,68,0.3)' : 'var(--main-border)'}`
                        }}
                      >
                        <div
                          style={{
                            width: '28px',
                            height: '28px',
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '11px',
                            fontWeight: 700,
                            flexShrink: 0,
                            background: selected ? 'rgba(239,68,68,0.2)' : 'rgba(99,102,241,0.2)',
                            color: selected ? '#f87171' : '#a5b4fc'
                          }}
                        >
                          {(r.name || r.recipient_id).slice(0, 2).toUpperCase()}
                        </div>
                        <div style={{ minWidth: 0, flex: 1 }}>
                          <div style={{ fontSize: '12.5px', fontWeight: 600, color: 'var(--main-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.name || r.recipient_id}</div>
                          {r.role && <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.role}</div>}
                        </div>
                        {selected && <ShieldAlert size={14} style={{ color: '#ef4444', flexShrink: 0 }} />}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Attack Method */}
            <div
              className="glass-card"
              style={{ padding: '16px', borderRadius: '18px', border: '1px solid var(--main-border)', background: 'var(--main-surface)' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Sliders size={16} style={{ color: '#A855F7' }} />
                <span style={{ fontSize: '13px', fontWeight: 650, color: 'var(--main-text-primary)' }}>Attack Method</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {ATTACK_METHODS.map(m => (
                  <label
                    key={m.value}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '10px',
                      padding: '10px 12px',
                      borderRadius: '12px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      background: attackMethod === m.value
                        ? 'rgba(168,85,247,0.12)'
                        : 'var(--main-surface-hover)',
                      border: `1px solid ${attackMethod === m.value ? 'rgba(168,85,247,0.3)' : 'var(--main-border)'}`
                    }}
                  >
                    <input
                      type="radio"
                      name="attack_method"
                      value={m.value}
                      checked={attackMethod === m.value}
                      onChange={() => setAttackMethod(m.value)}
                      style={{ marginTop: '2px', accentColor: '#a855f7' }}
                    />
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 650, color: 'var(--main-text-primary)' }}>{m.label}</div>
                      <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '2px', lineHeight: 1.4 }}>{m.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Code Length */}
            <div
              className="glass-card"
              style={{ padding: '16px', borderRadius: '18px', border: '1px solid var(--main-border)', background: 'var(--main-surface)' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <Cpu size={16} style={{ color: '#06B6D4' }} />
                <span style={{ fontSize: '13px', fontWeight: 650, color: 'var(--main-text-primary)' }}>Code Length</span>
                <span style={{ marginLeft: 'auto', fontSize: '12px', fontFamily: 'monospace', fontWeight: 650, color: '#06B6D4' }}>{codeLength} bits</span>
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {CODE_LENGTHS.map(n => (
                  <button
                    key={n}
                    onClick={() => setCodeLength(n)}
                    style={{
                      padding: '5px 12px',
                      borderRadius: '9999px',
                      fontSize: '11.5px',
                      fontFamily: 'monospace',
                      fontWeight: 650,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      background: codeLength === n ? '#06B6D4' : 'var(--main-surface-hover)',
                      color: codeLength === n ? '#FFFFFF' : 'var(--main-text-secondary)',
                      border: `1px solid ${codeLength === n ? '#06B6D4' : 'var(--main-border)'}`
                    }}
                  >
                    {n}
                  </button>
                ))}
              </div>
              <p style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', margin: '8px 0 0 0', lineHeight: 1.4 }}>
                Longer codes → sharper discrimination but slower. 64 bits recommended for live demos.
              </p>
            </div>

            {/* Action buttons */}
            <button
              onClick={handleRunAttack}
              disabled={isExecuting || selectedCoalition.length < 2}
              className="btn-primary"
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '12px',
                borderRadius: '9999px',
                fontWeight: 650,
                fontSize: '13px',
                opacity: (isExecuting || selectedCoalition.length < 2) ? 0.6 : 1,
                cursor: (isExecuting || selectedCoalition.length < 2) ? 'not-allowed' : 'pointer'
              }}
            >
              {isExecuting ? (
                <><Loader2 size={15} className="animate-spin" /> Running Tardos Analysis…</>
              ) : (
                <><Zap size={15} /> Run Coalition Attack</>
              )}
            </button>

            {result && (
              <button
                onClick={handleReset}
                className="main-btn-secondary"
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '10px',
                  borderRadius: '9999px',
                  fontSize: '12.5px'
                }}
              >
                <RotateCcw size={14} /> Reset Lab
              </button>
            )}

            {error && (
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', padding: '12px', borderRadius: '14px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)', color: '#EF4444', fontSize: '12px' }}>
                <AlertCircle size={15} style={{ flexShrink: 0, marginTop: '2px' }} />
                <span>{error}</span>
              </div>
            )}
          </div>

          {/* RIGHT: Results panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            {/* Theory explainer (pre-result) */}
            {!result && (
              <div
                className="glass-card"
                style={{ padding: '20px', borderRadius: '18px', border: '1px solid var(--main-border)', background: 'var(--main-surface)' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                  <BarChart2 size={18} style={{ color: '#818CF8' }} />
                  <span style={{ fontSize: '14px', fontWeight: 650, color: 'var(--main-text-primary)' }}>Symmetric Tardos Fingerprinting</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '12.5px', color: 'var(--main-text-secondary)', lineHeight: 1.55 }}>
                  <p style={{ margin: 0 }}>
                    <strong style={{ color: 'var(--main-text-primary)' }}>Tardos codes</strong> are probabilistic
                    fingerprinting codes that are provably robust against collusion attacks. Each recipient receives a unique
                    binary codeword. When a pirate document is discovered, the colluding recipients can be mathematically traced
                    even if they combine or interleave their copies.
                  </p>
                  <p style={{ margin: 0 }}>
                    The <strong style={{ color: '#F59E0B', fontFamily: 'monospace' }}>τ (tau) threshold</strong> is computed from the
                    Neyman-Pearson criterion. Any recipient whose Tardos score exceeds τ is accused as a colluder
                    with false-positive probability below 10⁻³.
                  </p>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginTop: '8px' }}>
                    {[
                      { label: 'Select Recipients', desc: 'Choose ≥ 2 colluders from the left panel', icon: '①' },
                      { label: 'Pick Attack', desc: 'Choose how coalition forges the piracy copy', icon: '②' },
                      { label: 'Run Analysis', desc: 'Tardos scores computed per recipient', icon: '③' }
                    ].map(step => (
                      <div key={step.icon}
                        style={{ padding: '14px 10px', borderRadius: '14px', textAlign: 'center', background: 'var(--main-surface-hover)', border: '1px solid var(--main-border)' }}>
                        <div style={{ fontSize: '18px', color: 'var(--apple-blue)', fontWeight: 700, marginBottom: '4px' }}>{step.icon}</div>
                        <div style={{ fontSize: '12px', fontWeight: 650, color: 'var(--main-text-primary)', marginBottom: '2px' }}>{step.label}</div>
                        <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>{step.desc}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Result: Summary cards */}
            {result && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
                  {[
                    {
                      label: 'Code Length',
                      value: `${result.code_length} bits`,
                      color: '#06B6D4'
                    },
                    {
                      label: 'Coalition Size',
                      value: `${result.coalition_size} members`,
                      color: '#EF4444'
                    },
                    {
                      label: 'Threshold τ',
                      value: result.threshold.toFixed(2),
                      color: '#F59E0B'
                    },
                    {
                      label: 'Accused',
                      value: `${result.accused_recipients.length} / ${result.scores.length}`,
                      color: result.accused_recipients.length > 0 ? '#EF4444' : '#10B981'
                    }
                  ].map(card => (
                    <div key={card.label}
                      className="glass-card"
                      style={{ padding: '14px 12px', borderRadius: '16px', textAlign: 'center', background: 'var(--main-surface)', border: '1px solid var(--main-border)' }}>
                      <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, marginBottom: '4px' }}>{card.label}</div>
                      <div style={{ fontSize: '16px', fontWeight: 700, fontFamily: 'monospace', color: card.color }}>
                        {card.value}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Marking Assumption */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '12px 16px',
                    borderRadius: '14px',
                    fontSize: '12px',
                    background: result.marking_assumption_valid
                      ? 'rgba(34,197,94,0.08)'
                      : 'rgba(239,68,68,0.08)',
                    border: `1px solid ${result.marking_assumption_valid ? 'rgba(34,197,94,0.25)' : 'rgba(239,68,68,0.25)'}`
                  }}
                >
                  {result.marking_assumption_valid
                    ? <CheckCircle2 size={16} style={{ color: '#10B981', flexShrink: 0 }} />
                    : <AlertTriangle size={16} style={{ color: '#EF4444', flexShrink: 0 }} />}
                  <span style={{ color: 'var(--main-text-secondary)', lineHeight: 1.4 }}>
                    <strong style={{ color: result.marking_assumption_valid ? '#10B981' : '#EF4444' }}>
                      Marking Assumption {result.marking_assumption_valid ? 'SATISFIED' : 'VIOLATED'}
                    </strong>
                    {result.marking_assumption_valid
                      ? ' — All piracy bits appear in at least one colluder’s codeword. Identification is provably valid.'
                      : ' — Coalition produced bits outside their codewords. Results may be unreliable.'}
                  </span>
                </div>

                {/* Bar chart */}
                <div
                  className="glass-card"
                  style={{ padding: '16px', borderRadius: '18px', border: '1px solid var(--main-border)', background: 'var(--main-surface)' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                    <BarChart2 size={16} style={{ color: '#818CF8' }} />
                    <span style={{ fontSize: '13px', fontWeight: 650, color: 'var(--main-text-primary)' }}>Tardos Score Distribution</span>
                    <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#F59E0B', fontFamily: 'monospace', fontWeight: 650 }}>— τ = {result.threshold.toFixed(2)}</span>
                  </div>
                  <canvas
                    ref={chartRef}
                    style={{ width: '100%', height: '200px', display: 'block', borderRadius: '12px' }}
                  />
                </div>

                {/* Per-recipient verdict table */}
                <div
                  className="glass-card"
                  style={{ borderRadius: '18px', border: '1px solid var(--main-border)', background: 'var(--main-surface)', overflow: 'hidden' }}
                >
                  <div
                    style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 650, color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', borderBottom: '1px solid var(--main-border)', background: 'var(--main-surface-hover)' }}
                  >
                    Per-Recipient Verdict
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    {result.scores
                      .sort((a, b) => b.score - a.score)
                      .map((s, idx) => (
                        <div
                          key={s.recipient_id}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '14px',
                            padding: '12px 16px',
                            borderTop: idx > 0 ? '1px solid var(--main-border)' : 'none',
                            background: s.accused
                              ? 'rgba(239,68,68,0.06)'
                              : 'transparent'
                          }}
                        >
                          {s.accused
                            ? <UserX size={16} style={{ color: '#EF4444', flexShrink: 0 }} />
                            : <UserCheck size={16} style={{ color: '#10B981', flexShrink: 0 }} />}
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.name}</div>
                            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>{s.recipient_id}</div>
                          </div>
                          {/* Score bar */}
                          <div style={{ width: '120px', flexShrink: 0 }}>
                            <div style={{ height: '6px', borderRadius: '9999px', overflow: 'hidden', background: 'var(--main-surface-hover)' }}>
                              <div
                                style={{
                                  height: '100%',
                                  borderRadius: '9999px',
                                  transition: 'all 0.7s ease',
                                  width: `${Math.min(100, (s.score / (result.threshold * 2)) * 100)}%`,
                                  background: s.accused
                                    ? 'linear-gradient(90deg, #ef4444, #f87171)'
                                    : 'linear-gradient(90deg, #10b981, #34d399)'
                                }}
                              />
                            </div>
                          </div>
                          <div style={{ textAlign: 'right', flexShrink: 0, width: '70px' }}>
                            <div
                              style={{ fontSize: '13px', fontFamily: 'monospace', fontWeight: 700, color: s.accused ? '#EF4444' : '#10B981' }}
                            >
                              {s.score.toFixed(3)}
                            </div>
                            <div style={{ fontSize: '10.5px', fontWeight: 650, color: s.accused ? '#EF4444' : '#10B981' }}>
                              {s.accused ? 'ACCUSED' : 'INNOCENT'}
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Attack method info */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '12px 16px',
                    borderRadius: '14px',
                    fontSize: '12px',
                    background: 'rgba(99,102,241,0.08)',
                    border: '1px solid rgba(99,102,241,0.2)'
                  }}
                >
                  <Layers size={16} style={{ color: '#818CF8', flexShrink: 0 }} />
                  <span style={{ color: 'var(--main-text-secondary)' }}>
                    Attack: <strong style={{ color: 'var(--main-text-primary)' }}>{result.attack_method}</strong> ·
                    Code length: <strong style={{ color: 'var(--main-text-primary)' }}>{result.code_length} bits</strong> ·
                    Coalition of <strong style={{ color: '#EF4444' }}>{result.coalition_size} members</strong>
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainCollusionLabModal;

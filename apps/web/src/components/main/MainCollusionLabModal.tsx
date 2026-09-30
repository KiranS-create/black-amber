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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div
        className="relative w-full max-w-5xl max-h-[92vh] overflow-y-auto rounded-2xl border shadow-2xl"
        style={{
          background: 'linear-gradient(135deg, rgba(10,10,30,0.98) 0%, rgba(15,25,50,0.98) 100%)',
          borderColor: 'rgba(99,102,241,0.3)'
        }}
      >
        {/* Header */}
        <div
          className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b"
          style={{
            borderColor: 'rgba(99,102,241,0.2)',
            background: 'linear-gradient(90deg, rgba(99,102,241,0.12) 0%, rgba(139,92,246,0.08) 100%)'
          }}
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl" style={{ background: 'rgba(99,102,241,0.2)' }}>
              <Layers className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">Anti-Collusion Lab</h2>
              <p className="text-xs text-indigo-300/70 mt-0.5">Symmetric Tardos Fingerprinting · Coalition Traceability</p>
            </div>
            <span
              className="ml-3 px-2 py-0.5 rounded text-xs font-semibold"
              style={{
                background: isLive ? 'rgba(34,197,94,0.15)' : 'rgba(251,191,36,0.15)',
                color: isLive ? '#4ade80' : '#fbbf24',
                border: `1px solid ${isLive ? 'rgba(34,197,94,0.3)' : 'rgba(251,191,36,0.3)'}`
              }}
            >
              {isLive ? '● LIVE BACKEND' : '◎ OFFLINE SIM'}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* LEFT: Configuration panel */}
          <div className="lg:col-span-1 space-y-5">
            {/* Recipients */}
            <div
              className="rounded-xl p-4 border"
              style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.08)' }}
            >
              <div className="flex items-center gap-2 mb-3">
                <Users className="w-4 h-4 text-indigo-400" />
                <span className="text-sm font-semibold text-white">Coalition Members</span>
                {selectedCoalition.length > 0 && (
                  <span className="ml-auto px-2 py-0.5 rounded-full text-xs bg-indigo-500/20 text-indigo-300">
                    {selectedCoalition.length} selected
                  </span>
                )}
              </div>

              {loadingRecipients ? (
                <div className="flex items-center gap-2 text-slate-400 py-4 justify-center">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-xs">Loading recipients…</span>
                </div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {recipients.map(r => {
                    const selected = selectedCoalition.includes(r.recipient_id);
                    return (
                      <button
                        key={r.recipient_id}
                        onClick={() => toggleCoalitionMember(r.recipient_id)}
                        className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all duration-150"
                        style={{
                          background: selected
                            ? 'rgba(239,68,68,0.18)'
                            : 'rgba(255,255,255,0.04)',
                          borderWidth: 1,
                          borderStyle: 'solid',
                          borderColor: selected ? 'rgba(239,68,68,0.4)' : 'rgba(255,255,255,0.07)'
                        }}
                      >
                        <div
                          className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                          style={{
                            background: selected ? 'rgba(239,68,68,0.3)' : 'rgba(99,102,241,0.3)',
                            color: selected ? '#f87171' : '#a5b4fc'
                          }}
                        >
                          {(r.name || r.recipient_id).slice(0, 2).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <div className="text-xs font-medium text-white truncate">{r.name || r.recipient_id}</div>
                          {r.role && <div className="text-xs text-slate-500 truncate">{r.role}</div>}
                        </div>
                        {selected && <ShieldAlert className="w-3.5 h-3.5 text-red-400 ml-auto flex-shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Attack Method */}
            <div
              className="rounded-xl p-4 border"
              style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.08)' }}
            >
              <div className="flex items-center gap-2 mb-3">
                <Sliders className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-semibold text-white">Attack Method</span>
              </div>
              <div className="space-y-2">
                {ATTACK_METHODS.map(m => (
                  <label
                    key={m.value}
                    className="flex items-start gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all"
                    style={{
                      background: attackMethod === m.value
                        ? 'rgba(139,92,246,0.18)'
                        : 'rgba(255,255,255,0.03)',
                      border: `1px solid ${attackMethod === m.value ? 'rgba(139,92,246,0.4)' : 'rgba(255,255,255,0.06)'}`
                    }}
                  >
                    <input
                      type="radio"
                      name="attack_method"
                      value={m.value}
                      checked={attackMethod === m.value}
                      onChange={() => setAttackMethod(m.value)}
                      className="mt-0.5 accent-purple-500"
                    />
                    <div>
                      <div className="text-xs font-semibold text-white">{m.label}</div>
                      <div className="text-xs text-slate-500 mt-0.5 leading-relaxed">{m.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Code Length */}
            <div
              className="rounded-xl p-4 border"
              style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.08)' }}
            >
              <div className="flex items-center gap-2 mb-3">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <span className="text-sm font-semibold text-white">Code Length</span>
                <span className="ml-auto text-xs font-mono text-cyan-300">{codeLength} bits</span>
              </div>
              <div className="flex gap-2 flex-wrap">
                {CODE_LENGTHS.map(n => (
                  <button
                    key={n}
                    onClick={() => setCodeLength(n)}
                    className="px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all"
                    style={{
                      background: codeLength === n ? 'rgba(6,182,212,0.25)' : 'rgba(255,255,255,0.05)',
                      borderWidth: 1,
                      borderStyle: 'solid',
                      borderColor: codeLength === n ? 'rgba(6,182,212,0.5)' : 'rgba(255,255,255,0.08)',
                      color: codeLength === n ? '#67e8f9' : '#94a3b8'
                    }}
                  >
                    {n}
                  </button>
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Longer codes → sharper discrimination but slower. 64 bits recommended for demos.
              </p>
            </div>

            {/* Action buttons */}
            <button
              onClick={handleRunAttack}
              disabled={isExecuting || selectedCoalition.length < 2}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm transition-all"
              style={{
                background: isExecuting || selectedCoalition.length < 2
                  ? 'rgba(99,102,241,0.2)'
                  : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                color: isExecuting || selectedCoalition.length < 2 ? '#6366f1' : 'white',
                cursor: isExecuting || selectedCoalition.length < 2 ? 'not-allowed' : 'pointer'
              }}
            >
              {isExecuting ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Running Tardos Analysis…</>
              ) : (
                <><Zap className="w-4 h-4" /> Run Coalition Attack</>
              )}
            </button>

            {result && (
              <button
                onClick={handleReset}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm text-slate-400 hover:text-white transition-colors"
                style={{ background: 'rgba(255,255,255,0.04)' }}
              >
                <RotateCcw className="w-4 h-4" /> Reset Lab
              </button>
            )}

            {error && (
              <div className="flex items-start gap-2 p-3 rounded-xl text-red-300 text-xs"
                style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}>
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                {error}
              </div>
            )}
          </div>

          {/* RIGHT: Results panel */}
          <div className="lg:col-span-2 space-y-5">
            {/* Theory explainer (pre-result) */}
            {!result && (
              <div
                className="rounded-xl p-5 border"
                style={{ background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.07)' }}
              >
                <div className="flex items-center gap-2 mb-4">
                  <BarChart2 className="w-5 h-5 text-indigo-400" />
                  <span className="text-sm font-semibold text-white">Symmetric Tardos Fingerprinting</span>
                </div>
                <div className="space-y-3 text-xs text-slate-400 leading-relaxed">
                  <p>
                    <span className="text-indigo-300 font-semibold">Tardos codes</span> are probabilistic
                    fingerprinting codes that are robust against collusion attacks. Each recipient receives a unique
                    binary codeword. When a pirate document is discovered, the colluding recipients can be traced
                    even if they combine their copies.
                  </p>
                  <p>
                    The <span className="text-yellow-300 font-mono">τ (tau) threshold</span> is computed from the
                    Neyman-Pearson criterion. Any recipient whose Tardos score exceeds τ is identified as a colluder
                    with false-positive probability below 10⁻³.
                  </p>
                  <div className="grid grid-cols-3 gap-3 mt-4">
                    {[
                      { label: 'Select Recipients', desc: 'Choose ≥ 2 colluders from the left panel', icon: '①' },
                      { label: 'Pick Attack', desc: 'Choose how the coalition forges the piracy copy', icon: '②' },
                      { label: 'Run Analysis', desc: 'Tardos scores computed per recipient', icon: '③' }
                    ].map(step => (
                      <div key={step.icon}
                        className="rounded-lg p-3 text-center"
                        style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)' }}>
                        <div className="text-2xl text-indigo-300 font-bold mb-1">{step.icon}</div>
                        <div className="text-white text-xs font-semibold mb-1">{step.label}</div>
                        <div className="text-slate-500 text-xs">{step.desc}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Result: Summary cards */}
            {result && (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    {
                      label: 'Code Length',
                      value: `${result.code_length} bits`,
                      color: '#67e8f9',
                      bg: 'rgba(6,182,212,0.1)',
                      border: 'rgba(6,182,212,0.25)'
                    },
                    {
                      label: 'Coalition Size',
                      value: `${result.coalition_size} members`,
                      color: '#f87171',
                      bg: 'rgba(239,68,68,0.1)',
                      border: 'rgba(239,68,68,0.25)'
                    },
                    {
                      label: 'Threshold τ',
                      value: result.threshold.toFixed(2),
                      color: '#fbbf24',
                      bg: 'rgba(245,158,11,0.1)',
                      border: 'rgba(245,158,11,0.25)'
                    },
                    {
                      label: 'Accused',
                      value: `${result.accused_recipients.length} / ${result.scores.length}`,
                      color: result.accused_recipients.length > 0 ? '#f87171' : '#4ade80',
                      bg: result.accused_recipients.length > 0 ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)',
                      border: result.accused_recipients.length > 0 ? 'rgba(239,68,68,0.25)' : 'rgba(34,197,94,0.25)'
                    }
                  ].map(card => (
                    <div key={card.label}
                      className="rounded-xl p-3 text-center"
                      style={{ background: card.bg, border: `1px solid ${card.border}` }}>
                      <div className="text-xs text-slate-400 mb-1">{card.label}</div>
                      <div className="text-sm font-bold font-mono" style={{ color: card.color }}>
                        {card.value}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Marking Assumption */}
                <div
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs"
                  style={{
                    background: result.marking_assumption_valid
                      ? 'rgba(34,197,94,0.08)'
                      : 'rgba(239,68,68,0.08)',
                    border: `1px solid ${result.marking_assumption_valid ? 'rgba(34,197,94,0.25)' : 'rgba(239,68,68,0.25)'}`
                  }}
                >
                  {result.marking_assumption_valid
                    ? <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
                    : <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />}
                  <span className="text-slate-300">
                    <strong className={result.marking_assumption_valid ? 'text-green-400' : 'text-red-400'}>
                      Marking Assumption {result.marking_assumption_valid ? 'SATISFIED' : 'VIOLATED'}
                    </strong>
                    {result.marking_assumption_valid
                      ? ' \u2014 All piracy bits appear in at least one colluder\u2019s codeword. Identification is provably valid.'
                      : ' \u2014 Coalition produced bits outside their codewords. Results may be unreliable.'}
                  </span>
                </div>

                {/* Bar chart */}
                <div
                  className="rounded-xl p-4 border"
                  style={{ background: 'rgba(0,0,0,0.4)', borderColor: 'rgba(255,255,255,0.08)' }}
                >
                  <div className="flex items-center gap-2 mb-3">
                    <BarChart2 className="w-4 h-4 text-indigo-400" />
                    <span className="text-sm font-semibold text-white">Tardos Score Distribution</span>
                    <span className="ml-auto text-xs text-yellow-400 font-mono">— τ = {result.threshold.toFixed(2)}</span>
                  </div>
                  <canvas
                    ref={chartRef}
                    className="w-full"
                    style={{ height: '200px', display: 'block' }}
                  />
                </div>

                {/* Per-recipient verdict table */}
                <div
                  className="rounded-xl border overflow-hidden"
                  style={{ borderColor: 'rgba(255,255,255,0.08)' }}
                >
                  <div
                    className="px-4 py-2.5 text-xs font-semibold text-slate-400 uppercase tracking-widest"
                    style={{ background: 'rgba(255,255,255,0.04)' }}
                  >
                    Per-Recipient Verdict
                  </div>
                  <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                    {result.scores
                      .sort((a, b) => b.score - a.score)
                      .map(s => (
                        <div
                          key={s.recipient_id}
                          className="flex items-center gap-4 px-4 py-3"
                          style={{
                            background: s.accused
                              ? 'rgba(239,68,68,0.06)'
                              : 'rgba(34,197,94,0.03)'
                          }}
                        >
                          {s.accused
                            ? <UserX className="w-4 h-4 text-red-400 flex-shrink-0" />
                            : <UserCheck className="w-4 h-4 text-green-400 flex-shrink-0" />}
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-white truncate">{s.name}</div>
                            <div className="text-xs text-slate-500">{s.recipient_id}</div>
                          </div>
                          {/* Score bar */}
                          <div className="w-32 flex-shrink-0">
                            <div className="h-1.5 rounded-full overflow-hidden bg-white/10">
                              <div
                                className="h-full rounded-full transition-all duration-700"
                                style={{
                                  width: `${Math.min(100, (s.score / (result.threshold * 2)) * 100)}%`,
                                  background: s.accused
                                    ? 'linear-gradient(90deg, #ef4444, #f87171)'
                                    : 'linear-gradient(90deg, #22c55e, #4ade80)'
                                }}
                              />
                            </div>
                          </div>
                          <div className="text-right flex-shrink-0 w-16">
                            <div
                              className="text-sm font-mono font-bold"
                              style={{ color: s.accused ? '#f87171' : '#4ade80' }}
                            >
                              {s.score.toFixed(3)}
                            </div>
                            <div className="text-xs" style={{ color: s.accused ? '#ef4444' : '#22c55e' }}>
                              {s.accused ? 'ACCUSED' : 'INNOCENT'}
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Attack method info */}
                <div
                  className="flex items-start gap-3 px-4 py-3 rounded-xl text-xs"
                  style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)' }}
                >
                  <Layers className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                  <span className="text-slate-400">
                    Attack: <strong className="text-indigo-300">{result.attack_method}</strong> ·
                    Code length: <strong className="text-indigo-300">{result.code_length} bits</strong> ·
                    Coalition of <strong className="text-red-300">{result.coalition_size}</strong>
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

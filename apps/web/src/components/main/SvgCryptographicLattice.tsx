import React, { useState } from 'react';
import { Shield, Key, Cpu, Database, CheckCircle2, Lock, ArrowRight, Zap, RefreshCw } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export const SvgCryptographicLattice: React.FC = () => {
  const { theme } = useTheme();
  const isLight = theme === 'light';
  const [activeNode, setActiveNode] = useState<number>(1);

  const nodes = [
    {
      id: 0,
      title: 'Broadcast Envelope',
      std: 'NIST FIPS 203',
      tech: 'ML-KEM-768 + AES-GCM',
      details: 'LWE Lattice q=3329, k=3. Single ciphertext container broadcast to all N cleared recipients.',
      icon: Lock,
      color: '#0284C7',
      status: 'SEALED',
    },
    {
      id: 1,
      title: 'Client WASM Enclave',
      std: 'Memory Isolation',
      tech: '64MB Private RAM',
      details: 'Unpaged linear memory. Direct volatile raster watermark injection prior to pixel compositing.',
      icon: Cpu,
      color: '#8B5CF6',
      status: 'AIR-GAPPED',
    },
    {
      id: 2,
      title: 'Tardos DSSS Modulation',
      std: 'Traitor-Tracing',
      tech: '2D DCT Frequency Mark',
      details: 'Orthogonal Tardos codeword (m=128) embedded at zero perceptual degradation (PSNR 48.2 dB).',
      icon: Zap,
      color: '#F59E0B',
      status: 'MODULATED',
    },
    {
      id: 3,
      title: 'Immutable DLT Ledger',
      std: 'NIST FIPS 204',
      tech: 'ML-DSA-65 + RFC-6962',
      details: 'Hardware enclave signs decryption receipt H(P)||UID. Merkle tree committed before viewport unlocks.',
      icon: Database,
      color: '#10B981',
      status: 'COMMITTED',
    },
  ];

  return (
    <div 
      className="glass-panel"
      style={{
        borderRadius: '10px',
        padding: '20px 24px',
        marginBottom: '20px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Header bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div 
            style={{ 
              width: '28px', 
              height: '28px', 
              borderRadius: '6px', 
              background: isLight ? 'rgba(2, 132, 199, 0.1)' : 'rgba(56, 189, 248, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#0284C7'
            }}
          >
            <Shield size={16} />
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', letterSpacing: '-0.01em' }}>
              Cryptographic Architecture & Signal Pipeline
            </div>
            <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', fontFamily: 'var(--font-mono)' }}>
              NIST FIPS 203 (ML-KEM-768) · FIPS 204 (ML-DSA-65) · Gabor Tardos Traitor Tracing
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span 
            style={{ 
              fontSize: '11px', 
              fontFamily: 'var(--font-mono)', 
              padding: '2px 8px', 
              borderRadius: '4px',
              background: isLight ? 'rgba(16, 185, 129, 0.1)' : 'rgba(34, 197, 94, 0.15)',
              color: isLight ? '#059669' : '#22C55E',
              border: `1px solid ${isLight ? 'rgba(16, 185, 129, 0.25)' : 'rgba(34, 197, 94, 0.3)'}`,
              fontWeight: 600,
            }}
          >
            ACTIVE KERNEL • 2D VECTOR HUD
          </span>
        </div>
      </div>

      {/* 2D SVG Pipeline Diagram */}
      <div style={{ width: '100%', position: 'relative' }}>
        <svg 
          viewBox="0 0 880 130" 
          style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}
        >
          <defs>
            <linearGradient id="pqcBeam" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0284C7" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#8B5CF6" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#10B981" stopOpacity="0.8" />
            </linearGradient>
            <filter id="nodeGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="4" floodOpacity={isLight ? "0.08" : "0.3"} />
            </filter>
          </defs>

          {/* Connection Cables / Transmission Lines */}
          <line 
            x1="110" y1="50" x2="330" y2="50" 
            stroke={isLight ? "#CBD5E1" : "rgba(255,255,255,0.12)"} 
            strokeWidth="3" 
            strokeDasharray="4 4" 
          />
          <line 
            x1="330" y1="50" x2="550" y2="50" 
            stroke={isLight ? "#CBD5E1" : "rgba(255,255,255,0.12)"} 
            strokeWidth="3" 
            strokeDasharray="4 4" 
          />
          <line 
            x1="550" y1="50" x2="770" y2="50" 
            stroke={isLight ? "#CBD5E1" : "rgba(255,255,255,0.12)"} 
            strokeWidth="3" 
            strokeDasharray="4 4" 
          />

          {/* Active Data Flow Line */}
          <line 
            x1="110" y1="50" x2="770" y2="50" 
            stroke="url(#pqcBeam)" 
            strokeWidth="2" 
            strokeOpacity="0.7"
          />

          {/* Pipeline Nodes */}
          {nodes.map((node, i) => {
            const cx = 110 + i * 220;
            const cy = 50;
            const isSelected = activeNode === i;
            const IconComponent = node.icon;

            return (
              <g 
                key={node.id} 
                onClick={() => setActiveNode(i)}
                style={{ cursor: 'pointer' }}
              >
                {/* Outer Ring */}
                <circle 
                  cx={cx} cy={cy} r={isSelected ? 30 : 25}
                  fill={isLight ? "#FFFFFF" : (isSelected ? "rgba(26, 33, 43, 0.95)" : "rgba(18, 22, 27, 0.9)")}
                  stroke={isSelected ? node.color : (isLight ? "#CBD5E1" : "rgba(255, 255, 255, 0.15)")}
                  strokeWidth={isSelected ? 3 : 1.5}
                  filter="url(#nodeGlow)"
                  style={{ transition: 'all 0.2s ease' }}
                />

                {/* Inner Pulse */}
                {isSelected && (
                  <circle 
                    cx={cx} cy={cy} r="36"
                    fill="none"
                    stroke={node.color}
                    strokeWidth="1"
                    strokeOpacity="0.4"
                    strokeDasharray="3 3"
                  />
                )}

                {/* Node Step Index Badge */}
                <circle 
                  cx={cx + 20} cy={cy - 20} r="10"
                  fill={node.color}
                />
                <text 
                  x={cx + 20} y={cy - 16}
                  textAnchor="middle"
                  fill="#FFFFFF"
                  fontSize="10"
                  fontWeight="bold"
                  fontFamily="sans-serif"
                >
                  {i + 1}
                </text>

                {/* Labels below node */}
                <text 
                  x={cx} y={cy + 42}
                  textAnchor="middle"
                  fill={isLight ? "#0F172A" : "#EDEDE8"}
                  fontSize="11.5"
                  fontWeight="600"
                  fontFamily="sans-serif"
                >
                  {node.title}
                </text>
                <text 
                  x={cx} y={cy + 56}
                  textAnchor="middle"
                  fill={isLight ? "#64748B" : "#9BA3AF"}
                  fontSize="10"
                  fontFamily="monospace"
                >
                  {node.tech}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Interactive Detail Inspector Strip */}
      <div 
        style={{ 
          marginTop: '8px', 
          padding: '12px 16px', 
          borderRadius: '8px', 
          background: isLight ? '#F1F5F9' : 'rgba(18, 22, 27, 0.6)', 
          border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255, 255, 255, 0.08)'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span 
            style={{ 
              fontSize: '11px', 
              fontWeight: 700, 
              padding: '3px 8px', 
              borderRadius: '4px', 
              background: nodes[activeNode].color, 
              color: '#FFFFFF' 
            }}
          >
            STAGE {activeNode + 1}: {nodes[activeNode].status}
          </span>
          <span style={{ fontSize: '12px', color: 'var(--main-text-primary)', fontWeight: 500 }}>
            <strong style={{ color: nodes[activeNode].color }}>{nodes[activeNode].title} ({nodes[activeNode].std}):</strong> {nodes[activeNode].details}
          </span>
        </div>

        <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
          {nodes.map((n, idx) => (
            <button
              key={n.id}
              onClick={() => setActiveNode(idx)}
              style={{
                border: 'none',
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: activeNode === idx ? n.color : (isLight ? '#CBD5E1' : 'rgba(255,255,255,0.2)'),
                cursor: 'pointer',
                padding: 0,
                transition: 'all 0.15s ease'
              }}
              title={n.title}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

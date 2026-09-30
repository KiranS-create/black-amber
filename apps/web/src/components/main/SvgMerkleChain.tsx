import React from 'react';
import { Database, ShieldAlert, CheckCircle2, Link2, AlertTriangle, ArrowRight } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

interface SvgMerkleChainProps {
  isTampered: boolean;
}

export const SvgMerkleChain: React.FC<SvgMerkleChainProps> = ({ isTampered }) => {
  const { theme } = useTheme();
  const isLight = theme === 'light';

  const blocks = [
    {
      id: 0,
      name: 'Genesis Root',
      hash: '0x3a9f...e102',
      prevHash: '0x0000...0000',
      type: 'MASTER_ENVELOPE',
      tampered: false,
    },
    {
      id: 1,
      name: 'Enclave Mint #1',
      hash: isTampered ? '0xBAD0...6666 [MUTATED]' : '0x7b1c...99d4',
      prevHash: '0x3a9f...e102',
      type: 'RECIPIENT_SEAL',
      tampered: isTampered,
    },
    {
      id: 2,
      name: 'Decryption Receipt #2',
      hash: isTampered ? '0xFAIL...7777 [ORPHANED]' : '0x4d8a...22e8',
      prevHash: isTampered ? '0x7b1c...99d4 [MISMATCH]' : '0x7b1c...99d4',
      type: 'ML-DSA-65_SIGNATURE',
      tampered: isTampered,
    },
    {
      id: 3,
      name: 'Forensic Proof #3',
      hash: '0x9f02...11a7',
      prevHash: '0x4d8a...22e8',
      type: 'ATTRIBUTION_CONVICTION',
      tampered: false,
    },
  ];

  return (
    <div 
      className="glass-panel"
      style={{
        borderRadius: '10px',
        padding: '18px 20px',
        marginBottom: '16px',
        border: `1px solid ${isTampered ? '#EF4444' : (isLight ? '#E2E8F0' : 'rgba(255, 255, 255, 0.08)')}`,
        transition: 'all 0.2s ease',
      }}
    >
      {/* Header bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isTampered ? (
            <ShieldAlert size={18} color="#EF4444" />
          ) : (
            <Database size={18} color="#0284C7" />
          )}
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
            RFC-6962 Cryptographic Merkle Ledger Chain & DAG
          </span>
        </div>

        <div>
          {isTampered ? (
            <span 
              style={{ 
                fontSize: '11px', 
                fontFamily: 'var(--font-mono)', 
                padding: '3px 8px', 
                borderRadius: '4px',
                background: isLight ? 'rgba(239, 68, 68, 0.1)' : 'rgba(239, 68, 68, 0.2)',
                color: '#EF4444',
                border: '1px solid #EF4444',
                fontWeight: 700,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <AlertTriangle size={12} />
              TAMPER ATTACK DETECTED · HASH CHAIN BROKEN
            </span>
          ) : (
            <span 
              style={{ 
                fontSize: '11px', 
                fontFamily: 'var(--font-mono)', 
                padding: '3px 8px', 
                borderRadius: '4px',
                background: isLight ? 'rgba(16, 185, 129, 0.1)' : 'rgba(34, 197, 94, 0.15)',
                color: isLight ? '#059669' : '#22C55E',
                border: `1px solid ${isLight ? 'rgba(16, 185, 129, 0.25)' : 'rgba(34, 197, 94, 0.3)'}`,
                fontWeight: 600,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <CheckCircle2 size={12} />
              IMMUTABLE DLT VERIFIED · 100% INCLUSION
            </span>
          )}
        </div>
      </div>

      {/* 2D SVG Block Chain */}
      <div style={{ width: '100%' }}>
        <svg viewBox="0 0 840 90" style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}>
          <defs>
            <linearGradient id="linkVerified" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10B981" />
              <stop offset="100%" stopColor="#10B981" />
            </linearGradient>
            <linearGradient id="linkTampered" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#EF4444" />
              <stop offset="100%" stopColor="#EF4444" />
            </linearGradient>
          </defs>

          {/* Connection Link Lines between blocks */}
          <line x1="180" y1="45" x2="225" y2="45" stroke={isTampered ? "#EF4444" : "#10B981"} strokeWidth="2.5" strokeDasharray={isTampered ? "4 4" : "none"} />
          <line x1="395" y1="45" x2="440" y2="45" stroke={isTampered ? "#EF4444" : "#10B981"} strokeWidth="2.5" strokeDasharray={isTampered ? "4 4" : "none"} />
          <line x1="610" y1="45" x2="655" y2="45" stroke={isTampered ? "#EF4444" : "#10B981"} strokeWidth="2.5" />

          {/* Blocks */}
          {blocks.map((block, i) => {
            const bx = 10 + i * 215;
            const by = 12;
            const bw = 170;
            const bh = 66;
            const isBlockBad = block.tampered;

            let cardBg = isLight ? "#FFFFFF" : "rgba(18, 22, 28, 0.9)";
            let cardBorder = isLight ? "#E2E8F0" : "rgba(255, 255, 255, 0.12)";
            if (isBlockBad) {
              cardBg = isLight ? "#FEF2F2" : "rgba(239, 68, 68, 0.15)";
              cardBorder = "#EF4444";
            }

            return (
              <g key={block.id}>
                {/* Block Card Rect */}
                <rect 
                  x={bx} y={by} width={bw} height={bh} rx="6"
                  fill={cardBg}
                  stroke={cardBorder}
                  strokeWidth={isBlockBad ? 2 : 1}
                />

                {/* Block Header Tab */}
                <rect 
                  x={bx} y={by} width={bw} height="20" rx="6"
                  fill={isBlockBad ? "rgba(239, 68, 68, 0.2)" : (isLight ? "#F1F5F9" : "rgba(255,255,255,0.06)")}
                />

                {/* Block Name */}
                <text 
                  x={bx + 8} y={by + 14}
                  fill={isBlockBad ? "#EF4444" : (isLight ? "#0F172A" : "#EDEDE8")}
                  fontSize="11"
                  fontWeight="bold"
                  fontFamily="sans-serif"
                >
                  Block #{block.id}: {block.name}
                </text>

                {/* Hash */}
                <text 
                  x={bx + 8} y={by + 36}
                  fill={isBlockBad ? "#EF4444" : (isLight ? "#475569" : "#9BA3AF")}
                  fontSize="10"
                  fontFamily="monospace"
                >
                  Hash: {block.hash}
                </text>

                {/* PrevHash */}
                <text 
                  x={bx + 8} y={by + 52}
                  fill={isBlockBad ? "#DC2626" : (isLight ? "#64748B" : "#64748B")}
                  fontSize="9.5"
                  fontFamily="monospace"
                >
                  Prev: {block.prevHash}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

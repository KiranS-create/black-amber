import React, { useState } from 'react';
import { Shield, Lock, Cpu, Zap, Database, ArrowRight } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export const SvgCryptographicLattice: React.FC = () => {
  const { theme } = useTheme();
  const isLight = theme === 'light';
  const [activeNode, setActiveNode] = useState<number>(0);

  const nodes = [
    {
      id: 0,
      title: 'Broadcast Envelope',
      std: 'NIST FIPS 203',
      tech: 'ML-KEM-768 + AES-GCM',
      details: 'Ring-LWE Lattice q=3329, k=3. Single ciphertext container broadcast to all N cleared recipients.',
      color: '#00D8F6',
      badgeColor: '#0284C7',
      status: 'PQC ENCRYPTED',
      type: 'broadcast'
    },
    {
      id: 1,
      title: 'Client WASM Enclave',
      std: 'Memory Isolation',
      tech: '64MB Private RAM',
      details: 'Unpaged linear memory enclave. Direct volatile raster watermark injection prior to pixel compositing.',
      color: '#A855F7',
      badgeColor: '#8B5CF6',
      status: 'AIR-GAPPED SHIELD',
      type: 'enclave'
    },
    {
      id: 2,
      title: 'Tardos DSSS Modulation',
      std: 'Traitor-Tracing',
      tech: '2D DCT Frequency Mark',
      details: 'Orthogonal Tardos codeword (m=128) embedded at zero perceptual degradation (PSNR 48.2 dB).',
      color: '#F59E0B',
      badgeColor: '#D97706',
      status: 'SPECTRAL MODULATION',
      type: 'dsss'
    },
    {
      id: 3,
      title: 'Immutable DLT Ledger',
      std: 'NIST FIPS 204',
      tech: 'ML-DSA-65 + RFC-6962',
      details: 'Hardware enclave signs decryption receipt H(P)||UID. Merkle tree committed before viewport unlocks.',
      color: '#10B981',
      badgeColor: '#059669',
      status: 'SEALED & PROVEN',
      type: 'ledger'
    },
  ];

  return (
    <div 
      className="glass-panel"
      style={{
        borderRadius: '12px',
        padding: '22px 24px',
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

      </div>

      {/* 2D SVG Pipeline Diagram with Clean Vector Nodes */}
      <div style={{ width: '100%', position: 'relative' }}>
        <svg 
          viewBox="0 0 880 145" 
          style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}
        >
          <defs>
            {/* Subtle 2D tinted fills */}
            <linearGradient id="laserBeam" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00D8F6" stopOpacity="0.8" />
              <stop offset="33%" stopColor="#A855F7" stopOpacity="0.8" />
              <stop offset="66%" stopColor="#F59E0B" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#10B981" stopOpacity="0.8" />
            </linearGradient>
          </defs>

          {/* Connection Cables / Transmission Lines */}
          <line 
            x1="110" y1="55" x2="330" y2="55" 
            stroke={isLight ? "#CBD5E1" : "rgba(255,255,255,0.15)"} 
            strokeWidth="2" 
            strokeDasharray="4 4" 
          />
          <line 
            x1="330" y1="55" x2="550" y2="55" 
            stroke={isLight ? "#CBD5E1" : "rgba(255,255,255,0.15)"} 
            strokeWidth="2" 
            strokeDasharray="4 4" 
          />
          <line 
            x1="550" y1="55" x2="770" y2="55" 
            stroke={isLight ? "#CBD5E1" : "rgba(255,255,255,0.15)"} 
            strokeWidth="2" 
            strokeDasharray="4 4" 
          />

          {/* Flowing Laser Signal Conduit */}
          <line 
            x1="110" y1="55" x2="770" y2="55" 
            stroke="url(#laserBeam)" 
            strokeWidth="1.5" 
            strokeOpacity={isLight ? "0.35" : "0.55"}
          />

          {/* Moving 2D Laser Photon Pulses along the line */}
          <circle cy="55" r="3.5" fill="#00D8F6">
            <animate attributeName="cx" values="110;330" dur="2s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite" />
          </circle>

          <circle cy="55" r="3.5" fill="#C084FC">
            <animate attributeName="cx" values="330;550" dur="2s" begin="0.65s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" begin="0.65s" repeatCount="indefinite" />
          </circle>

          <circle cy="55" r="3.5" fill="#34D399">
            <animate attributeName="cx" values="550;770" dur="2s" begin="1.3s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" begin="1.3s" repeatCount="indefinite" />
          </circle>

          {/* ==================== NODE 1: 2D Broadcast Envelope ==================== */}
          <g onClick={() => setActiveNode(0)} style={{ cursor: 'pointer' }}>
            {/* 2D Expanding Radar Ripples */}
            <circle cx="110" cy="55" r="28" fill="none" stroke="#00D8F6" strokeWidth="1.2">
              <animate attributeName="r" values="23;34;44" dur="2.4s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.7;0.25;0" dur="2.4s" repeatCount="indefinite" />
            </circle>

            {/* Active Rotating Vector Ring */}
            {activeNode === 0 && (
              <circle cx="110" cy="55" r="29" fill="none" stroke="#00D8F6" strokeWidth="1" strokeDasharray="3 3">
                <animateTransform attributeName="transform" type="rotate" from="0 110 55" to="360 110 55" dur="10s" repeatCount="indefinite" />
              </circle>
            )}

            {/* 2D Flat Disc */}
            <circle 
              cx="110" cy="55" r={activeNode === 0 ? 23 : 21}
              fill={isLight ? (activeNode === 0 ? "#F0F9FF" : "#FFFFFF") : (activeNode === 0 ? "#0C1E30" : "#111620")}
              stroke="#00D8F6"
              strokeWidth={activeNode === 0 ? "2.5" : "1.8"}
            />

            {/* Concentric 2D Inner Ring */}
            <circle cx="110" cy="55" r="14" fill="none" stroke="#00D8F6" strokeWidth="1" strokeDasharray="2 2" opacity="0.6" />

            {/* Step Number Badge */}
            <circle cx="127" cy="38" r="8.5" fill="#0284C7" stroke={isLight ? "#FFFFFF" : "#090C0F"} strokeWidth="1.5" />
            <text x="127" y="41" textAnchor="middle" fill="#FFFFFF" fontSize="9.5" fontWeight="bold" fontFamily="sans-serif">1</text>

            {/* Label */}
            <text x="110" y="98" textAnchor="middle" fill={isLight ? "#0F172A" : "#EDEDE8"} fontSize="12" fontWeight="600" fontFamily="sans-serif">
              Broadcast Envelope
            </text>
            <text x="110" y="112" textAnchor="middle" fill={isLight ? "#475569" : "#9BA3AF"} fontSize="10" fontFamily="monospace">
              ML-KEM-768 + AES-GCM
            </text>
          </g>

          {/* ==================== NODE 2: 2D Client WASM Enclave ==================== */}
          <g onClick={() => setActiveNode(1)} style={{ cursor: 'pointer' }}>
            {/* 2D Rotating Dashed Orbit Ring */}
            <circle cx="330" cy="55" r="29" fill="none" stroke="#C084FC" strokeWidth="1.2" strokeDasharray="4 3">
              <animateTransform attributeName="transform" type="rotate" from="0 330 55" to="360 330 55" dur="12s" repeatCount="indefinite" />
            </circle>

            {/* 2D Flat Disc */}
            <circle 
              cx="330" cy="55" r={activeNode === 1 ? 23 : 21}
              fill={isLight ? (activeNode === 1 ? "#FAF5FF" : "#FFFFFF") : (activeNode === 1 ? "#1D1030" : "#111620")}
              stroke="#A855F7"
              strokeWidth={activeNode === 1 ? "2.5" : "1.8"}
            />

            {/* Concentric 2D Inner Ring */}
            <circle cx="330" cy="55" r="14" fill="none" stroke="#C084FC" strokeWidth="1" strokeDasharray="2 2" opacity="0.6" />

            {/* Step Number Badge */}
            <circle cx="347" cy="38" r="8.5" fill="#8B5CF6" stroke={isLight ? "#FFFFFF" : "#090C0F"} strokeWidth="1.5" />
            <text x="347" y="41" textAnchor="middle" fill="#FFFFFF" fontSize="9.5" fontWeight="bold" fontFamily="sans-serif">2</text>

            {/* Label */}
            <text x="330" y="98" textAnchor="middle" fill={isLight ? "#0F172A" : "#EDEDE8"} fontSize="12" fontWeight="600" fontFamily="sans-serif">
              Client WASM Enclave
            </text>
            <text x="330" y="112" textAnchor="middle" fill={isLight ? "#475569" : "#9BA3AF"} fontSize="10" fontFamily="monospace">
              64MB Private RAM
            </text>
          </g>

          {/* ==================== NODE 3: 2D Tardos DSSS Modulation ==================== */}
          <g onClick={() => setActiveNode(2)} style={{ cursor: 'pointer' }}>
            {/* 2D Spectral Frequency Ring */}
            <circle cx="550" cy="55" r="29" fill="none" stroke="#FBBF24" strokeWidth="1.2" strokeDasharray="5 3">
              <animateTransform attributeName="transform" type="rotate" from="360 550 55" to="0 550 55" dur="10s" repeatCount="indefinite" />
            </circle>

            {/* 2D Flat Disc */}
            <circle 
              cx="550" cy="55" r={activeNode === 2 ? 23 : 21}
              fill={isLight ? (activeNode === 2 ? "#FFFBEB" : "#FFFFFF") : (activeNode === 2 ? "#261908" : "#111620")}
              stroke="#F59E0B"
              strokeWidth={activeNode === 2 ? "2.5" : "1.8"}
            />

            {/* Concentric 2D Inner Ring */}
            <circle cx="550" cy="55" r="14" fill="none" stroke="#F59E0B" strokeWidth="1" strokeDasharray="2 2" opacity="0.6" />

            {/* Step Number Badge */}
            <circle cx="567" cy="38" r="8.5" fill="#D97706" stroke={isLight ? "#FFFFFF" : "#090C0F"} strokeWidth="1.5" />
            <text x="567" y="41" textAnchor="middle" fill="#FFFFFF" fontSize="9.5" fontWeight="bold" fontFamily="sans-serif">3</text>

            {/* Label */}
            <text x="550" y="98" textAnchor="middle" fill={isLight ? "#0F172A" : "#EDEDE8"} fontSize="12" fontWeight="600" fontFamily="sans-serif">
              Tardos DSSS Modulation
            </text>
            <text x="550" y="112" textAnchor="middle" fill={isLight ? "#475569" : "#9BA3AF"} fontSize="10" fontFamily="monospace">
              2D DCT Frequency Mark
            </text>
          </g>

          {/* ==================== NODE 4: 2D Immutable DLT Ledger ==================== */}
          <g onClick={() => setActiveNode(3)} style={{ cursor: 'pointer' }}>
            {/* 2D Rotating Concentric Verification Ring */}
            <circle cx="770" cy="55" r="29" fill="none" stroke="#34D399" strokeWidth="1.2" strokeDasharray="6 3">
              <animateTransform attributeName="transform" type="rotate" from="0 770 55" to="360 770 55" dur="8s" repeatCount="indefinite" />
            </circle>

            {/* 2D Flat Disc */}
            <circle 
              cx="770" cy="55" r={activeNode === 3 ? 23 : 21}
              fill={isLight ? (activeNode === 3 ? "#ECFDF5" : "#FFFFFF") : (activeNode === 3 ? "#0D241B" : "#111620")}
              stroke="#10B981"
              strokeWidth={activeNode === 3 ? "2.5" : "1.8"}
            />

            {/* Concentric 2D Inner Ring */}
            <circle cx="770" cy="55" r="14" fill="none" stroke="#10B981" strokeWidth="1" strokeDasharray="2 2" opacity="0.6" />

            {/* Step Number Badge */}
            <circle cx="787" cy="38" r="8.5" fill="#059669" stroke={isLight ? "#FFFFFF" : "#090C0F"} strokeWidth="1.5" />
            <text x="787" y="41" textAnchor="middle" fill="#FFFFFF" fontSize="9.5" fontWeight="bold" fontFamily="sans-serif">4</text>

            {/* Label */}
            <text x="770" y="98" textAnchor="middle" fill={isLight ? "#0F172A" : "#EDEDE8"} fontSize="12" fontWeight="600" fontFamily="sans-serif">
              Immutable DLT Ledger
            </text>
            <text x="770" y="112" textAnchor="middle" fill={isLight ? "#475569" : "#9BA3AF"} fontSize="10" fontFamily="monospace">
              ML-DSA-65 + RFC-6962
            </text>
          </g>
        </svg>
      </div>

      {/* Interactive Detail Inspector Strip */}
      <div 
        style={{ 
          marginTop: '10px', 
          padding: '12px 16px', 
          borderRadius: '8px', 
          background: isLight ? '#F1F5F9' : 'rgba(18, 22, 27, 0.75)', 
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
              background: nodes[activeNode].badgeColor, 
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

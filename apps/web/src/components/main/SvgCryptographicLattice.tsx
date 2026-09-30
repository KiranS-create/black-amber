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

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span 
            style={{ 
              fontSize: '11px', 
              fontFamily: 'var(--font-mono)', 
              padding: '3px 9px', 
              borderRadius: '4px',
              background: isLight ? 'rgba(16, 185, 129, 0.12)' : 'rgba(34, 197, 94, 0.15)',
              color: isLight ? '#059669' : '#22C55E',
              border: `1px solid ${isLight ? 'rgba(16, 185, 129, 0.25)' : 'rgba(34, 197, 94, 0.3)'}`,
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: isLight ? '#059669' : '#22C55E' }} />
            ACTIVE KERNEL • ANIMATED FUSION ORBS
          </span>
        </div>
      </div>

      {/* 2D SVG Pipeline Diagram with Animated Fusion Orbs */}
      <div style={{ width: '100%', position: 'relative' }}>
        <svg 
          viewBox="0 0 880 145" 
          style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}
        >
          <defs>
            {/* Gradients for Node 1: Electric Cyan Radar Orb */}
            <radialGradient id="orbGrad1Dark" cx="40%" cy="35%" r="65%">
              <stop offset="0%" stopColor="#E0F7FF" />
              <stop offset="35%" stopColor="#00D8F6" />
              <stop offset="75%" stopColor="#0284C7" />
              <stop offset="100%" stopColor="#062238" />
            </radialGradient>
            <radialGradient id="orbGrad1Light" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stopColor="#FFFFFF" />
              <stop offset="30%" stopColor="#BAE6FD" />
              <stop offset="70%" stopColor="#0284C7" />
              <stop offset="100%" stopColor="#0369A1" />
            </radialGradient>

            {/* Gradients for Node 2: Violet/Purple Magnetic Enclave */}
            <radialGradient id="orbGrad2Dark" cx="40%" cy="35%" r="65%">
              <stop offset="0%" stopColor="#F5EDFF" />
              <stop offset="35%" stopColor="#C084FC" />
              <stop offset="75%" stopColor="#7E22CE" />
              <stop offset="100%" stopColor="#25093D" />
            </radialGradient>
            <radialGradient id="orbGrad2Light" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stopColor="#FFFFFF" />
              <stop offset="30%" stopColor="#DDD6FE" />
              <stop offset="70%" stopColor="#8B5CF6" />
              <stop offset="100%" stopColor="#6D28D9" />
            </radialGradient>

            {/* Gradients for Node 3: Amber/Gold Harmonic Spectral Emitter */}
            <radialGradient id="orbGrad3Dark" cx="40%" cy="35%" r="65%">
              <stop offset="0%" stopColor="#FFFBEB" />
              <stop offset="35%" stopColor="#FBBF24" />
              <stop offset="75%" stopColor="#D97706" />
              <stop offset="100%" stopColor="#3B1E04" />
            </radialGradient>
            <radialGradient id="orbGrad3Light" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stopColor="#FFFFFF" />
              <stop offset="30%" stopColor="#FED7AA" />
              <stop offset="70%" stopColor="#F59E0B" />
              <stop offset="100%" stopColor="#B45309" />
            </radialGradient>

            {/* Gradients for Node 4: Emerald Green Cryptographic Seal */}
            <radialGradient id="orbGrad4Dark" cx="40%" cy="35%" r="65%">
              <stop offset="0%" stopColor="#ECFDF5" />
              <stop offset="35%" stopColor="#34D399" />
              <stop offset="75%" stopColor="#059669" />
              <stop offset="100%" stopColor="#062D1F" />
            </radialGradient>
            <radialGradient id="orbGrad4Light" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stopColor="#FFFFFF" />
              <stop offset="30%" stopColor="#A7F3D0" />
              <stop offset="70%" stopColor="#10B981" />
              <stop offset="100%" stopColor="#047857" />
            </radialGradient>

            {/* Dynamic Drop Shadows & Glow Filters */}
            <filter id="orbGlowDark" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="orbGlowLight" x="-30%" y="-30%" width="160%" height="160%">
              <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#0F172A" floodOpacity="0.12" />
            </filter>

            {/* Laser Line Gradient */}
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
            stroke={isLight ? "#E2E8F0" : "rgba(255,255,255,0.12)"} 
            strokeWidth="3" 
            strokeDasharray="4 4" 
          />
          <line 
            x1="330" y1="55" x2="550" y2="55" 
            stroke={isLight ? "#E2E8F0" : "rgba(255,255,255,0.12)"} 
            strokeWidth="3" 
            strokeDasharray="4 4" 
          />
          <line 
            x1="550" y1="55" x2="770" y2="55" 
            stroke={isLight ? "#E2E8F0" : "rgba(255,255,255,0.12)"} 
            strokeWidth="3" 
            strokeDasharray="4 4" 
          />

          {/* Flowing Laser Signal Conduit */}
          <line 
            x1="110" y1="55" x2="770" y2="55" 
            stroke="url(#laserBeam)" 
            strokeWidth="1.5" 
            strokeOpacity={isLight ? "0.4" : "0.6"}
          />

          {/* Moving Laser Photon Pulses along the line */}
          {/* Pulse 1: Node 1 -> Node 2 */}
          <circle cy="55" r="4" fill="#00D8F6" opacity="0.9">
            <animate attributeName="cx" values="110;330" dur="2s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.2;1;0.2" dur="2s" repeatCount="indefinite" />
          </circle>

          {/* Pulse 2: Node 2 -> Node 3 */}
          <circle cy="55" r="4" fill="#C084FC" opacity="0.9">
            <animate attributeName="cx" values="330;550" dur="2s" begin="0.65s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.2;1;0.2" dur="2s" begin="0.65s" repeatCount="indefinite" />
          </circle>

          {/* Pulse 3: Node 3 -> Node 4 */}
          <circle cy="55" r="4" fill="#34D399" opacity="0.9">
            <animate attributeName="cx" values="550;770" dur="2s" begin="1.3s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.2;1;0.2" dur="2s" begin="1.3s" repeatCount="indefinite" />
          </circle>

          {/* ==================== NODE 1: Electric Cyan Radar Orb ==================== */}
          <g onClick={() => setActiveNode(0)} style={{ cursor: 'pointer' }}>
            {/* Expanding Radar Ripples */}
            <circle cx="110" cy="55" r="28" fill="none" stroke="#00D8F6" strokeWidth="1.5">
              <animate attributeName="r" values="24;36;46" dur="2.4s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.8;0.3;0" dur="2.4s" repeatCount="indefinite" />
            </circle>
            <circle cx="110" cy="55" r="28" fill="none" stroke="#00D8F6" strokeWidth="1">
              <animate attributeName="r" values="24;36;46" dur="2.4s" begin="1.2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.8;0.3;0" dur="2.4s" begin="1.2s" repeatCount="indefinite" />
            </circle>

            {/* Glowing Core Sphere */}
            <circle 
              cx="110" cy="55" r={activeNode === 0 ? 25 : 22}
              fill={isLight ? "url(#orbGrad1Light)" : "url(#orbGrad1Dark)"}
              stroke="#00D8F6"
              strokeWidth={activeNode === 0 ? "2.5" : "1.5"}
              filter={isLight ? "url(#orbGlowLight)" : "url(#orbGlowDark)"}
            />

            {/* Optical Glass Specular Highlight (Light mode 3D sphere depth) */}
            <ellipse cx="104" cy="48" rx="8" ry="4" fill="#FFFFFF" opacity={isLight ? "0.6" : "0.35"} />

            {/* Step Number Badge */}
            <circle cx="128" cy="37" r="9" fill="#0284C7" stroke={isLight ? "#FFFFFF" : "#090C0F"} strokeWidth="1.5" />
            <text x="128" y="40.5" textAnchor="middle" fill="#FFFFFF" fontSize="10" fontWeight="bold" fontFamily="sans-serif">1</text>

            {/* Label */}
            <text x="110" y="98" textAnchor="middle" fill={isLight ? "#0F172A" : "#EDEDE8"} fontSize="12" fontWeight="600" fontFamily="sans-serif">
              Broadcast Envelope
            </text>
            <text x="110" y="112" textAnchor="middle" fill={isLight ? "#475569" : "#9BA3AF"} fontSize="10" fontFamily="monospace">
              ML-KEM-768 + AES-GCM
            </text>
          </g>

          {/* ==================== NODE 2: Violet/Purple Magnetic Enclave ==================== */}
          <g onClick={() => setActiveNode(1)} style={{ cursor: 'pointer' }}>
            {/* Magnetic Containment Shield Ring (Pulsing stroke) */}
            <circle cx="330" cy="55" r="32" fill="none" stroke="#C084FC" strokeDasharray="3 3">
              <animate attributeName="stroke-width" values="1;2.5;1" dur="2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.4;0.9;0.4" dur="2s" repeatCount="indefinite" />
              <animateTransform attributeName="transform" type="rotate" from="0 330 55" to="360 330 55" dur="12s" repeatCount="indefinite" />
            </circle>

            {/* Glowing Core Sphere */}
            <circle 
              cx="330" cy="55" r={activeNode === 1 ? 25 : 22}
              fill={isLight ? "url(#orbGrad2Light)" : "url(#orbGrad2Dark)"}
              stroke="#A855F7"
              strokeWidth={activeNode === 1 ? "2.5" : "1.5"}
              filter={isLight ? "url(#orbGlowLight)" : "url(#orbGlowDark)"}
            />

            {/* Specular Highlight */}
            <ellipse cx="324" cy="48" rx="8" ry="4" fill="#FFFFFF" opacity={isLight ? "0.6" : "0.35"} />

            {/* Step Number Badge */}
            <circle cx="348" cy="37" r="9" fill="#8B5CF6" stroke={isLight ? "#FFFFFF" : "#090C0F"} strokeWidth="1.5" />
            <text x="348" y="40.5" textAnchor="middle" fill="#FFFFFF" fontSize="10" fontWeight="bold" fontFamily="sans-serif">2</text>

            {/* Label */}
            <text x="330" y="98" textAnchor="middle" fill={isLight ? "#0F172A" : "#EDEDE8"} fontSize="12" fontWeight="600" fontFamily="sans-serif">
              Client WASM Enclave
            </text>
            <text x="330" y="112" textAnchor="middle" fill={isLight ? "#475569" : "#9BA3AF"} fontSize="10" fontFamily="monospace">
              64MB Private RAM
            </text>
          </g>

          {/* ==================== NODE 3: Amber/Gold Harmonic Emitter ==================== */}
          <g onClick={() => setActiveNode(2)} style={{ cursor: 'pointer' }}>
            {/* Oscillating Spectral Frequency Bands */}
            <ellipse cx="550" cy="55" rx="30" ry="18" fill="none" stroke="#FBBF24" strokeWidth="1.2">
              <animate attributeName="rx" values="26;34;26" dur="2.2s" repeatCount="indefinite" />
              <animate attributeName="ry" values="16;22;16" dur="2.2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2.2s" repeatCount="indefinite" />
            </ellipse>
            <ellipse cx="550" cy="55" rx="18" ry="30" fill="none" stroke="#F59E0B" strokeWidth="1.2">
              <animate attributeName="rx" values="16;22;16" dur="2.2s" repeatCount="indefinite" />
              <animate attributeName="ry" values="26;34;26" dur="2.2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2.2s" repeatCount="indefinite" />
            </ellipse>

            {/* Glowing Core Sphere */}
            <circle 
              cx="550" cy="55" r={activeNode === 2 ? 25 : 22}
              fill={isLight ? "url(#orbGrad3Light)" : "url(#orbGrad3Dark)"}
              stroke="#F59E0B"
              strokeWidth={activeNode === 2 ? "2.5" : "1.5"}
              filter={isLight ? "url(#orbGlowLight)" : "url(#orbGlowDark)"}
            />

            {/* Specular Highlight */}
            <ellipse cx="544" cy="48" rx="8" ry="4" fill="#FFFFFF" opacity={isLight ? "0.6" : "0.35"} />

            {/* Step Number Badge */}
            <circle cx="568" cy="37" r="9" fill="#D97706" stroke={isLight ? "#FFFFFF" : "#090C0F"} strokeWidth="1.5" />
            <text x="568" y="40.5" textAnchor="middle" fill="#FFFFFF" fontSize="10" fontWeight="bold" fontFamily="sans-serif">3</text>

            {/* Label */}
            <text x="550" y="98" textAnchor="middle" fill={isLight ? "#0F172A" : "#EDEDE8"} fontSize="12" fontWeight="600" fontFamily="sans-serif">
              Tardos DSSS Modulation
            </text>
            <text x="550" y="112" textAnchor="middle" fill={isLight ? "#475569" : "#9BA3AF"} fontSize="10" fontFamily="monospace">
              2D DCT Frequency Mark
            </text>
          </g>

          {/* ==================== NODE 4: Emerald Green Cryptographic Seal ==================== */}
          <g onClick={() => setActiveNode(3)} style={{ cursor: 'pointer' }}>
            {/* Rotating Concentric Verification Rings */}
            <circle cx="770" cy="55" r="32" fill="none" stroke="#34D399" strokeWidth="1.5" strokeDasharray="5 3">
              <animateTransform attributeName="transform" type="rotate" from="0 770 55" to="360 770 55" dur="8s" repeatCount="indefinite" />
            </circle>
            <circle cx="770" cy="55" r="36" fill="none" stroke="#10B981" strokeWidth="1" strokeDasharray="8 4" opacity="0.6">
              <animateTransform attributeName="transform" type="rotate" from="360 770 55" to="0 770 55" dur="14s" repeatCount="indefinite" />
            </circle>

            {/* Glowing Core Sphere */}
            <circle 
              cx="770" cy="55" r={activeNode === 3 ? 25 : 22}
              fill={isLight ? "url(#orbGrad4Light)" : "url(#orbGrad4Dark)"}
              stroke="#10B981"
              strokeWidth={activeNode === 3 ? "2.5" : "1.5"}
              filter={isLight ? "url(#orbGlowLight)" : "url(#orbGlowDark)"}
            />

            {/* Specular Highlight */}
            <ellipse cx="764" cy="48" rx="8" ry="4" fill="#FFFFFF" opacity={isLight ? "0.6" : "0.35"} />

            {/* Step Number Badge */}
            <circle cx="788" cy="37" r="9" fill="#059669" stroke={isLight ? "#FFFFFF" : "#090C0F"} strokeWidth="1.5" />
            <text x="788" y="40.5" textAnchor="middle" fill="#FFFFFF" fontSize="10" fontWeight="bold" fontFamily="sans-serif">4</text>

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

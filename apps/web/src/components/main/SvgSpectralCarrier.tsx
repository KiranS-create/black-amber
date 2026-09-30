import React, { useState } from 'react';
import { Activity, Layers, Zap, Info } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export const SvgSpectralCarrier: React.FC = () => {
  const { theme } = useTheme();
  const isLight = theme === 'light';
  const [selectedFreq, setSelectedFreq] = useState<number>(14);

  // Generate 8x8 DCT grid coefficients
  const dctGrid = Array.from({ length: 64 }, (_, i) => {
    const row = Math.floor(i / 8);
    const col = i % 8;
    const isDc = row === 0 && col === 0;
    const isMidBand = (row + col >= 3) && (row + col <= 8);
    const energy = isDc ? 0.95 : isMidBand ? 0.35 + Math.sin(i * 1.7) * 0.25 : 0.08 + Math.cos(i) * 0.05;
    return { id: i, row, col, isDc, isMidBand, energy: Math.max(0.05, Math.min(0.98, energy)) };
  });

  return (
    <div 
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        padding: '16px',
        borderRadius: '8px',
        background: isLight ? '#FFFFFF' : 'rgba(18, 22, 28, 0.85)',
        border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255, 255, 255, 0.08)'}`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={16} color="#0284C7" />
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
            2D Discrete Cosine Transform (DCT) Spectral Carrier Surface
          </span>
        </div>
        <span 
          style={{ 
            fontSize: '11px', 
            fontFamily: 'var(--font-mono)', 
            padding: '2px 8px', 
            borderRadius: '4px',
            background: isLight ? 'rgba(2, 132, 199, 0.1)' : 'rgba(56, 189, 248, 0.15)',
            color: '#0284C7',
            fontWeight: 600
          }}
        >
          MID-BAND EMBEDDING: PSNR 48.2 dB
        </span>
      </div>

      {/* 2D SVG Spectral Heatmap & Spectrum */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'center' }}>
        {/* 8x8 DCT Block Matrix */}
        <div>
          <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginBottom: '8px', fontWeight: 500 }}>
            8x8 Block Frequency Quantization Matrix:
          </div>
          <svg viewBox="0 0 240 240" style={{ width: '100%', maxWidth: '240px', height: 'auto', display: 'block' }}>
            {dctGrid.map((cell) => {
              const x = cell.col * 30;
              const y = cell.row * 30;
              const isSelected = selectedFreq === cell.id;

              // Color gradient: DC is amber, mid-band is cyan/petrol, high-freq is deep slate
              let fill = isLight ? "#F1F5F9" : "#1A212B";
              if (cell.isDc) {
                fill = isLight ? "#FEF3C7" : "rgba(245, 158, 11, 0.35)";
              } else if (cell.isMidBand) {
                fill = isLight ? `rgba(2, 132, 199, ${cell.energy * 0.6 + 0.1})` : `rgba(56, 189, 248, ${cell.energy * 0.8 + 0.15})`;
              }

              return (
                <rect
                  key={cell.id}
                  x={x + 1}
                  y={y + 1}
                  width="28"
                  height="28"
                  rx="3"
                  fill={fill}
                  stroke={isSelected ? "#0284C7" : (isLight ? "#E2E8F0" : "rgba(255,255,255,0.08)")}
                  strokeWidth={isSelected ? 2 : 1}
                  onClick={() => setSelectedFreq(cell.id)}
                  style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
                />
              );
            })}
          </svg>
        </div>

        {/* Frequency Band Spectrum Meter */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', fontWeight: 500 }}>
            Carrier Energy Distribution across Frequency Bins:
          </div>

          {[
            { label: 'DC Component (0,0)', val: '95.2%', note: 'Preserved (Zero Modification)', color: '#F59E0B' },
            { label: 'Low-Frequency (1-2)', val: '12.4%', note: 'Visual Barrier Threshold', color: isLight ? '#64748B' : '#9BA3AF' },
            { label: 'Mid-Frequency (3-8)', val: '88.6%', note: 'Tardos DSSS Carrier Active', color: '#0284C7' },
            { label: 'High-Frequency (9-15)', val: '4.1%', note: 'JPEG Quantization Resilient', color: isLight ? '#64748B' : '#9BA3AF' },
          ].map((item, idx) => (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                <span style={{ color: 'var(--main-text-primary)', fontWeight: 600 }}>{item.label}</span>
                <span style={{ color: item.color, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{item.val}</span>
              </div>
              <div style={{ width: '100%', height: '6px', borderRadius: '3px', background: isLight ? '#E2E8F0' : 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                <div style={{ width: item.val, height: '100%', background: item.color, borderRadius: '3px' }} />
              </div>
              <span style={{ fontSize: '10px', color: 'var(--main-text-tertiary)' }}>{item.note}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Info */}
      <div 
        style={{ 
          fontSize: '11px', 
          color: 'var(--main-text-secondary)', 
          background: isLight ? '#F8FAFC' : 'rgba(9, 12, 16, 0.5)', 
          padding: '8px 12px', 
          borderRadius: '6px',
          border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255, 255, 255, 0.05)'}`,
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}
      >
        <Zap size={14} color="#0284C7" />
        <span>
          <strong>DSSS Modulation:</strong> Tardos pseudo-noise chips modulate mid-frequency 2D DCT bins, surviving JPEG Q=10 and physical print-scan while remaining imperceptible to the human eye.
        </span>
      </div>
    </div>
  );
};

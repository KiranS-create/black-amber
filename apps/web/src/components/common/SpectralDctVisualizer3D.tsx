import React, { useEffect, useRef } from 'react';

interface SpectralDctVisualizer3DProps {
  distortionType: string;
  intensity: number;
}

export const SpectralDctVisualizer3D: React.FC<SpectralDctVisualizer3DProps> = ({
  distortionType,
  intensity
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let frame = 0;

    const render = () => {
      frame++;
      const w = canvas.width;
      const h = canvas.height;

      // Dark spectral background
      ctx.fillStyle = '#0B0F17';
      ctx.fillRect(0, 0, w, h);

      // Grid Lines
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.12)';
      ctx.lineWidth = 1;
      const gridSize = 24;
      for (let x = 0; x < w; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Draw 3D DCT Spectral Waves
      const bars = 32;
      const barWidth = (w - 40) / bars;

      for (let i = 0; i < bars; i++) {
        const factor = Math.sin((i / bars) * Math.PI * 2 + frame * 0.05);
        const noise = (Math.random() - 0.5) * (intensity / 100) * 15;
        const baseH = (h * 0.4) * (1 - (i / bars) * 0.5);
        const barHeight = Math.max(8, baseH + factor * 20 + noise);

        const x = 20 + i * barWidth;
        const y = h - 25 - barHeight;

        // Gradient based on distortion
        const grad = ctx.createLinearGradient(x, y, x, h - 25);
        if (distortionType === 'noise' || distortionType === 'jpeg') {
          grad.addColorStop(0, '#EF4444');
          grad.addColorStop(0.5, '#F59E0B');
          grad.addColorStop(1, '#3B82F6');
        } else {
          grad.addColorStop(0, '#38BDF8');
          grad.addColorStop(0.6, '#6366F1');
          grad.addColorStop(1, '#1E1B4B');
        }

        ctx.fillStyle = grad;
        ctx.fillRect(x, y, barWidth - 3, barHeight);

        // Cap highlight
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.fillRect(x, y, barWidth - 3, 2);
      }

      // Metadata labels
      ctx.fillStyle = '#94A3B8';
      ctx.font = '10px monospace';
      ctx.fillText(`DCT FREQUENCY ENERGY | MODALITY: ${distortionType.toUpperCase()}`, 20, 18);
      ctx.fillText(`PERTURBATION: ${intensity.toFixed(1)}%`, w - 160, 18);

      animationId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [distortionType, intensity]);

  return (
    <div style={{ width: '100%', height: '100%', minHeight: '260px', position: 'relative', overflow: 'hidden', borderRadius: '6px' }}>
      <canvas
        ref={canvasRef}
        width={640}
        height={260}
        style={{ width: '100%', height: '100%', display: 'block', backgroundColor: '#0B0F17' }}
      />
    </div>
  );
};

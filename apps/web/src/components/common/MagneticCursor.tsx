import React, { useEffect, useState, useRef } from 'react';
import { useTheme } from '../../context/ThemeContext';

interface MagneticCursorProps {
  className?: string;
}

export const MagneticCursor: React.FC<MagneticCursorProps> = ({ className = '' }) => {
  const { theme } = useTheme();
  const isLight = theme === 'light';

  const [mousePos, setMousePos] = useState<{ x: number; y: number }>({ x: -100, y: -100 });
  const [isVisible, setIsVisible] = useState(false);
  const [isHoveringInteractive, setIsHoveringInteractive] = useState(false);
  const [isClicking, setIsClicking] = useState(false);
  const [isTouchDevice, setIsTouchDevice] = useState(false);

  const cursorDotRef = useRef<HTMLDivElement>(null);
  const cursorRingRef = useRef<HTMLDivElement>(null);

  const currentPos = useRef<{ x: number; y: number }>({ x: -100, y: -100 });
  const targetPos = useRef<{ x: number; y: number }>({ x: -100, y: -100 });
  const animFrameId = useRef<number | null>(null);

  useEffect(() => {
    // Detect touch-only devices to avoid intrusive cursor on mobile
    if (window.matchMedia('(pointer: coarse)').matches) {
      setIsTouchDevice(true);
      return;
    }

    const handleMouseMove = (e: MouseEvent) => {
      targetPos.current = { x: e.clientX, y: e.clientY };
      if (!isVisible) setIsVisible(true);

      // Check if hovering interactive target
      const target = e.target as HTMLElement | null;
      if (target) {
        const isInteractive = !!target.closest(
          'button, a, input, select, textarea, [role="button"], .interactive-target, .workstation-card, [data-interactive="true"]'
        );
        setIsHoveringInteractive(isInteractive);
      }
    };

    const handleMouseDown = () => setIsClicking(true);
    const handleMouseUp = () => setIsClicking(false);
    const handleMouseLeave = () => setIsVisible(false);
    const handleMouseEnter = () => setIsVisible(true);

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('mouseenter', handleMouseEnter);

    // Smooth lerp loop for fluid organic tracking
    const updateCursor = () => {
      const ease = 0.18; // smooth lag
      currentPos.current.x += (targetPos.current.x - currentPos.current.x) * ease;
      currentPos.current.y += (targetPos.current.y - currentPos.current.y) * ease;

      if (cursorDotRef.current) {
        cursorDotRef.current.style.transform = `translate3d(${targetPos.current.x}px, ${targetPos.current.y}px, 0) translate(-50%, -50%)`;
      }

      if (cursorRingRef.current) {
        cursorRingRef.current.style.transform = `translate3d(${currentPos.current.x}px, ${currentPos.current.y}px, 0) translate(-50%, -50%)`;
      }

      animFrameId.current = requestAnimationFrame(updateCursor);
    };

    animFrameId.current = requestAnimationFrame(updateCursor);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('mouseenter', handleMouseEnter);
      if (animFrameId.current) cancelAnimationFrame(animFrameId.current);
    };
  }, [isVisible]);

  if (isTouchDevice || !isVisible) return null;

  const primaryColor = isLight ? '#0284C7' : '#38BDF8';
  const ringBorder = isLight 
    ? (isHoveringInteractive ? 'rgba(2, 132, 199, 0.75)' : 'rgba(2, 132, 199, 0.45)') 
    : (isHoveringInteractive ? 'rgba(56, 189, 248, 0.85)' : 'rgba(56, 189, 248, 0.50)');
  const ringBg = isLight
    ? (isHoveringInteractive ? 'rgba(2, 132, 199, 0.08)' : 'rgba(2, 132, 199, 0.03)')
    : (isHoveringInteractive ? 'rgba(56, 189, 248, 0.12)' : 'rgba(56, 189, 248, 0.04)');

  const ringScale = isClicking ? 0.85 : isHoveringInteractive ? 1.55 : 1.0;

  return (
    <div
      className={`magnetic-cursor-container ${className}`}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 9999,
        overflow: 'hidden'
      }}
      aria-hidden="true"
    >
      {/* Outer Magnetic Halo Ring */}
      <div
        ref={cursorRingRef}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          border: `1.5px solid ${ringBorder}`,
          backgroundColor: ringBg,
          boxShadow: isLight
            ? (isHoveringInteractive ? '0 0 16px rgba(2, 132, 199, 0.35)' : '0 0 8px rgba(2, 132, 199, 0.15)')
            : (isHoveringInteractive ? '0 0 20px rgba(56, 189, 248, 0.45)' : '0 0 10px rgba(56, 189, 248, 0.20)'),
          transition: 'width 0.2s ease, height 0.2s ease, border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease, transform 0.04s linear',
          transformOrigin: 'center center',
          scale: `${ringScale}`,
          willChange: 'transform'
        }}
      />

      {/* Center Laser Focus Dot */}
      <div
        ref={cursorDotRef}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: isHoveringInteractive ? '5px' : '4px',
          height: isHoveringInteractive ? '5px' : '4px',
          borderRadius: '50%',
          backgroundColor: primaryColor,
          boxShadow: `0 0 8px ${primaryColor}`,
          transition: 'width 0.15s ease, height 0.15s ease, background-color 0.2s ease',
          transformOrigin: 'center center',
          willChange: 'transform'
        }}
      />
    </div>
  );
};

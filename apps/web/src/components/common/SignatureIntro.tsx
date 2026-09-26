import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck } from 'lucide-react';

interface SignatureIntroProps {
  onComplete: () => void;
}

export const SignatureIntro: React.FC<SignatureIntroProps> = ({ onComplete }) => {
  const [stage, setStage] = useState<'line' | 'resolve' | 'finish'>('line');

  useEffect(() => {
    // Check for reduced motion preference
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      onComplete();
      return;
    }

    // Sequence timing: ~950ms total
    // Stage 1: Trace line draws across (0 - 350ms)
    // Stage 2: Shield and wordmark resolve + status activates (350 - 850ms)
    // Stage 3: Smooth dissolve to app (850 - 1000ms)
    const t1 = setTimeout(() => setStage('resolve'), 350);
    const t2 = setTimeout(() => setStage('finish'), 850);
    const t3 = setTimeout(() => onComplete(), 1050);

    const handleSkip = () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      onComplete();
    };

    window.addEventListener('keydown', handleSkip, { once: true });
    window.addEventListener('click', handleSkip, { once: true });

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      window.removeEventListener('keydown', handleSkip);
      window.removeEventListener('click', handleSkip);
    };
  }, [onComplete]);

  return (
    <AnimatePresence>
      {stage !== 'finish' && (
        <motion.div
          key="signature-intro"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            backgroundColor: 'var(--bg)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            userSelect: 'none'
          }}
        >
          {/* Central Forensic Initialization Box */}
          <div
            style={{
              position: 'relative',
              width: '380px',
              maxWidth: '90vw',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '14px'
            }}
          >
            {/* 1px Forensic Trace Line */}
            <motion.div
              initial={{ scaleX: 0, opacity: 0 }}
              animate={{ scaleX: 1, opacity: 1 }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
              style={{
                position: 'absolute',
                top: '50%',
                left: 0,
                right: 0,
                height: '1px',
                backgroundColor: 'var(--primary)',
                boxShadow: '0 0 8px var(--primary)',
                transformOrigin: 'left center',
                zIndex: 1
              }}
            />

            {/* Shield and Wordmark (resolves in stage 2) */}
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: stage === 'resolve' ? 1 : 0.2, scale: 1 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                zIndex: 2,
                backgroundColor: 'var(--bg)',
                padding: '0 16px'
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--primary)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 2px 8px rgba(37, 99, 235, 0.3)'
                }}
              >
                <ShieldCheck size={18} />
              </div>

              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      fontSize: '18px',
                      fontWeight: 800,
                      letterSpacing: '-0.02em',
                      color: 'var(--text)',
                      lineHeight: 1
                    }}
                  >
                    AegisTrace
                  </span>
                  <span
                    style={{
                      fontSize: '9.5px',
                      fontWeight: 700,
                      padding: '2px 5px',
                      borderRadius: 'var(--radius-xs)',
                      backgroundColor: 'var(--surface-hover)',
                      color: 'var(--text-secondary)',
                      border: '1px solid var(--border)',
                      lineHeight: 1
                    }}
                  >
                    FIPS 203/204
                  </span>
                </div>
                <div
                  style={{
                    fontSize: '11px',
                    color: 'var(--text-tertiary)',
                    marginTop: '3px'
                  }}
                >
                  Forensic Security Workstation
                </div>
              </div>
            </motion.div>

            {/* Small Subsystem Activation Indicator */}
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: stage === 'resolve' ? 1 : 0, y: stage === 'resolve' ? 0 : 4 }}
              transition={{ duration: 0.2, delay: 0.1 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '10.5px',
                color: 'var(--text-secondary)',
                fontFamily: 'var(--font-mono)',
                zIndex: 2,
                backgroundColor: 'var(--bg)',
                padding: '2px 8px'
              }}
            >
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--success)',
                  display: 'inline-block'
                }}
              />
              <span>PQC Engine Active: ML-KEM-768 • ML-DSA-65 • m=128</span>
            </motion.div>
          </div>

          {/* Discreet click to skip note */}
          <div
            style={{
              position: 'absolute',
              bottom: '24px',
              fontSize: '10.5px',
              color: 'var(--text-disabled)',
              letterSpacing: '0.04em'
            }}
          >
            Press any key or click to skip
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

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

    const t1 = setTimeout(() => setStage('resolve'), 300);
    const t2 = setTimeout(() => setStage('finish'), 750);
    const t3 = setTimeout(() => onComplete(), 900);

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
          transition={{ duration: 0.15, ease: 'easeOut' }}
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            backgroundColor: 'var(--bg-canvas)',
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
              width: '360px',
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
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              style={{
                position: 'absolute',
                top: '50%',
                left: 0,
                right: 0,
                height: '1px',
                backgroundColor: 'var(--petrol)',
                transformOrigin: 'left center',
                zIndex: 1
              }}
            />

            {/* Shield and Wordmark */}
            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: stage === 'resolve' ? 1 : 0.2, scale: 1 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                zIndex: 2,
                backgroundColor: 'var(--bg-canvas)',
                padding: '0 16px'
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--petrol)',
                  color: '#0B1015',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <ShieldCheck size={18} />
              </div>

              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      fontSize: '17px',
                      fontWeight: 600,
                      letterSpacing: '-0.02em',
                      color: 'var(--text-ivory)',
                      lineHeight: 1
                    }}
                  >
                    AegisTrace
                  </span>
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: 500,
                      padding: '2px 6px',
                      borderRadius: '3px',
                      backgroundColor: 'var(--bg-elevated)',
                      color: 'var(--text-slate)',
                      border: '1px solid var(--border-subtle)',
                      lineHeight: 1
                    }}
                  >
                    FIPS 203/204
                  </span>
                </div>
                <div
                  style={{
                    fontSize: '11px',
                    color: 'var(--text-graphite)',
                    marginTop: '3px'
                  }}
                >
                  Digital Forensic Investigation Workstation
                </div>
              </div>
            </motion.div>

            {/* Small Subsystem Activation Indicator */}
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: stage === 'resolve' ? 1 : 0, y: stage === 'resolve' ? 0 : 4 }}
              transition={{ duration: 0.2, delay: 0.05 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '10.5px',
                color: 'var(--text-slate)',
                fontFamily: 'var(--font-mono)',
                zIndex: 2,
                backgroundColor: 'var(--bg-canvas)',
                padding: '2px 8px'
              }}
            >
              <span
                style={{
                  width: '5px',
                  height: '5px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--jade)',
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
              fontSize: '11px',
              color: 'var(--text-graphite)',
              letterSpacing: '0.02em'
            }}
          >
            Click or press any key to enter
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

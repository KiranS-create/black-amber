import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  width?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

/**
 * Drawer Component — Layer 3 Contextual Glass Overlay
 * Controlled blur, hairline border, preserves underlying investigation context.
 */
export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  width = '520px',
  children,
  footer
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 100,
            display: 'flex',
            justifyContent: 'flex-end',
            backgroundColor: 'rgba(11, 16, 21, 0.65)',
            backdropFilter: 'blur(6px)',
            WebkitBackdropFilter: 'blur(6px)'
          }}
          onClick={onClose}
        >
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
            style={{
              width,
              maxWidth: '100vw',
              height: '100%',
              backgroundColor: 'var(--glass-surface-elevated)',
              backdropFilter: 'var(--glass-blur-md)',
              WebkitBackdropFilter: 'var(--glass-blur-md)',
              borderLeft: '1px solid var(--border)',
              boxShadow: 'var(--shadow-drawer)',
              display: 'flex',
              flexDirection: 'column',
              boxSizing: 'border-box'
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Drawer Header */}
            <div
              style={{
                padding: 'var(--space-4) var(--space-6)',
                borderBottom: '1px solid var(--border)',
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: 'var(--space-4)',
                backgroundColor: 'rgba(255, 255, 255, 0.02)'
              }}
            >
              <div>
                <h3
                  style={{
                    margin: 0,
                    fontSize: 'var(--text-md)',
                    fontWeight: 600,
                    color: 'var(--text)',
                    letterSpacing: '-0.01em'
                  }}
                >
                  {title}
                </h3>
                {subtitle && (
                  <p
                    style={{
                      margin: '2px 0 0 0',
                      fontSize: 'var(--text-xs)',
                      color: 'var(--text-tertiary)'
                    }}
                  >
                    {subtitle}
                  </p>
                )}
              </div>

              <button
                onClick={onClose}
                aria-label="Close drawer"
                style={{
                  background: 'transparent',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-xs)',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  padding: '5px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'color var(--transition-fast), border-color var(--transition-fast)'
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.color = 'var(--text)';
                  e.currentTarget.style.borderColor = 'var(--border)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.color = 'var(--text-secondary)';
                  e.currentTarget.style.borderColor = 'var(--border-subtle)';
                }}
              >
                <X size={15} />
              </button>
            </div>

            {/* Drawer Body Viewport */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: 'var(--space-6)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-5)'
              }}
            >
              {children}
            </div>

            {/* Optional Drawer Footer */}
            {footer && (
              <div
                style={{
                  padding: 'var(--space-4) var(--space-6)',
                  borderTop: '1px solid var(--border)',
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  display: 'flex',
                  justifyContent: 'flex-end',
                  gap: 'var(--space-3)'
                }}
              >
                {footer}
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

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
            backgroundColor: 'rgba(0, 0, 0, 0.45)',
            backdropFilter: 'blur(3px)'
          }}
          onClick={onClose}
        >
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 28, stiffness: 280 }}
            style={{
              width,
              maxWidth: '100vw',
              height: '100%',
              backgroundColor: 'var(--surface-elevated)',
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
                backgroundColor: 'var(--surface)'
              }}
            >
              <div>
                <h3
                  style={{
                    margin: 0,
                    fontSize: 'var(--text-lg)',
                    fontWeight: 700,
                    color: 'var(--text)',
                    letterSpacing: '-0.01em'
                  }}
                >
                  {title}
                </h3>
                {subtitle && (
                  <p
                    style={{
                      margin: '4px 0 0 0',
                      fontSize: 'var(--text-xs)',
                      color: 'var(--text-secondary)'
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
                  border: 'none',
                  color: 'var(--text-tertiary)',
                  cursor: 'pointer',
                  padding: '6px',
                  borderRadius: 'var(--radius-sm)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'background var(--transition-fast), color var(--transition-fast)'
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-hover)';
                  (e.currentTarget as HTMLElement).style.color = 'var(--text)';
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
                  (e.currentTarget as HTMLElement).style.color = 'var(--text-tertiary)';
                }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Drawer Body */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: 'var(--space-6)',
                color: 'var(--text)',
                fontSize: 'var(--text-base)'
              }}
            >
              {children}
            </div>

            {/* Drawer Footer (optional) */}
            {footer && (
              <div
                style={{
                  padding: 'var(--space-4) var(--space-6)',
                  borderTop: '1px solid var(--border)',
                  backgroundColor: 'var(--surface)',
                  display: 'flex',
                  alignItems: 'center',
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

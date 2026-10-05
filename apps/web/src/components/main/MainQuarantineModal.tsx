import React, { useState } from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2, Lock, X } from 'lucide-react';

export interface MainQuarantineModalProps {
  isOpen: boolean;
  onClose: () => void;
  suspectName: string;
  suspectRank: string;
  terminalId: string;
  secretCodeHex: string;
  onExecuteQuarantine: (suspectName: string, terminalId: string, reason: string) => Promise<void>;
  onViewLedger?: () => void;
}

export const MainQuarantineModal: React.FC<MainQuarantineModalProps> = ({
  isOpen,
  onClose,
  suspectName,
  suspectRank,
  terminalId,
  secretCodeHex,
  onExecuteQuarantine,
  onViewLedger
}) => {
  const [reason, setReason] = useState('Unauthorized leakage of classified material detected and attributed via Bayesian fusion.');
  const [isExecuting, setIsExecuting] = useState(false);
  const [isQuarantined, setIsQuarantined] = useState(false);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    setIsExecuting(true);
    try {
      await onExecuteQuarantine(suspectName, terminalId, reason);
      setIsQuarantined(true);
    } catch (err) {
      console.error('Failed to execute quarantine:', err);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="main-modal-backdrop" onClick={onClose} style={{ zIndex: 1100 }}>
      <div 
        className="main-modal glass-panel" 
        style={{
          width: '100%',
          maxWidth: '540px',
          borderRadius: '24px',
          overflow: 'hidden'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="main-modal-header" style={{ borderBottom: '1px solid var(--main-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ 
              width: '38px', 
              height: '38px', 
              borderRadius: '50%', 
              background: 'rgba(239, 68, 68, 0.12)', 
              color: '#EF4444', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              border: '1px solid rgba(239, 68, 68, 0.25)'
            }}>
              <ShieldAlert size={20} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="main-badge" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#EF4444', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                  Revocation Gate
                </span>
                <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', fontWeight: 600 }}>
                  WASM ISOLATION
                </span>
              </div>
              <h2 className="main-modal-title" style={{ fontSize: '17px', marginTop: '2px' }}>
                Sovereign Quarantine Authorization
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="main-btn-ghost"
            style={{ padding: '6px' }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Content */}
        <div className="main-modal-body" style={{ padding: '24px' }}>
          {isQuarantined ? (
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px auto',
                color: '#10B981'
              }}>
                <CheckCircle2 size={36} />
              </div>
              <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--main-text-primary)', margin: '0 0 8px 0', letterSpacing: '-0.02em' }}>
                Principal Quarantined
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--main-text-secondary)', margin: '0 0 20px 0', lineHeight: 1.5 }}>
                <strong>{suspectName}</strong> has been suspended from the identity directory. Device credentials and ML-KEM decryption keys have been revoked.
              </p>
              {onViewLedger && (
                <button
                  onClick={() => { onClose(); onViewLedger(); }}
                  className="main-btn-secondary"
                  style={{ fontSize: '13px' }}
                >
                  View Provenance Ledger Event
                </button>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div style={{
                backgroundColor: 'rgba(245, 158, 11, 0.08)',
                border: '1px solid rgba(245, 158, 11, 0.25)',
                borderRadius: '14px',
                padding: '14px',
                display: 'flex',
                gap: '12px',
                alignItems: 'flex-start'
              }}>
                <AlertTriangle size={18} style={{ color: '#F59E0B', flexShrink: 0, marginTop: '2px' }} />
                <div style={{ fontSize: '12.5px', color: 'var(--main-text-primary)', lineHeight: 1.45 }}>
                  Executing quarantine will immediately revoke the suspect's active session, lock their client identity, and log a permanent tamper-evident event to the DLT ledger.
                </div>
              </div>

              {/* Target Details */}
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr 1fr', 
                gap: '12px', 
                padding: '14px', 
                borderRadius: '14px',
                background: 'var(--main-surface-elevated)',
                border: '1px solid var(--main-border)',
                fontSize: '12.5px' 
              }}>
                <div>
                  <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                    Target Principal
                  </span>
                  <div style={{ fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '3px' }}>
                    {suspectName}
                  </div>
                  <div style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', marginTop: '1px' }}>
                    {suspectRank}
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                    Enclave Terminal
                  </span>
                  <div className="main-mono" style={{ color: 'var(--main-accent)', fontWeight: 600, marginTop: '3px' }}>
                    {terminalId}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', marginTop: '1px' }}>
                    ML-KEM Key Ring Revoked
                  </div>
                </div>
              </div>

              {/* Reason */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--main-text-primary)', marginBottom: '8px' }}>
                  Justification for Emergency Revocation
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={2}
                  className="form-input"
                  style={{
                    width: '100%',
                    borderRadius: '12px',
                    padding: '10px 12px',
                    fontSize: '12.5px',
                    resize: 'none'
                  }}
                />
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '6px' }}>
                <button
                  type="button"
                  onClick={onClose}
                  className="main-btn-secondary"
                  style={{ fontSize: '12.5px' }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirm}
                  disabled={isExecuting}
                  className="main-btn-primary"
                  style={{
                    backgroundColor: '#DC2626',
                    borderColor: '#B91C1C',
                    fontSize: '12.5px'
                  }}
                >
                  <Lock size={14} />
                  <span>{isExecuting ? 'Executing Quarantine…' : 'Confirm Sovereign Quarantine'}</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

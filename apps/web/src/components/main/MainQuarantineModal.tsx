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
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.6)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '16px'
    }}>
      <div style={{
        backgroundColor: 'var(--surface-elevated, #161B22)',
        border: '1px solid var(--border, #30363D)',
        borderRadius: '8px',
        width: '100%',
        maxWidth: '520px',
        boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: '1px solid var(--border, #30363D)',
          backgroundColor: 'rgba(239, 68, 68, 0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#EF4444' }}>
            <ShieldAlert size={20} />
            <span style={{ fontSize: '15px', fontWeight: 600 }}>Sovereign Quarantine Authorization</span>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-secondary, #8B949E)',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '20px' }}>
          {isQuarantined ? (
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <CheckCircle2 size={44} style={{ color: '#10B981', margin: '0 auto 12px auto' }} />
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text, #F0F6FC)', margin: '0 0 6px 0' }}>
                Principal Quarantined
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary, #8B949E)', margin: '0 0 16px 0' }}>
                {suspectName} has been suspended from the identity directory. Device credentials and ML-KEM decryption keys have been revoked.
              </p>
              {onViewLedger && (
                <button
                  onClick={() => { onClose(); onViewLedger(); }}
                  className="btn-secondary"
                  style={{ fontSize: '12.5px' }}
                >
                  View Provenance Ledger Event
                </button>
              )}
            </div>
          ) : (
            <div>
              <div style={{
                backgroundColor: 'rgba(245, 158, 11, 0.08)',
                border: '1px solid rgba(245, 158, 11, 0.25)',
                borderRadius: '6px',
                padding: '12px',
                marginBottom: '16px',
                display: 'flex',
                gap: '10px'
              }}>
                <AlertTriangle size={18} style={{ color: '#F59E0B', flexShrink: 0, marginTop: '2px' }} />
                <div style={{ fontSize: '12.5px', color: 'var(--text, #F0F6FC)', lineHeight: 1.4 }}>
                  Executing quarantine will immediately revoke the suspect's active session, lock their client identity, and log a permanent tamper-evident event to the DLT ledger.
                </div>
              </div>

              {/* Target Details */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px', fontSize: '12.5px' }}>
                <div>
                  <span style={{ color: 'var(--text-tertiary, #6E7681)' }}>Target Principal:</span>
                  <div style={{ fontWeight: 600, color: 'var(--text, #F0F6FC)', marginTop: '2px' }}>{suspectName} ({suspectRank})</div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-tertiary, #6E7681)' }}>Enclave Terminal:</span>
                  <div style={{ fontFamily: 'var(--font-mono, monospace)', color: 'var(--text, #F0F6FC)', marginTop: '2px' }}>{terminalId}</div>
                </div>
              </div>

              {/* Reason */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary, #8B949E)', marginBottom: '6px' }}>
                  Justification for Emergency Revocation
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={2}
                  style={{
                    width: '100%',
                    backgroundColor: 'var(--surface, #0D1117)',
                    border: '1px solid var(--border, #30363D)',
                    borderRadius: '6px',
                    padding: '8px 10px',
                    color: 'var(--text, #F0F6FC)',
                    fontSize: '12.5px',
                    resize: 'none'
                  }}
                />
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={onClose}
                  className="btn-secondary"
                  style={{ fontSize: '12.5px' }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirm}
                  disabled={isExecuting}
                  className="btn-primary"
                  style={{
                    backgroundColor: '#DC2626',
                    borderColor: '#DC2626',
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

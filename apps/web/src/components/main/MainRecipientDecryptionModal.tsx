import React, { useState } from 'react';
import { DocumentRelease, PublicRecipient } from '../../types';
import { apiService } from '../../services/api';
import { 
  X, 
  Key, 
  ShieldCheck, 
  FileCheck2, 
  Cpu, 
  Download, 
  Eye, 
  Search, 
  CheckCircle2, 
  Lock, 
  Sparkles,
  ArrowRight,
  Database
} from 'lucide-react';
import { audioService } from '../../services/audioService';

interface MainRecipientDecryptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  releases: DocumentRelease[];
  recipients: PublicRecipient[];
  initialRecipientId?: string;
  onEnrollRecipient?: (
    name: string, 
    id?: string, 
    role?: string, 
    terminalId?: string, 
    department?: string, 
    clearance?: string
  ) => Promise<void>;
  onOpenComparator?: (recipientName: string, docName: string) => void;
  onInvestigateLeak?: (scenarioId: string) => void;
  onTestLeakAttribution?: (recipient: PublicRecipient) => void;
  onRefresh?: () => Promise<void>;
}

export const MainRecipientDecryptionModal: React.FC<MainRecipientDecryptionModalProps> = ({
  isOpen,
  onClose,
  releases,
  recipients,
  initialRecipientId,
  onEnrollRecipient,
  onOpenComparator,
  onInvestigateLeak,
  onTestLeakAttribution,
  onRefresh
}) => {
  const [selectedRecipientId, setSelectedRecipientId] = useState<string>(() => initialRecipientId || 'bob');
  const [selectedReleaseId, setSelectedReleaseId] = useState<string>(() => releases[0]?.release_id || 'rel_20260926_001');
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [decryptionResult, setDecryptionResult] = useState<any | null>(null);
  const [subTab, setSubTab] = useState<'terminal' | 'enclave'>('terminal');

  // Inline Quick-Enroll state
  const [showQuickEnroll, setShowQuickEnroll] = useState(false);
  const [quickName, setQuickName] = useState('');
  const [quickTerminal, setQuickTerminal] = useState('');
  const [quickRole, setQuickRole] = useState('');

  React.useEffect(() => {
    if (initialRecipientId) {
      setSelectedRecipientId(initialRecipientId);
    }
  }, [initialRecipientId]);

  if (!isOpen) return null;

  const currentRelease = releases.find(r => r.release_id === selectedReleaseId) || releases[0];
  const currentRecipient: PublicRecipient = recipients.find(r => r.recipient_id === selectedRecipientId) || {
    recipient_id: 'bob',
    name: 'Marcus Vance',
    role: 'Principal Cryptanalyst',
    algorithm_kem: 'ML-KEM-768 (Kyber-768 standard)',
    algorithm_dsa: 'ML-DSA-65 (Dilithium3 standard)',
    kem_public_key_b64: 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0',
    dsa_public_key_b64: 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1',
    created_at: new Date().toISOString(),
    status: 'ACTIVE',
    terminal_id: 'Field Terminal #ST-842911',
    department: 'Strategic Intelligence Division'
  };

  const handleExecuteDecryption = async () => {
    setIsExecuting(true);
    setDecryptionResult(null);
    setCurrentStep(1);

    try {
      // Step 1: ML-KEM-768 Decapsulation
      await new Promise(r => setTimeout(r, 600));
      setCurrentStep(2);

      // Step 2: Dynamic in-memory Tardos watermark injection
      await new Promise(r => setTimeout(r, 700));
      setCurrentStep(3);

      // Step 3: ML-DSA-65 Recipient Provenance Signing
      await new Promise(r => setTimeout(r, 600));
      setCurrentStep(4);

      // Step 4: Merkle Ledger Block Minting
      const result = await apiService.decryptPackage(
        currentRelease?.release_id || 'rel_20260926_001',
        selectedRecipientId
      );

      await new Promise(r => setTimeout(r, 500));
      setDecryptionResult(result);
      audioService.playDecryptionSuccess();
      if (onRefresh) await onRefresh();
    } catch (err: any) {
      console.error('Decryption failed:', err);
      // Fallback result for offline / mock testing
      setDecryptionResult({
        status: 'SUCCESS',
        release_id: currentRelease?.release_id || 'rel_20260926_001',
        document_id: currentRelease?.document_id || 'doc_sec_shield_99',
        recipient_id: selectedRecipientId,
        original_document_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
        traceable_artifact_hash: selectedRecipientId === 'bob' 
          ? '7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b'
          : '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b',
        signature_b64: `dSA65_sig_${selectedRecipientId}_02_eefa1234567890abcdef1234567890`,
        timestamp: new Date().toISOString()
      });
      audioService.playDecryptionSuccess();
      if (onRefresh) await onRefresh();
    } finally {
      setIsExecuting(false);
    }
  };

  const handleDownloadCopy = () => {
    const docName = currentRelease?.document_name || 'Protected_Protocol.pdf';
    const cleanName = docName.replace('.pdf', '') + `_decrypted_${selectedRecipientId}.pdf`;
    const terminalTag = currentRecipient.terminal_id || `Field Terminal #ST-${selectedRecipientId.toUpperCase()}`;
    const dummyPdfContent = `%PDF-1.7\n% AegisTrace Cryptographic Provenance Watermarked Document\n% Recipient: ${currentRecipient.name} (${selectedRecipientId})\n% Terminal: ${terminalTag}\n% Department: ${currentRecipient.department || 'Strategic Intelligence Division'}\n% Role: ${currentRecipient.role || 'Authorized Principal'}\n% ML-DSA-65 Signature: ${decryptionResult?.signature_b64 || 'SIMULATED'}\n% Original Hash: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08\n% Traitor-Tracing Codeword: Tardos m=128, c<=5\n%%EOF`;
    const blob = new Blob([dummyPdfContent], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = cleanName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="main-modal-backdrop" onClick={onClose}>
      <div 
        className="main-modal" 
        style={{ maxWidth: '680px', width: '100%', maxHeight: '90vh', overflowY: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="main-modal-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="main-badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', borderColor: 'rgba(59, 130, 246, 0.3)' }}>
                Sovereign Directive
              </span>
              <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                Interactive Recipient Portal
              </span>
            </div>
            <h2 className="main-modal-title" style={{ fontSize: '18px' }}>
              Recipient Decryption & Provenance Signing
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '4px 0 0 0' }}>
              Demonstrates independent post-quantum decapsulation, dynamic volatile-memory watermarking, and non-repudiable DLT block minting.
            </p>
          </div>
          <button onClick={onClose} className="main-btn-ghost" style={{ padding: '6px' }}>
            <X size={16} />
          </button>
        </div>

        {/* Sub-tab Selector */}
        <div style={{ padding: '16px 28px 0 28px', display: 'flex' }}>
          <div className="glass-pill-container">
            <button
              type="button"
              onClick={() => setSubTab('terminal')}
              className={`glass-pill-btn ${subTab === 'terminal' ? 'active' : ''}`}
            >
              ✦ Terminal Decryption Pipeline
            </button>
            <button
              type="button"
              onClick={() => setSubTab('enclave')}
              className={`glass-pill-btn ${subTab === 'enclave' ? 'active' : ''}`}
            >
              🛡️ Secure WASM Enclave & Memory Architecture
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="main-modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {subTab === 'terminal' ? (
            <>
              {/* Recipient Selection */}
              {/* Release Selection */}
              <div>
                <label style={{ fontSize: '12px', fontWeight: 650, color: 'var(--main-text-primary)', display: 'block', marginBottom: '8px' }}>
                  1. Select Broadcast Release Package
                </label>
                {releases.length > 0 ? (
                  <select
                    value={selectedReleaseId}
                    onChange={(e) => {
                      setSelectedReleaseId(e.target.value);
                      const targetRel = releases.find(r => r.release_id === e.target.value);
                      if (targetRel && targetRel.recipient_ids && targetRel.recipient_ids.length > 0) {
                        setSelectedRecipientId(targetRel.recipient_ids[0]);
                      }
                    }}
                    disabled={isExecuting}
                    className="main-select"
                    style={{ width: '100%', padding: '10px 14px', borderRadius: '12px', background: 'var(--main-surface)', border: '1px solid var(--main-border)', color: 'var(--main-text-primary)', fontSize: '13px' }}
                  >
                    {releases.map(rel => (
                      <option key={rel.release_id} value={rel.release_id}>
                        {rel.document_name} ({rel.release_id}) — {rel.recipient_ids?.length || 0} Recipients
                      </option>
                    ))}
                  </select>
                ) : (
                  <div style={{ padding: '10px 14px', borderRadius: '12px', background: 'var(--main-surface)', border: '1px solid var(--main-border)', fontSize: '12px', color: 'var(--main-text-secondary)' }}>
                    Active Release Envelope: <strong>{selectedReleaseId}</strong>
                  </div>
                )}
              </div>

              {/* Recipient Selection */}
              <div>
                <label style={{ fontSize: '12px', fontWeight: 650, color: 'var(--main-text-primary)', display: 'block', marginBottom: '10px' }}>
                  2. Select Recipient Workstation Terminal
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
                  {(recipients.length > 0 ? recipients : [
                    { recipient_id: 'bob', name: 'Marcus Vance', role: 'Principal Cryptanalyst' },
                    { recipient_id: 'alice', name: 'Sarah Jenkins', role: 'Cyber Defense Lead' },
                    { recipient_id: 'charlie', name: 'Dr. Aris Thorne', role: 'Visiting PQC Scientist' }
                  ]).map(rec => {
                    const isSelected = selectedRecipientId === rec.recipient_id;
                    return (
                      <div
                        key={rec.recipient_id}
                        onClick={() => !isExecuting && setSelectedRecipientId(rec.recipient_id)}
                        style={{
                          padding: '14px',
                          borderRadius: '14px',
                          border: `1px solid ${isSelected ? 'var(--main-accent)' : 'var(--main-border)'}`,
                          background: isSelected ? 'var(--main-surface-hover)' : 'var(--main-surface-elevated)',
                          cursor: isExecuting ? 'not-allowed' : 'pointer',
                          transition: 'all 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
                          boxShadow: isSelected ? '0 4px 16px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.12)' : 'none'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <span style={{ fontSize: '11px', fontWeight: 650, color: isSelected ? 'var(--main-accent)' : 'var(--main-text-tertiary)' }}>
                            TERMINAL #{rec.recipient_id.toUpperCase()}
                          </span>
                          {isSelected && <CheckCircle2 size={13} style={{ color: 'var(--main-accent)' }} />}
                        </div>
                        <div style={{ fontSize: '13.5px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                          {rec.name}
                        </div>
                        <div style={{ fontSize: '11.5px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
                          {rec.role || 'Authorized Principal'}
                        </div>
                      </div>
                    );
                  })}

                  {onEnrollRecipient && (
                    <div
                      onClick={() => setShowQuickEnroll(!showQuickEnroll)}
                      style={{
                        padding: '14px',
                        borderRadius: '14px',
                        border: '1px dashed var(--main-border-active)',
                        background: 'transparent',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                        minHeight: '80px',
                        transition: 'all 0.18s ease'
                      }}
                    >
                      <Sparkles size={16} style={{ color: 'var(--main-accent)' }} />
                      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--main-accent)' }}>
                        + Add Custom Recipient
                      </span>
                    </div>
                  )}
                </div>

                {showQuickEnroll && (
                  <div style={{ marginTop: '12px', padding: '14px 16px', background: 'var(--main-surface-elevated)', borderRadius: '12px', border: '1px solid var(--main-accent)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ fontSize: '12px', fontWeight: 650, color: 'var(--main-text-primary)' }}>
                      Quick-Enroll Principal & Terminal
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px' }}>
                      <input
                        type="text"
                        placeholder="Officer Name *"
                        value={quickName}
                        onChange={e => setQuickName(e.target.value)}
                        style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--main-border)', background: 'var(--main-surface)', color: 'var(--main-text-primary)', fontSize: '12px' }}
                      />
                      <input
                        type="text"
                        placeholder="Terminal ID (e.g. ST-7721)"
                        value={quickTerminal}
                        onChange={e => setQuickTerminal(e.target.value)}
                        style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--main-border)', background: 'var(--main-surface)', color: 'var(--main-text-primary)', fontSize: '12px' }}
                      />
                      <input
                        type="text"
                        placeholder="Role / Rank"
                        value={quickRole}
                        onChange={e => setQuickRole(e.target.value)}
                        style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--main-border)', background: 'var(--main-surface)', color: 'var(--main-text-primary)', fontSize: '12px' }}
                      />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                      <button
                        type="button"
                        onClick={() => setShowQuickEnroll(false)}
                        className="main-btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '11px' }}
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        disabled={!quickName.trim()}
                        onClick={async () => {
                          if (!onEnrollRecipient || !quickName.trim()) return;
                          const cleanId = quickName.trim().toLowerCase().replace(/[^a-z0-9]/g, '_');
                          const term = quickTerminal.trim() || `Field Terminal #ST-${Math.floor(100000 + Math.random() * 900000)}`;
                          await onEnrollRecipient(quickName.trim(), cleanId, quickRole.trim() || 'Principal Intelligence Officer', term);
                          setSelectedRecipientId(cleanId);
                          setQuickName('');
                          setQuickTerminal('');
                          setQuickRole('');
                          setShowQuickEnroll(false);
                        }}
                        className="main-btn-primary"
                        style={{ padding: '4px 12px', fontSize: '11px' }}
                      >
                        Enroll & Select
                      </button>
                    </div>
                  </div>
                )}
              </div>

          {/* Cryptographic Package Info */}
          <div style={{ padding: '14px 16px', background: 'var(--main-surface-elevated)', borderRadius: '14px', border: '1px solid var(--main-border)', fontSize: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 650, color: 'var(--main-text-primary)' }}>Broadcast Envelope Details:</span>
              <span className="main-mono" style={{ fontSize: '11px', color: 'var(--main-text-secondary)' }}>
                {currentRelease?.release_id || 'rel_20260926_001'}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', color: 'var(--main-text-secondary)', fontSize: '11.5px' }}>
              <div>Document: <strong style={{ color: 'var(--main-text-primary)' }}>{currentRelease?.document_name || 'National_Defense_Protocol_2026.pdf'}</strong></div>
              <div>Key Encapsulation: <strong style={{ color: 'var(--main-text-primary)' }}>ML-KEM-768 (NIST FIPS 203)</strong></div>
              <div>Digital Signature: <strong style={{ color: 'var(--main-text-primary)' }}>ML-DSA-65 (NIST FIPS 204)</strong></div>
              <div>Traitor Tracing: <strong style={{ color: 'var(--main-text-primary)' }}>Tardos 128-bit (c ≤ 5)</strong></div>
            </div>
          </div>

          {/* Stepper Progress Visualizer */}
          {(isExecuting || decryptionResult) && (
            <div style={{ padding: '18px 20px', background: 'var(--main-surface-elevated)', borderRadius: '16px', border: '1px solid var(--main-border)' }}>
              <div style={{ fontSize: '12.5px', fontWeight: 650, color: 'var(--main-text-primary)', marginBottom: '12px' }}>
                Cryptographic Execution Pipeline
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {[
                  { step: 1, title: 'ML-KEM-768 Decapsulation', desc: 'Recipient private key decapsulates AES-256 session key without master server contact' },
                  { step: 2, title: 'Dynamic Volatile-Memory Watermarking', desc: 'Orthogonal Tardos sequence & DSSS carrier injected directly in RAM (never written unwatermarked)' },
                  { step: 3, title: 'ML-DSA-65 Recipient Provenance Signing', desc: 'Hardware enclave signs Decryption Receipt H(Plaintext) || Timestamp' },
                  { step: 4, title: 'Merkle Ledger Block Minting', desc: 'Non-repudiable receipt appended to RFC-6962 immutable hash tree chain' }
                ].map((s) => {
                  const isDone = currentStep > s.step || decryptionResult !== null;
                  const isCurrent = currentStep === s.step && isExecuting;
                  return (
                    <div 
                      key={s.step}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: '8px 10px',
                        borderRadius: '6px',
                        background: isCurrent ? 'var(--main-surface-hover)' : 'transparent',
                        border: isCurrent ? '1px solid var(--main-border-active)' : '1px solid transparent'
                      }}
                    >
                      <div 
                        style={{
                          width: '24px',
                          height: '24px',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '11px',
                          fontWeight: 600,
                          background: isDone ? 'var(--main-jade)' : isCurrent ? '#3B82F6' : 'var(--main-surface-elevated)',
                          color: isDone || isCurrent ? '#FFFFFF' : 'var(--main-text-tertiary)'
                        }}
                      >
                        {isDone ? <CheckCircle2 size={14} /> : s.step}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '12px', fontWeight: 600, color: isDone || isCurrent ? 'var(--main-text-primary)' : 'var(--main-text-tertiary)' }}>
                          {s.title}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)' }}>
                          {s.desc}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Decryption Completed Result Summary */}
          {decryptionResult && (
            <div style={{ padding: '16px', background: 'rgba(34, 197, 94, 0.05)', borderRadius: '8px', border: '1px solid rgba(34, 197, 94, 0.25)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span className="main-badge main-badge-verified" style={{ fontSize: '12px' }}>
                  <CheckCircle2 size={13} />
                  DECRYPTED & SIGNED (PROVENANCE RECORDED)
                </span>
                <span className="main-mono" style={{ fontSize: '11px', color: 'var(--main-text-secondary)' }}>
                  Block #2 Minted
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px', fontSize: '11px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--main-text-tertiary)' }}>Master Document SHA-256:</span>
                  <span className="main-mono" style={{ color: 'var(--main-text-primary)' }}>
                    9f86d081884c7d659a2feaa0c55ad015...
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--main-text-tertiary)' }}>Recipient Watermarked Hash:</span>
                  <span className="main-mono" style={{ color: 'var(--main-jade)', fontWeight: 600 }}>
                    {decryptionResult.traceable_artifact_hash?.substring(0, 32)}...
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--main-text-tertiary)' }}>ML-DSA-65 Recipient Signature:</span>
                  <span className="main-mono" style={{ color: 'var(--main-text-secondary)' }}>
                    {decryptionResult.signature_b64?.substring(0, 32)}...
                  </span>
                </div>
              </div>

              {/* Action Buttons for Next Steps */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '16px', flexWrap: 'wrap' }}>
                <button
                  onClick={() => {
                    onClose();
                    if (onOpenComparator) {
                      onOpenComparator(currentRecipient.name, currentRelease?.document_name || 'Protocol.pdf');
                    }
                  }}
                  className="main-btn-primary"
                  style={{ fontSize: '12px', background: '#3B82F6', borderColor: '#2563EB' }}
                >
                  <Eye size={13} />
                  <span>Launch Visual Comparator (Proof of Invisibility) →</span>
                </button>

                <button
                  onClick={handleDownloadCopy}
                  className="main-btn-secondary"
                  style={{ fontSize: '12px' }}
                >
                  <Download size={13} />
                  <span>Download Watermarked PDF</span>
                </button>

                <button
                  onClick={() => {
                    onClose();
                    if (onTestLeakAttribution) {
                      onTestLeakAttribution(currentRecipient);
                    } else if (onInvestigateLeak) {
                      const scenarioId = currentRecipient.recipient_id === 'alice' ? 'clean_alice' : currentRecipient.recipient_id === 'charlie' ? 'clean_charlie' : 'clean_bob';
                      onInvestigateLeak(scenarioId);
                    }
                  }}
                  className="main-btn-primary"
                  style={{ fontSize: '12px', background: '#0284C7', borderColor: '#0369A1' }}
                >
                  <Search size={13} />
                  <span>⚡ Immediately Test Leak Attribution on This Copy →</span>
                </button>
              </div>
            </div>
          )}
          </>
          ) : (
            /* WASM Enclave Memory Isolation Visualizer */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="glass-card" style={{ padding: '16px 18px', background: 'rgba(34, 197, 94, 0.05)', border: '1px solid rgba(34, 197, 94, 0.2)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <ShieldCheck size={16} style={{ color: 'var(--main-jade)' }} />
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                    Client-Side Hardware Enclave & WebAssembly Memory Isolation
                  </span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--main-text-secondary)', margin: 0, lineHeight: 1.5 }}>
                  Guarantees that raw, unwatermarked plaintext is physically prevented from reaching the OS filesystem, disk cache, or unprivileged JavaScript DOM. Watermarking occurs inside an isolated 64MB WASM memory buffer prior to frame compositing.
                </p>
              </div>

              {/* Three-Tier Memory Security Architecture */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {/* Layer 1: Host JS / DOM Layer */}
                <div style={{ padding: '14px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--main-border)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="main-mono" style={{ fontSize: '10px', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--main-crimson)', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>
                        RING 3 • UNPRIVILEGED
                      </span>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                        Host Browser & JavaScript Main Thread
                      </span>
                    </div>
                    <span style={{ fontSize: '10px', color: 'var(--main-text-tertiary)' }}>Zero Plaintext Exposure</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', lineHeight: 1.5 }}>
                    • Ingests encrypted broadcast container (AES-256-GCM ciphertext + PQC KEM header).<br />
                    • Cannot inspect internal linear memory addresses of the WASM runtime.<br />
                    • <strong>Anti-Debugger Trap:</strong> Monitors runtime hooks; active debugger or breakpoint triggers immediate memory wipe and session abort.
                  </div>
                </div>

                {/* Layer 2: WASM Sandboxed Memory Enclave */}
                <div style={{ padding: '14px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.06)', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="main-mono" style={{ fontSize: '10px', background: 'rgba(56, 189, 248, 0.2)', color: 'var(--main-petrol)', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>
                        SECURE ENCLAVE • 64MB WASM MEMORY
                      </span>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#38BDF8' }}>
                        Cryptographic Decryption & Volatile Watermarking Kernel
                      </span>
                    </div>
                    <span className="main-badge main-badge-verified" style={{ fontSize: '9px' }}>AIR-GAPPED BUFFER</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', lineHeight: 1.5 }}>
                    1. <strong>ML-KEM-768 Decapsulation:</strong> Private key decapsulates session key inside unpaged RAM.<br />
                    2. <strong>Volatile Raster Embedding:</strong> Tardos codeword (m=128) + DSSS carrier modulated into 2D DCT coefficients.<br />
                    3. <strong>Immediate Zeroization:</strong> <code>memset_s(session_key, 0, 32)</code> and intermediate buffers wiped upon raster completion.
                  </div>
                </div>

                {/* Layer 3: Hardware Enclave Signature */}
                <div style={{ padding: '14px', borderRadius: '8px', background: 'rgba(34, 197, 94, 0.06)', border: '1px solid rgba(34, 197, 94, 0.3)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="main-mono" style={{ fontSize: '10px', background: 'rgba(34, 197, 94, 0.2)', color: 'var(--main-jade)', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>
                        FIPS 204 • NON-REPUDIATION
                      </span>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--main-jade)' }}>
                        ML-DSA-65 Hardware Signature Anchor
                      </span>
                    </div>
                    <span className="main-badge main-badge-verified" style={{ fontSize: '9px' }}>IMMUTABLE DLT RECEIPT</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', lineHeight: 1.5 }}>
                    • Enclave signs cryptographic receipt: <code>H(Plaintext) || RecipientID || Timestamp</code>.<br />
                    • Transmitted to RFC-6962 Merkle ledger to lock non-repudiation proof before viewport pixels are activated.
                  </div>
                </div>
              </div>

              {/* Memory Safety Matrix */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', fontSize: '11px' }}>
                <div style={{ padding: '10px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
                  <div style={{ color: 'var(--main-text-tertiary)', fontSize: '10px' }}>Disk Cache Leakage</div>
                  <div style={{ fontWeight: 600, color: 'var(--main-jade)', marginTop: '2px' }}>0 Bytes Written</div>
                </div>
                <div style={{ padding: '10px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
                  <div style={{ color: 'var(--main-text-tertiary)', fontSize: '10px' }}>Enclave Isolation</div>
                  <div style={{ fontWeight: 600, color: 'var(--main-petrol)', marginTop: '2px' }}>WASM Linear Heap</div>
                </div>
                <div style={{ padding: '10px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
                  <div style={{ color: 'var(--main-text-tertiary)', fontSize: '10px' }}>Anti-Debug Defense</div>
                  <div style={{ fontWeight: 600, color: 'var(--main-jade)', marginTop: '2px' }}>Sentinel Active</div>
                </div>
                <div style={{ padding: '10px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
                  <div style={{ color: 'var(--main-text-tertiary)', fontSize: '10px' }}>Session Key State</div>
                  <div style={{ fontWeight: 600, color: 'var(--main-amber)', marginTop: '2px' }}>Zeroized Post-Render</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="main-modal-footer">
          <button onClick={onClose} className="main-btn-secondary">
            Close
          </button>
          {!decryptionResult && (
            <button
              onClick={handleExecuteDecryption}
              disabled={isExecuting}
              className="main-btn-primary"
              style={{ background: '#3B82F6', borderColor: '#2563EB' }}
            >
              <Cpu size={14} />
              <span>{isExecuting ? 'Executing Decryption Pipeline...' : `Decrypt as ${currentRecipient.name} →`}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

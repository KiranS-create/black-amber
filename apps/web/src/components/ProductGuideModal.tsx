import React, { useState } from 'react';
import { 
  X, 
  CheckCircle2, 
  ChevronRight, 
  ChevronLeft, 
  Play, 
  Shield, 
  Lock, 
  Unlock, 
  Database, 
  Search, 
  Building
} from 'lucide-react';

interface ProductGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
  setActiveTab: (tab: any) => void;
  onTriggerDecryption: () => Promise<void>;
  onTriggerLeakAnalysis: (scenarioId: string) => Promise<void>;
  onTriggerLedgerTamper: () => void;
}

export const ProductGuideModal: React.FC<ProductGuideModalProps> = ({
  isOpen,
  onClose,
  setActiveTab,
  onTriggerDecryption,
  onTriggerLeakAnalysis,
  onTriggerLedgerTamper
}) => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [actionState, setActionState] = useState<{ loading: boolean; completed: boolean; message: string | null }>({
    loading: false,
    completed: false,
    message: null
  });

  if (!isOpen) return null;

  const steps = [
    {
      step: 1,
      title: 'Post-Quantum Principal Key Isolation',
      subtitle: 'NIST Standardized ML-KEM-768 & ML-DSA-65',
      icon: Shield,
      color: 'var(--petrol)',
      tabTarget: 'recipients',
      narrative: 'Each authorized recipient (Sarah, Marcus, Aris) is provisioned with mathematically isolated Post-Quantum Cryptographic (PQC) keypairs. Key encapsulation uses ML-KEM-768 (NIST FIPS 203) and provenance event signing uses ML-DSA-65 (NIST FIPS 204). Private keys strictly remain within recipient client boundaries.',
      keyPoints: [
        'ML-KEM-768 public key (1,184 bytes) for quantum-resistant symmetric key encapsulation',
        'ML-DSA-65 verification key (1,952 bytes) for non-repudiation provenance signatures',
        'Cryptographic isolation: packages contain zero cross-recipient key material'
      ],
      actionLabel: 'Inspect Recipient Principals',
      onAction: async () => {
        setActiveTab('recipients');
        setActionState({ loading: false, completed: true, message: 'Navigated to enrolled recipient identities and PQC public keys.' });
      }
    },
    {
      step: 2,
      title: 'Encrypted Multi-Recipient Document Release',
      subtitle: 'Single AES-256-GCM Payload + Per-Recipient ML-KEM Encapsulation',
      icon: Lock,
      color: 'var(--slate-blue)',
      tabTarget: 'releases',
      narrative: 'When headquarters distributes a classified document, the file is encrypted ONCE using AES-256-GCM with an ephemeral 256-bit key. That single key is encapsulated separately for each authorized principal via their ML-KEM-768 public keys. Eliminates multi-gigabyte re-encryption overhead while preserving independent recipient attribution.',
      keyPoints: [
        'Single encrypted payload shared across all recipients (O(1) storage scaling)',
        'Per-recipient ML-KEM key capsules containing wrapped 256-bit symmetric session keys',
        'Original document hash linked to immutable release context'
      ],
      actionLabel: 'View Encrypted Release Packages',
      onAction: async () => {
        setActiveTab('releases');
        setActionState({ loading: false, completed: true, message: 'Navigated to AES-256-GCM envelope and ML-KEM-768 capsules.' });
      }
    },
    {
      step: 3,
      title: 'Decryption & Non-Repudiation Provenance',
      subtitle: 'ML-DSA-65 Decryption Event Signing to Ledger',
      icon: Unlock,
      color: 'var(--amber)',
      tabTarget: 'releases',
      narrative: 'When Marcus Vance initiates decryption, his client decapsulates the session key, verifies the AES-GCM authentication tag, embeds an authenticated cryptographic attribution marker, and immediately signs an ML-DSA-65 Decryption Provenance Event that is committed to the immutable audit ledger before document access is granted.',
      keyPoints: [
        'Non-repudiation: Recipient cannot deny having decrypted and possessed the plaintext',
        'Automated watermark/marker embedding occurs at client decryption boundary',
        'Provenance event logged immutably to the ledger'
      ],
      actionLabel: 'Execute Decryption Simulation',
      onAction: async () => {
        setActionState({ loading: true, completed: false, message: 'Decapsulating ML-KEM-768 and signing ML-DSA-65 event…' });
        await onTriggerDecryption();
        setActiveTab('releases');
        setActionState({ loading: false, completed: true, message: 'Decryption completed. Plaintext decrypted and signed event committed to ledger.' });
      }
    },
    {
      step: 4,
      title: 'Tamper-Evident Hash-Chained Audit Ledger',
      subtitle: 'SHA-256 Block Linkage & Linear Chain Verification',
      icon: Database,
      color: 'var(--jade)',
      tabTarget: 'ledger',
      narrative: 'All lifecycle actions (Genesis, Envelope Release, Decryption, Provenance Signing) are committed to an immutable append-only hash-chained ledger. Every block pins the SHA-256 hash of its predecessor. Any modification immediately invalidates all downstream blocks.',
      keyPoints: [
        'Deterministic hash-chain verification runs locally in O(N)',
        'Simulate real ledger tampering to observe instantaneous chain break detection',
        'Cryptographic receipts suitable for legal non-repudiation'
      ],
      actionLabel: 'Test Hash-Chain Integrity & Simulate Tamper',
      onAction: async () => {
        setActiveTab('ledger');
        onTriggerLedgerTamper();
        setActionState({ loading: false, completed: true, message: 'Simulated corruption on Block #1. Notice immediate chain break detection!' });
      }
    },
    {
      step: 5,
      title: 'Multi-Channel Bayesian Evidence Fusion',
      subtitle: 'Spatial DSSS + Tardos Traitor Tracing Matrix + Fail-Closed Decision Guard',
      icon: Search,
      color: 'var(--crimson)',
      tabTarget: 'investigations',
      narrative: 'When a leaked artifact is recovered, the forensic engine autonomously extracts physical watermark carriers and Tardos traitor tracing codewords. Evidence channels are fused under Bayesian Log-Likelihood Ratio bounds with strict anti-double-counting safeguards.',
      keyPoints: [
        'Fail-closed policy: Engine never guesses or forces attribution under ambiguity',
        'Strict decision boundary (Z >= 11.40, epsilon <= 10^-5 false alarm bound)',
        'Independent multi-channel correlation (Watermark, Tardos m=128, Ledger receipts)'
      ],
      actionLabel: 'Run Forensic Bayesian Analysis',
      onAction: async () => {
        setActionState({ loading: true, completed: false, message: 'Evaluating multi-channel evidence and calculating fused Log-Likelihood Ratio…' });
        await onTriggerLeakAnalysis('clean_bob');
        setActiveTab('investigations');
        setActionState({ loading: false, completed: true, message: 'Bayesian evidence fusion executed. Fused score exceeds Z=11.40 threshold.' });
      }
    },
    {
      step: 6,
      title: 'Enterprise Identity Directory Resolution',
      subtitle: 'Decoupled Forensic Identity Resolution (IdentityResolver)',
      icon: Building,
      color: 'var(--slate-blue)',
      tabTarget: 'directory',
      narrative: 'The forensic engine identifies an opaque principal ID from mathematical evidence. It then queries the enterprise Identity Directory to resolve the principal into an employee identity (Marcus Vance, Principal Cryptanalyst) with fail-soft resilience against directory outages.',
      keyPoints: [
        'Complete separation of forensic evidence principal from human directory identity',
        'Fail-soft directory caching: Offline resilience during Active Directory outages',
        'Historical preservation: Revoked identities remain attributed without deletion'
      ],
      actionLabel: 'Inspect Enterprise Directory',
      onAction: async () => {
        setActiveTab('directory');
        setActionState({ loading: false, completed: true, message: 'Inspected federated enterprise identities and directory resolution bindings.' });
      }
    }
  ];

  const current = steps[currentStep - 1];
  const StepIcon = current.icon;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(11, 16, 21, 0.8)',
        backdropFilter: 'blur(16px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}
      onClick={onClose}
    >
      <div
        className="workstation-card"
        style={{
          width: '100%',
          maxWidth: '680px',
          padding: 0,
          boxShadow: '0 24px 48px rgba(0, 0, 0, 0.5)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Top Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'var(--bg-elevated)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '4px',
                backgroundColor: 'rgba(76, 154, 154, 0.1)',
                color: current.color,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid var(--border-subtle)'
              }}
            >
              <StepIcon size={16} />
            </div>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-graphite)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.04em' }}>
                Architecture Walkthrough • Step {current.step} of {steps.length}
              </div>
              <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-ivory)' }}>
                {current.title}
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-graphite)',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Content Body */}
        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: '65vh', overflowY: 'auto' }}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: current.color, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            {current.subtitle}
          </div>

          <div style={{ fontSize: '13px', color: 'var(--text-slate)', lineHeight: 1.6 }}>
            {current.narrative}
          </div>

          <div
            style={{
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '4px',
              padding: '14px 16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}
          >
            <div style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)' }}>
              Core Technical Guarantees
            </div>
            {current.keyPoints.map((point, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '12px', color: 'var(--text-slate)', lineHeight: 1.45 }}>
                <CheckCircle2 size={14} style={{ color: 'var(--jade)', flexShrink: 0, marginTop: '2px' }} />
                <span>{point}</span>
              </div>
            ))}
          </div>

          {actionState.message && (
            <div
              style={{
                padding: '10px 14px',
                borderRadius: '4px',
                backgroundColor: 'rgba(76, 154, 154, 0.08)',
                border: '1px solid rgba(76, 154, 154, 0.2)',
                fontSize: '12px',
                color: 'var(--text-ivory)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <span>{actionState.message}</span>
            </div>
          )}

          {/* Action Trigger Button */}
          <button
            onClick={current.onAction}
            disabled={actionState.loading}
            className="btn-primary"
            style={{
              height: '38px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            <Play size={13} fill="currentColor" />
            <span>{actionState.loading ? 'Executing…' : current.actionLabel}</span>
          </button>
        </div>

        {/* Modal Bottom Stepper Controls */}
        <div
          style={{
            padding: '12px 20px',
            borderTop: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-elevated)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <button
            onClick={() => {
              if (currentStep > 1) {
                setCurrentStep(currentStep - 1);
                setActionState({ loading: false, completed: false, message: null });
              }
            }}
            disabled={currentStep === 1}
            className="btn-secondary"
            style={{
              padding: '4px 10px',
              fontSize: '11px',
              opacity: currentStep === 1 ? 0.4 : 1,
              cursor: currentStep === 1 ? 'not-allowed' : 'pointer'
            }}
          >
            <ChevronLeft size={13} />
            <span>Previous</span>
          </button>

          {/* Step dots */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {steps.map(s => (
              <button
                key={s.step}
                onClick={() => {
                  setCurrentStep(s.step);
                  setActionState({ loading: false, completed: false, message: null });
                }}
                style={{
                  width: s.step === currentStep ? '16px' : '6px',
                  height: '6px',
                  borderRadius: '3px',
                  backgroundColor: s.step === currentStep ? 'var(--petrol)' : 'var(--border-strong)',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                  transition: 'all var(--transition-fast)'
                }}
              />
            ))}
          </div>

          <button
            onClick={() => {
              if (currentStep < steps.length) {
                setCurrentStep(currentStep + 1);
                setActionState({ loading: false, completed: false, message: null });
              } else {
                onClose();
              }
            }}
            className="btn-primary"
            style={{
              padding: '4px 12px',
              fontSize: '11px'
            }}
          >
            <span>{currentStep === steps.length ? 'Close walkthrough' : 'Next step'}</span>
            <ChevronRight size={13} />
          </button>
        </div>
      </div>
    </div>
  );
};

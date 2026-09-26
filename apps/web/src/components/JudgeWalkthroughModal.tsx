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
  AlertTriangle,
  ArrowRight,
  Sparkles
} from 'lucide-react';

interface JudgeWalkthroughModalProps {
  isOpen: boolean;
  onClose: () => void;
  setActiveTab: (tab: any) => void;
  onTriggerDecryption: () => Promise<void>;
  onTriggerLeakAnalysis: (scenarioId: string) => Promise<void>;
  onTriggerLedgerTamper: () => void;
}

export const JudgeWalkthroughModal: React.FC<JudgeWalkthroughModalProps> = ({
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
      title: 'Post-Quantum Recipient Key Isolation',
      subtitle: 'NIST Standardized ML-KEM-768 & ML-DSA-65',
      icon: Shield,
      color: '#38bdf8',
      tabTarget: 'recipients',
      narrative: 'Each authorized recipient (Alice, Bob, Charlie) is provisioned with mathematically isolated Post-Quantum Cryptographic (PQC) keypairs. Key encapsulation uses ML-KEM-768 (Kyber-768 standard) and provenance event signing uses ML-DSA-65 (Dilithium3 standard). Private keys strictly remain within recipient boundaries.',
      keyPoints: [
        'ML-KEM-768 public key (1,184 bytes) for quantum-resistant symmetric key encapsulation',
        'ML-DSA-65 verification key (1,952 bytes) for non-repudiation provenance signatures',
        'Cryptographic isolation: packages contain zero cross-recipient key material'
      ],
      actionLabel: 'Inspect Recipient Identities (GET /recipients)',
      onAction: async () => {
        setActiveTab('recipients');
        setActionState({ loading: false, completed: true, message: 'Inspecting enrolled recipient identities and PQC public keys.' });
      }
    },
    {
      step: 2,
      title: 'Encrypted Multi-Recipient Document Release',
      subtitle: 'Single AES-256-GCM Payload + Per-Recipient ML-KEM Encapsulation',
      icon: Lock,
      color: '#a855f7',
      tabTarget: 'release',
      narrative: 'When headquarters distributes a confidential document, the file is encrypted ONCE using AES-256-GCM with an ephemeral 256-bit key. That single key is encapsulated separately for Alice, Bob, and Charlie via their ML-KEM-768 public keys. Eliminates multi-gigabyte re-encryption overhead.',
      keyPoints: [
        'Single encrypted payload shared across all recipients (O(1) storage scaling)',
        'Per-recipient ML-KEM key capsules containing wrapped 256-bit symmetric session keys',
        'ORIGINAL_DOCUMENT_HASH linked to release context rel_20260926_001'
      ],
      actionLabel: 'View Encrypted Release Packages (GET /releases)',
      onAction: async () => {
        setActiveTab('release');
        setActionState({ loading: false, completed: true, message: 'Inspected AES-256-GCM envelope and ML-KEM-768 capsules.' });
      }
    },
    {
      step: 3,
      title: 'Decryption & Non-Repudiation Provenance',
      subtitle: 'ML-DSA-65 Decryption Event Signing to Ledger',
      icon: Unlock,
      color: '#fb923c',
      tabTarget: 'decrypt',
      narrative: 'When Bob initiates decryption, his client decapsulates the session key, verifies the AES-GCM tag, embeds an authenticated cryptographic attribution marker, and immediately signs an ML-DSA-65 Decryption Provenance Event that is submitted to the immutable audit ledger before document access is granted.',
      keyPoints: [
        'Non-repudiation: Bob cannot deny having decrypted and possessed the plaintext',
        'Automated watermark/marker embedding occurs at client decryption boundary',
        'Provenance event logged immutably: Event ID evt_dec_bob_002'
      ],
      actionLabel: 'Execute Decryption (POST /releases/{id}/decrypt)',
      onAction: async () => {
        setActionState({ loading: true, completed: false, message: 'Decapsulating ML-KEM-768 and signing ML-DSA-65 event...' });
        await onTriggerDecryption();
        setActiveTab('decrypt');
        setActionState({ loading: false, completed: true, message: 'Bob successfully decrypted package & logged signed provenance event!' });
      }
    },
    {
      step: 4,
      title: 'Tamper-Evident SHA-256 Hash-Chained Ledger',
      subtitle: 'Mathematical Immutability & Tamper Simulation Demo',
      icon: Database,
      color: '#10b981',
      tabTarget: 'ledger',
      narrative: 'Every distribution and decryption event is linked cryptographically in a hash chain: Hash_n = SHA256(Hash_{n-1} || event_id || artifact_hash || signature). Any modification of a historical block instantly breaks the cryptographic chain tip and is caught during ledger verification.',
      keyPoints: [
        'Cryptographic hash chaining prevents retroactive log alteration or deletion',
        'Non-repudiation signatures linked directly into block hashes',
        'Interactive Tamper Simulator demonstrates instant detection of corrupted logs'
      ],
      actionLabel: 'Inspect Ledger & Verify Chain (GET /ledger/verify)',
      onAction: async () => {
        setActiveTab('ledger');
        setActionState({ loading: false, completed: true, message: 'Ledger explorer active. Try clicking "Simulate Block Tamper" to see instant chain failure!' });
      }
    },
    {
      step: 5,
      title: 'Multi-Channel Bayesian Evidence Fusion',
      subtitle: 'Robust Attribution of Leaked Document',
      icon: Search,
      color: '#38bdf8',
      tabTarget: 'leak',
      narrative: 'A leaked document is analyzed through our multi-channel Bayesian engine: spatial watermarks (Barker-13/Reed-Solomon), Tardos fingerprint scores (m=128), ML-DSA-65 provenance signatures, and ledger verification. Channel measurements are weighted by reliability discounts (rho_i) with anti-double-counting bounds.',
      keyPoints: [
        'Candidate Bob attributed with HIGH confidence (Fused LLR: 18.08 >= threshold 8.0)',
        'Candidate separation margin Delta = 18.08 >= threshold 3.0',
        'All independent and derived evidence channels corroborate identity'
      ],
      actionLabel: 'Run Bayesian Attribution (POST /analyze)',
      onAction: async () => {
        setActionState({ loading: true, completed: false, message: 'Executing Bayesian Multi-Channel Evidence Fusion...' });
        await onTriggerLeakAnalysis('clean_bob');
        setActiveTab('leak');
        setActionState({ loading: false, completed: true, message: 'Attribution Complete: Bob Martinez attributed with HIGH confidence!' });
      }
    },
    {
      step: 6,
      title: 'Adversarial Robustness & Fail-Closed Policy',
      subtitle: 'Axiom: Abstention is strictly preferred over False Accusation',
      icon: AlertTriangle,
      color: '#ec4899',
      tabTarget: 'attack_lab',
      narrative: 'In high-consequence forensic investigations, false positive accusations are unacceptable. Our fail-closed engine tests against adversarial attacks: raw leaks (NO_SIGNAL), forged HMACs (INSUFFICIENT_EVIDENCE), framed identities, and cross-document scope clashes (CONFLICT), strictly returning ABSTAIN in every adversarial scenario.',
      keyPoints: [
        'Protection of innocent parties against targeted framing attacks',
        'Print-Scan-Camera 3D perspective corrected via OpenCV homography',
        'Fail-closed decision policy strictly enforces abstention on weak signals'
      ],
      actionLabel: 'Launch Adversarial Attack Lab',
      onAction: async () => {
        setActiveTab('attack_lab');
        setActionState({ loading: false, completed: true, message: 'Adversarial stress-test laboratory active.' });
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
        backgroundColor: 'rgba(0, 0, 0, 0.55)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 110,
        padding: '20px'
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'var(--surface-elevated)',
          border: '1px solid var(--border-strong)',
          borderRadius: 'var(--radius-lg)',
          maxWidth: '800px',
          width: '100%',
          boxShadow: 'var(--shadow-lg)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: '90vh'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: 'var(--space-4) var(--space-6)',
            backgroundColor: 'var(--surface-subtle)',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={18} style={{ color: 'var(--primary-text)' }} />
            <div>
              <h2 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 700, color: 'var(--text)' }}>
                AegisTrace Evaluation Walkthrough
              </h2>
              <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: 'var(--text-tertiary)' }}>
                Stage {currentStep} of {steps.length}: Live Interactive Demonstration Flow
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-tertiary)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: 'var(--radius-sm)'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Step Progress Indicators */}
        <div
          style={{
            display: 'flex',
            padding: 'var(--space-2) var(--space-6)',
            backgroundColor: 'var(--surface)',
            borderBottom: '1px solid var(--border)',
            gap: '8px'
          }}
        >
          {steps.map(s => (
            <div
              key={s.step}
              onClick={() => {
                setCurrentStep(s.step);
                setActionState({ loading: false, completed: false, message: null });
              }}
              style={{
                flex: 1,
                height: '4px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: s.step === currentStep 
                  ? 'var(--primary)' 
                  : (s.step < currentStep ? 'var(--success)' : 'var(--border)'),
                cursor: 'pointer',
                transition: 'all var(--transition-fast)'
              }}
              title={`Stage ${s.step}: ${s.title}`}
            />
          ))}
        </div>

        {/* Content Body */}
        <div style={{ padding: 'var(--space-6)', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
            <div
              style={{
                backgroundColor: 'var(--surface-subtle)',
                border: '1px solid var(--border)',
                padding: '10px',
                borderRadius: 'var(--radius-md)',
                color: 'var(--primary-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}
            >
              <StepIcon size={24} />
            </div>
            <div>
              <span style={{ fontSize: '10.5px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--primary-text)' }}>
                Stage {current.step} Evaluation
              </span>
              <h3 style={{ margin: '2px 0 2px 0', fontSize: 'var(--text-lg)', color: 'var(--text)', fontWeight: 700 }}>
                {current.title}
              </h3>
              <p style={{ margin: 0, fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                {current.subtitle}
              </p>
            </div>
          </div>

          <p style={{ fontSize: 'var(--text-base)', lineHeight: 1.5, color: 'var(--text-secondary)', margin: 0 }}>
            {current.narrative}
          </p>

          {/* Key architectural bullet points */}
          <div
            style={{
              backgroundColor: 'var(--surface-subtle)',
              padding: 'var(--space-4)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)'
            }}
          >
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '6px' }}>
              Cryptographic & Architectural Proofs
            </div>
            <ul style={{ margin: 0, paddingLeft: '18px', color: 'var(--text)', fontSize: 'var(--text-xs)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {current.keyPoints.map((kp, i) => (
                <li key={i}>{kp}</li>
              ))}
            </ul>
          </div>

          {/* Live Action Trigger */}
          <div
            style={{
              backgroundColor: 'var(--surface)',
              border: '1px dashed var(--border-strong)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px'
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: 'var(--text-base)', color: 'var(--text)' }}>
                Interactive Action for Evaluators
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Trigger this operation in real time against the backend or local simulator.
              </div>
            </div>

            <button
              onClick={current.onAction}
              disabled={actionState.loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                backgroundColor: 'var(--primary)',
                color: '#ffffff',
                border: 'none',
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                fontWeight: 600,
                fontSize: 'var(--text-xs)',
                cursor: 'pointer',
                transition: 'background var(--transition-fast)'
              }}
              onMouseEnter={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary-hover)')}
              onMouseLeave={e => ((e.currentTarget as HTMLElement).style.backgroundColor = 'var(--primary)')}
            >
              <Play size={13} fill="#ffffff" />
              <span>{actionState.loading ? 'Executing Step...' : current.actionLabel}</span>
            </button>
          </div>

          {actionState.message && (
            <div
              style={{
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--success-subtle)',
                border: '1px solid var(--success-border)',
                color: 'var(--success-text)',
                fontSize: 'var(--text-xs)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <CheckCircle2 size={15} />
              <span>{actionState.message}</span>
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        <div
          style={{
            padding: 'var(--space-3) var(--space-6)',
            backgroundColor: 'var(--surface-subtle)',
            borderTop: '1px solid var(--border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
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
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              backgroundColor: 'var(--surface)',
              color: currentStep === 1 ? 'var(--text-disabled)' : 'var(--text)',
              border: '1px solid var(--border)',
              padding: '6px 14px',
              borderRadius: 'var(--radius-md)',
              fontWeight: 600,
              fontSize: 'var(--text-xs)',
              cursor: currentStep === 1 ? 'not-allowed' : 'pointer'
            }}
          >
            <ChevronLeft size={14} />
            <span>Previous</span>
          </button>

          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
            {currentStep} / {steps.length}
          </span>

          {currentStep < steps.length ? (
            <button
              onClick={() => {
                setCurrentStep(currentStep + 1);
                setActionState({ loading: false, completed: false, message: null });
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                backgroundColor: 'var(--primary)',
                color: '#ffffff',
                border: 'none',
                padding: '6px 14px',
                borderRadius: 'var(--radius-md)',
                fontWeight: 600,
                fontSize: 'var(--text-xs)',
                cursor: 'pointer'
              }}
            >
              <span>Next Stage</span>
              <ChevronRight size={14} />
            </button>
          ) : (
            <button
              onClick={onClose}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                backgroundColor: 'var(--success)',
                color: '#ffffff',
                border: 'none',
                padding: '6px 14px',
                borderRadius: 'var(--radius-md)',
                fontWeight: 600,
                fontSize: 'var(--text-xs)',
                cursor: 'pointer'
              }}
            >
              <span>Complete Walkthrough</span>
              <CheckCircle2 size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

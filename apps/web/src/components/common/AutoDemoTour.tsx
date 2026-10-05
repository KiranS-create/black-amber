import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Play, 
  Pause, 
  SkipForward, 
  SkipBack, 
  Volume2, 
  VolumeX, 
  X, 
  Sparkles, 
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';
import { MainTabId } from '../main/MainSidebar';

export interface AutoDemoTourProps {
  isOpen: boolean;
  onClose: () => void;
  // App navigation and modal control hooks
  onSetViewMode: (mode: 'landing' | 'login' | 'workstation') => void;
  onLoginDemo: () => Promise<void>;
  onSetTab: (tab: MainTabId) => void;
  onOpenComparator: (recipientName?: string, docName?: string) => void;
  onCloseComparator: () => void;
  onOpenCollusion: () => void;
  onCloseCollusion: () => void;
  onOpenAirGap: () => void;
  onCloseAirGap: () => void;
  onOpenCertificate: () => void;
  onCloseCertificate: () => void;
  onOpenStandaloneVerifier: () => void;
  onCloseStandaloneVerifier: () => void;
  onTriggerPipeline?: () => void;
}

interface TourStep {
  id: number;
  title: string;
  badge: string;
  speech: string;
  action: (props: AutoDemoTourProps) => Promise<void> | void;
  durationMs: number;
}

export const AutoDemoTour: React.FC<AutoDemoTourProps> = ({
  isOpen,
  onClose,
  onSetViewMode,
  onLoginDemo,
  onSetTab,
  onOpenComparator,
  onCloseComparator,
  onOpenCollusion,
  onCloseCollusion,
  onOpenAirGap,
  onCloseAirGap,
  onOpenCertificate,
  onCloseCertificate,
  onOpenStandaloneVerifier,
  onCloseStandaloneVerifier,
  onTriggerPipeline
}) => {
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [voicesLoaded, setVoicesLoaded] = useState<boolean>(false);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isTransitioningRef = useRef<boolean>(false);

  // Define the 8 exact Tour Steps matching the website flow
  const STEPS: TourStep[] = [
    {
      id: 1,
      title: "The Smartphone Camera Blindspot",
      badge: "Step 1 of 8 • Introduction & Login",
      speech: "No firewall in the world can stop an employee taking a photo of their laptop screen with a phone. This is AegisTrace—we make every document self-identifying, so you always know who leaked it. Let's log in with one click.",
      durationMs: 10000,
      action: async (p) => {
        p.onCloseComparator();
        p.onCloseCollusion();
        p.onCloseAirGap();
        p.onCloseCertificate();
        p.onCloseStandaloneVerifier();
        p.onSetViewMode('login');
        await new Promise(r => setTimeout(r, 1200));
        await p.onLoginDemo();
      }
    },
    {
      id: 2,
      title: "Mission Control • Zero Storage Waste",
      badge: "Step 2 of 8 • Overview Dashboard",
      speech: "Welcome to the command workstation. First major breakthrough: Zero server storage waste. The server keeps one master file instead of fifty duplicate copies, eliminating gigabytes of server bloat.",
      durationMs: 9500,
      action: (p) => {
        p.onCloseComparator();
        p.onCloseCollusion();
        p.onCloseCertificate();
        p.onCloseStandaloneVerifier();
        p.onSetViewMode('workstation');
        p.onSetTab('overview');
      }
    },
    {
      id: 3,
      title: "Document Protection & Memory Synthesis",
      badge: "Step 3 of 8 • Documents Registry",
      speech: "Let's go to Documents. When released to Sarah Jenkins and Marcus Vance, each officer's computer weaves an invisible tracking pattern directly in memory the exact second they open it.",
      durationMs: 10000,
      action: (p) => {
        p.onCloseComparator();
        p.onCloseCollusion();
        p.onSetTab('documents');
      }
    },
    {
      id: 4,
      title: "The Invisibility Test • Split Slider & Spectral View",
      badge: "Step 4 of 8 • Visual Comparator",
      speech: "Does this watermark hurt readability? Not at all. Looking at this split slider: original on the left, Marcus Vance's copy on the right. They are 100% visually identical. But flip on the spectral lens—there is the invisible mathematical tracking pattern, hidden deep in the pixel frequencies.",
      durationMs: 14000,
      action: (p) => {
        p.onOpenComparator('Marcus Vance', 'National_Defense_Protocol_2026.pdf');
      }
    },
    {
      id: 5,
      title: "The Leak • Finding the Culprit in 800ms",
      badge: "Step 5 of 8 • Forensic Attribution",
      speech: "Now, let's catch a leaker. A photo was taken off a monitor at a 40-degree angle, with screen glare and heavy compression. In under 800 milliseconds, our engine dewarps the angle, clears the glare, and locks in the suspect: Marcus Vance.",
      durationMs: 13000,
      action: (p) => {
        p.onCloseComparator();
        p.onSetTab('investigations');
        if (p.onTriggerPipeline) {
          p.onTriggerPipeline();
        }
      }
    },
    {
      id: 6,
      title: "Tardos Collusion Defense & Emergency Killswitch",
      badge: "Step 6 of 8 • Collusion Lab & Quarantine",
      speech: "What if two rogue officers team up to wash out the watermark? Our traitor-tracing algorithms unmask both conspirators at once. And with one click on Sovereign Quarantine, Marcus Vance's decryption keys are purged across the entire network.",
      durationMs: 12500,
      action: async (p) => {
        p.onOpenCollusion();
        await new Promise(r => setTimeout(r, 6000));
        p.onCloseCollusion();
      }
    },
    {
      id: 7,
      title: "Courtroom-Ready Proof • Section 63 BSA Docket",
      badge: "Step 7 of 8 • Evidence Ledger & Court Docket",
      speech: "Under Section 63 of India's Bharatiya Sakshya Adhiniyam, digital evidence requires strict custody. Our two-officer quorum requires both the forensic scientist and the provost marshal to sign off, generating a magistrate-ready certificate with a scannable verification QR code.",
      durationMs: 13500,
      action: (p) => {
        p.onCloseCollusion();
        p.onSetTab('evidence');
        p.onOpenCertificate();
      }
    },
    {
      id: 8,
      title: "100% Offline in Submarine Mode",
      badge: "Step 8 of 8 • Air-Gapped Standalone Verifier",
      speech: "Finally, notice I am logging out completely. This standalone verifier runs 100% offline inside your browser. No internet, no cloud, no data leaks. It works on a naval submarine at sea or inside an air-gapped courtroom. Over 1,200 automated tests passed. Zero duplicate storage. Unshakeable proof. That is AegisTrace. Thanks for watching!",
      durationMs: 16000,
      action: (p) => {
        p.onCloseCertificate();
        p.onOpenStandaloneVerifier();
      }
    }
  ];

  // Initialize Speech Synthesis Voices
  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;

    const populateVoices = () => {
      const allVoices = window.speechSynthesis.getVoices();
      if (allVoices.length > 0) {
        setVoicesLoaded(true);
        // Find best natural English voice (Google US English, Samantha, Microsoft David/Natural, etc.)
        const preferred = allVoices.find(v => 
          (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Daniel') || v.name.includes('David')) &&
          v.lang.startsWith('en')
        ) || allVoices.find(v => v.lang.startsWith('en')) || allVoices[0];
        
        setSelectedVoice(preferred || null);
      }
    };

    populateVoices();
    window.speechSynthesis.onvoiceschanged = populateVoices;

    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Handle Speech & Step Transitions
  const executeStep = useCallback((stepIdx: number) => {
    if (stepIdx < 0 || stepIdx >= STEPS.length) {
      // Tour completed
      setIsPlaying(false);
      return;
    }

    isTransitioningRef.current = true;
    const step = STEPS[stepIdx];

    // 1. Run the UI action
    step.action({
      isOpen,
      onClose,
      onSetViewMode,
      onLoginDemo,
      onSetTab,
      onOpenComparator,
      onCloseComparator,
      onOpenCollusion,
      onCloseCollusion,
      onOpenAirGap,
      onCloseAirGap,
      onOpenCertificate,
      onCloseCertificate,
      onOpenStandaloneVerifier,
      onCloseStandaloneVerifier,
      onTriggerPipeline
    });

    // 2. Speak or Set Timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    const advanceToNext = () => {
      if (stepIdx + 1 < STEPS.length) {
        setCurrentStep(stepIdx + 1);
      } else {
        setIsPlaying(false);
      }
    };

    if (!isMuted && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(step.speech);
      if (selectedVoice) {
        utterance.voice = selectedVoice;
      }
      utterance.rate = 1.04;
      utterance.pitch = 1.0;

      utterance.onend = () => {
        timerRef.current = setTimeout(() => {
          advanceToNext();
        }, 800);
      };

      utterance.onerror = () => {
        timerRef.current = setTimeout(() => {
          advanceToNext();
        }, step.durationMs);
      };

      window.speechSynthesis.speak(utterance);

      // Fallback timer if speech takes too long or halts
      timerRef.current = setTimeout(() => {
        advanceToNext();
      }, step.durationMs + 2000);
    } else {
      // Voice muted: rely on timed duration
      timerRef.current = setTimeout(() => {
        advanceToNext();
      }, step.durationMs);
    }

    isTransitioningRef.current = false;
  }, [STEPS, isMuted, selectedVoice, isOpen, onClose, onSetViewMode, onLoginDemo, onSetTab, onOpenComparator, onCloseComparator, onOpenCollusion, onCloseCollusion, onOpenAirGap, onCloseAirGap, onOpenCertificate, onCloseCertificate, onOpenStandaloneVerifier, onCloseStandaloneVerifier, onTriggerPipeline]);

  // Trigger step when currentStep or isPlaying changes
  useEffect(() => {
    if (!isOpen) {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      if (timerRef.current) clearTimeout(timerRef.current);
      return;
    }

    if (isPlaying) {
      executeStep(currentStep);
    } else {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      if (timerRef.current) clearTimeout(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isOpen, currentStep, isPlaying, executeStep]);

  if (!isOpen) return null;

  const activeStep = STEPS[currentStep] || STEPS[0];
  const progressPercent = Math.round(((currentStep + 1) / STEPS.length) * 100);

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        left: '50%',
        transform: 'translateX(-50%)',
        width: 'min(780px, 94vw)',
        zIndex: 9999,
        background: 'rgba(7, 10, 15, 0.88)',
        backdropFilter: 'blur(24px) saturate(180%)',
        WebkitBackdropFilter: 'blur(24px) saturate(180%)',
        border: '1px solid rgba(56, 189, 248, 0.35)',
        borderRadius: '24px',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(56, 189, 248, 0.15)',
        padding: '18px 24px',
        color: '#FFFFFF',
        fontFamily: 'var(--font-sans, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif)'
      }}
    >
      {/* Top Meta Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span 
            style={{ 
              display: 'inline-flex', 
              alignItems: 'center', 
              gap: '6px', 
              fontSize: '11px', 
              fontWeight: 700, 
              padding: '3px 9px', 
              borderRadius: '9999px',
              background: isPlaying ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
              border: `1px solid ${isPlaying ? '#10B981' : '#F59E0B'}`,
              color: isPlaying ? '#34D399' : '#FBBF24',
              letterSpacing: '0.04em',
              textTransform: 'uppercase'
            }}
          >
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: isPlaying ? '#10B981' : '#F59E0B' }} />
            {isPlaying ? 'Live Auto-Demo' : 'Demo Paused'}
          </span>
          <span style={{ fontSize: '12px', color: '#94A3B8', fontWeight: 600 }}>
            {activeStep.badge}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '11.5px', color: '#38BDF8', fontWeight: 650 }}>
            {progressPercent}% Complete
          </span>
          <button
            onClick={() => {
              if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
                window.speechSynthesis.cancel();
              }
              onClose();
            }}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94A3B8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              padding: '4px'
            }}
            title="Exit Tour"
            aria-label="Exit Tour"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Spoken Narration Subtitle Box */}
      <div
        style={{
          background: 'rgba(17, 24, 39, 0.65)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '14px',
          padding: '12px 16px',
          marginBottom: '12px',
          minHeight: '48px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}
      >
        <Sparkles size={18} style={{ color: '#38BDF8', flexShrink: 0 }} />
        <p style={{ margin: 0, fontSize: '13.5px', lineHeight: 1.5, color: '#F8FAFC', fontWeight: 450 }}>
          &ldquo;{activeStep.speech}&rdquo;
        </p>
      </div>

      {/* Progress Track */}
      <div 
        style={{ 
          width: '100%', 
          height: '4px', 
          background: 'rgba(255, 255, 255, 0.1)', 
          borderRadius: '9999px',
          overflow: 'hidden',
          marginBottom: '14px'
        }}
      >
        <div 
          style={{ 
            height: '100%', 
            width: `${progressPercent}%`, 
            background: 'linear-gradient(90deg, #0284C7, #38BDF8)',
            borderRadius: '9999px',
            transition: 'width 0.4s ease'
          }} 
        />
      </div>

      {/* Controller Buttons Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => {
              if (currentStep > 0) setCurrentStep(currentStep - 1);
            }}
            disabled={currentStep === 0}
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '9999px',
              padding: '6px 12px',
              color: currentStep === 0 ? '#64748B' : '#FFFFFF',
              cursor: currentStep === 0 ? 'not-allowed' : 'pointer',
              fontSize: '12px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <SkipBack size={13} />
            <span>Prev</span>
          </button>

          <button
            onClick={() => setIsPlaying(!isPlaying)}
            style={{
              background: isPlaying ? '#0284C7' : '#10B981',
              border: 'none',
              borderRadius: '9999px',
              padding: '6px 16px',
              color: '#FFFFFF',
              cursor: 'pointer',
              fontSize: '12.5px',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 4px 14px rgba(2, 132, 199, 0.4)'
            }}
          >
            {isPlaying ? <Pause size={13} /> : <Play size={13} />}
            <span>{isPlaying ? 'Pause' : 'Resume'}</span>
          </button>

          <button
            onClick={() => {
              if (currentStep + 1 < STEPS.length) setCurrentStep(currentStep + 1);
            }}
            disabled={currentStep + 1 >= STEPS.length}
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '9999px',
              padding: '6px 12px',
              color: currentStep + 1 >= STEPS.length ? '#64748B' : '#FFFFFF',
              cursor: currentStep + 1 >= STEPS.length ? 'not-allowed' : 'pointer',
              fontSize: '12px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <span>Next</span>
            <SkipForward size={13} />
          </button>
        </div>

        {/* Voice Toggle & Exit */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => {
              if (!isMuted && typeof window !== 'undefined' && 'speechSynthesis' in window) {
                window.speechSynthesis.cancel();
              }
              setIsMuted(!isMuted);
            }}
            style={{
              background: isMuted ? 'rgba(239, 68, 68, 0.15)' : 'rgba(56, 189, 248, 0.15)',
              border: `1px solid ${isMuted ? 'rgba(239, 68, 68, 0.3)' : 'rgba(56, 189, 248, 0.3)'}`,
              borderRadius: '9999px',
              padding: '6px 12px',
              color: isMuted ? '#EF4444' : '#38BDF8',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 650,
              display: 'flex',
              alignItems: 'center',
              gap: '5px'
            }}
            title={isMuted ? "Unmute Voice Narration" : "Mute Voice Narration"}
          >
            {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
            <span>{isMuted ? 'Voice Muted' : 'Voice Active'}</span>
          </button>

          <button
            onClick={() => {
              if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
                window.speechSynthesis.cancel();
              }
              onClose();
            }}
            style={{
              background: 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: '9999px',
              padding: '6px 12px',
              color: '#CBD5E1',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600
            }}
          >
            Exit Tour
          </button>
        </div>
      </div>
    </div>
  );
};

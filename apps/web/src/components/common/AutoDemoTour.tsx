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
  ChevronDown, 
  ChevronUp 
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
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);

  // Independent timer refs to prevent double-advancing race conditions
  const fallbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const nextTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearAllTimers = useCallback(() => {
    if (fallbackTimerRef.current) {
      clearTimeout(fallbackTimerRef.current);
      fallbackTimerRef.current = null;
    }
    if (nextTimerRef.current) {
      clearTimeout(nextTimerRef.current);
      nextTimerRef.current = null;
    }
  }, []);

  // Define the 8 exact Tour Steps matching the website flow
  const STEPS: TourStep[] = [
    {
      id: 1,
      title: "The Smartphone Camera Blindspot",
      badge: "Step 1/8 • Intro & Login",
      speech: "No firewall in the world can stop an employee taking a photo of their laptop screen with a phone. This is AegisTrace—we make every document self-identifying, so you always know who leaked it. Let's log in with one click.",
      durationMs: 9500,
      action: async (p) => {
        p.onCloseComparator();
        p.onCloseCollusion();
        p.onCloseAirGap();
        p.onCloseCertificate();
        p.onCloseStandaloneVerifier();
        await p.onLoginDemo();
        p.onSetViewMode('workstation');
        p.onSetTab('overview');
      }
    },
    {
      id: 2,
      title: "Mission Control • Zero Storage Waste",
      badge: "Step 2/8 • Overview",
      speech: "Welcome to the command workstation. First major breakthrough: Zero server storage waste. The server keeps one master file instead of fifty duplicate copies, eliminating gigabytes of server bloat.",
      durationMs: 9000,
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
      badge: "Step 3/8 • Documents",
      speech: "Let's go to Documents. When released to Sarah Jenkins and Marcus Vance, each officer's computer weaves an invisible tracking pattern directly in memory the exact second they open it.",
      durationMs: 9500,
      action: (p) => {
        p.onCloseComparator();
        p.onCloseCollusion();
        p.onSetTab('documents');
      }
    },
    {
      id: 4,
      title: "The Invisibility Test • Split Slider",
      badge: "Step 4/8 • Comparator",
      speech: "Does this watermark hurt readability? Not at all. Looking at this split slider: original on the left, Marcus Vance's copy on the right. They are visually identical, but contain an invisible mathematical tracking pattern.",
      durationMs: 12000,
      action: (p) => {
        p.onOpenComparator('Marcus Vance', 'National_Defense_Protocol_2026.pdf');
      }
    },
    {
      id: 5,
      title: "The Leak • Attribution in 800ms",
      badge: "Step 5/8 • Attribution",
      speech: "Now, let's catch a leaker. A photo was taken off a monitor at an angle with glare. In under 800 milliseconds, our 9-stage pipeline dewarps the angle, clears glare, and identifies the suspect: Marcus Vance.",
      durationMs: 12000,
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
      title: "Tardos Collusion Defense",
      badge: "Step 6/8 • Collusion Lab",
      speech: "What if two rogue officers team up to wash out the watermark? Our traitor-tracing algorithms unmask both conspirators at once, and Sovereign Quarantine can purge their decryption keys in one click.",
      durationMs: 11000,
      action: (p) => {
        p.onCloseComparator();
        p.onOpenCollusion();
      }
    },
    {
      id: 7,
      title: "Courtroom-Ready Proof • Section 63 BSA",
      badge: "Step 7/8 • Court Docket",
      speech: "Under Section 63 of India's Bharatiya Sakshya Adhiniyam, digital evidence requires strict custody. Our two-officer quorum generates a magistrate-ready certificate with a scannable verification QR code.",
      durationMs: 12000,
      action: (p) => {
        p.onCloseCollusion();
        p.onSetTab('evidence');
        p.onOpenCertificate();
      }
    },
    {
      id: 8,
      title: "100% Offline in Submarine Mode",
      badge: "Step 8/8 • Offline Verifier",
      speech: "Finally, this standalone verifier runs 100% offline inside your browser. No internet, no cloud, no leaks. It works on a naval submarine or in an air-gapped courtroom. That is AegisTrace. Thanks for watching!",
      durationMs: 13000,
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
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Handle Speech & Step Transitions with bug-free timer management
  const executeStep = useCallback((stepIdx: number) => {
    if (stepIdx < 0 || stepIdx >= STEPS.length) {
      setIsPlaying(false);
      return;
    }

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

    // 2. Clear all previous timers and cancel any active speech
    clearAllTimers();

    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    const advanceToNext = () => {
      clearAllTimers();
      if (stepIdx + 1 < STEPS.length) {
        setCurrentStep(stepIdx + 1);
      } else {
        setIsPlaying(false);
      }
    };

    // 3. Play voiceover or fallback to timed duration
    if (!isMuted && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(step.speech);
      if (selectedVoice) {
        utterance.voice = selectedVoice;
      }
      utterance.rate = 1.02;
      utterance.pitch = 1.0;

      utterance.onend = () => {
        clearAllTimers();
        nextTimerRef.current = setTimeout(() => {
          advanceToNext();
        }, 800);
      };

      utterance.onerror = (e) => {
        console.warn('Speech error, fallback to duration:', e);
        clearAllTimers();
        nextTimerRef.current = setTimeout(() => {
          advanceToNext();
        }, step.durationMs);
      };

      try {
        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.warn('speechSynthesis.speak failed:', err);
      }

      // Fallback timer in case onend never triggers
      fallbackTimerRef.current = setTimeout(() => {
        clearAllTimers();
        advanceToNext();
      }, step.durationMs + 2500);
    } else {
      // Voice muted: rely strictly on timed duration
      nextTimerRef.current = setTimeout(() => {
        advanceToNext();
      }, step.durationMs);
    }
  }, [STEPS, isMuted, selectedVoice, clearAllTimers, isOpen, onClose, onSetViewMode, onLoginDemo, onSetTab, onOpenComparator, onCloseComparator, onOpenCollusion, onCloseCollusion, onOpenAirGap, onCloseAirGap, onOpenCertificate, onCloseCertificate, onOpenStandaloneVerifier, onCloseStandaloneVerifier, onTriggerPipeline]);

  // Trigger step when currentStep or isPlaying changes
  useEffect(() => {
    if (!isOpen) {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      clearAllTimers();
      return;
    }

    if (isPlaying) {
      executeStep(currentStep);
    } else {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      clearAllTimers();
    }

    return () => {
      clearAllTimers();
    };
  }, [isOpen, currentStep, isPlaying, executeStep, clearAllTimers]);

  const handleExit = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    clearAllTimers();
    onCloseComparator();
    onCloseCollusion();
    onCloseAirGap();
    onCloseCertificate();
    onCloseStandaloneVerifier();
    onClose();
  };

  if (!isOpen) return null;

  const activeStep = STEPS[currentStep] || STEPS[0];
  const progressPercent = Math.round(((currentStep + 1) / STEPS.length) * 100);

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '16px',
        left: '50%',
        transform: 'translateX(-50%)',
        width: 'min(450px, 92vw)',
        zIndex: 10000,
        background: 'rgba(9, 14, 23, 0.94)',
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        border: '1px solid rgba(56, 189, 248, 0.35)',
        borderRadius: '16px',
        boxShadow: '0 12px 40px rgba(0, 0, 0, 0.65), 0 0 20px rgba(56, 189, 248, 0.12)',
        padding: isMinimized ? '6px 12px 8px 12px' : '8px 12px 10px 12px',
        color: '#FFFFFF',
        fontFamily: 'var(--font-sans, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif)',
        transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
        overflow: 'hidden'
      }}
    >
      {/* Top Header & Compact Controls Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
        {/* Left Status & Step Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0 }}>
          <span 
            style={{ 
              width: '6px', 
              height: '6px', 
              borderRadius: '50%', 
              background: isPlaying ? '#10B981' : '#F59E0B',
              boxShadow: `0 0 6px ${isPlaying ? '#10B981' : '#F59E0B'}`,
              flexShrink: 0
            }} 
          />
          <span style={{ fontSize: '11px', fontWeight: 700, color: '#38BDF8', letterSpacing: '0.02em', whiteSpace: 'nowrap' }}>
            Auto-Demo
          </span>
          <span 
            style={{ 
              fontSize: '10px', 
              color: '#94A3B8', 
              fontWeight: 600, 
              background: 'rgba(255, 255, 255, 0.08)',
              padding: '1px 6px',
              borderRadius: '9999px',
              whiteSpace: 'nowrap'
            }}
          >
            {currentStep + 1}/{STEPS.length}
          </span>
        </div>

        {/* Center / Right Compact Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {/* Previous Step */}
          <button
            onClick={() => {
              if (currentStep > 0) setCurrentStep(currentStep - 1);
            }}
            disabled={currentStep === 0}
            style={{
              background: 'transparent',
              border: 'none',
              borderRadius: '6px',
              width: '24px',
              height: '24px',
              color: currentStep === 0 ? '#475569' : '#CBD5E1',
              cursor: currentStep === 0 ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 0
            }}
            title="Previous Step"
          >
            <SkipBack size={12} />
          </button>

          {/* Play / Pause Toggle */}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            style={{
              background: isPlaying ? '#0284C7' : '#10B981',
              border: 'none',
              borderRadius: '9999px',
              padding: '3px 9px',
              color: '#FFFFFF',
              cursor: 'pointer',
              fontSize: '11px',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              boxShadow: '0 2px 8px rgba(2, 132, 199, 0.3)'
            }}
            title={isPlaying ? "Pause Tour" : "Resume Tour"}
          >
            {isPlaying ? <Pause size={10} /> : <Play size={10} />}
            <span style={{ fontSize: '10.5px' }}>{isPlaying ? 'Pause' : 'Play'}</span>
          </button>

          {/* Next Step */}
          <button
            onClick={() => {
              if (currentStep + 1 < STEPS.length) setCurrentStep(currentStep + 1);
            }}
            disabled={currentStep + 1 >= STEPS.length}
            style={{
              background: 'transparent',
              border: 'none',
              borderRadius: '6px',
              width: '24px',
              height: '24px',
              color: currentStep + 1 >= STEPS.length ? '#475569' : '#CBD5E1',
              cursor: currentStep + 1 >= STEPS.length ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 0
            }}
            title="Next Step"
          >
            <SkipForward size={12} />
          </button>

          {/* Mute Toggle */}
          <button
            onClick={() => {
              if (!isMuted && typeof window !== 'undefined' && 'speechSynthesis' in window) {
                window.speechSynthesis.cancel();
              }
              setIsMuted(!isMuted);
            }}
            style={{
              background: isMuted ? 'rgba(239, 68, 68, 0.15)' : 'rgba(56, 189, 248, 0.12)',
              border: `1px solid ${isMuted ? 'rgba(239, 68, 68, 0.3)' : 'rgba(56, 189, 248, 0.25)'}`,
              borderRadius: '6px',
              width: '24px',
              height: '24px',
              color: isMuted ? '#EF4444' : '#38BDF8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 0
            }}
            title={isMuted ? "Unmute Voice" : "Mute Voice"}
          >
            {isMuted ? <VolumeX size={12} /> : <Volume2 size={12} />}
          </button>

          {/* Minimize / Expand Toggle */}
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            style={{
              background: 'transparent',
              border: 'none',
              borderRadius: '6px',
              width: '22px',
              height: '22px',
              color: '#94A3B8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 0
            }}
            title={isMinimized ? "Expand Captions" : "Minimize Window"}
          >
            {isMinimized ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>

          {/* Exit Button */}
          <button
            onClick={handleExit}
            style={{
              background: 'transparent',
              border: 'none',
              borderRadius: '6px',
              width: '22px',
              height: '22px',
              color: '#94A3B8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 0
            }}
            title="Exit Demo Tour"
          >
            <X size={13} />
          </button>
        </div>
      </div>

      {/* Row 2: Really Compact Subtitle Line (Hidden when Minimized) */}
      {!isMinimized && (
        <div
          style={{
            marginTop: '6px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(255, 255, 255, 0.04)',
            padding: '4px 8px',
            borderRadius: '8px'
          }}
        >
          <Sparkles size={11} style={{ color: '#38BDF8', flexShrink: 0 }} />
          <p
            style={{
              margin: 0,
              fontSize: '11px',
              lineHeight: 1.35,
              color: '#E2E8F0',
              fontWeight: 450,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical'
            }}
          >
            &ldquo;{activeStep.speech}&rdquo;
          </p>
        </div>
      )}

      {/* Razor-Thin Bottom Edge Progress Line */}
      <div 
        style={{ 
          position: 'absolute',
          bottom: 0,
          left: 0,
          height: '2px', 
          width: `${progressPercent}%`, 
          background: 'linear-gradient(90deg, #0284C7, #38BDF8)',
          transition: 'width 0.3s ease'
        }} 
      />
    </div>
  );
};

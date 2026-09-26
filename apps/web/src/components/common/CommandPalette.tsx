import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Layers, 
  Users, 
  FileText, 
  Unlock, 
  Database, 
  ShieldAlert, 
  Zap, 
  Cpu, 
  PlayCircle, 
  RotateCcw, 
  Wifi, 
  WifiOff, 
  AlertTriangle,
  FileCheck
} from 'lucide-react';

export interface CommandItem {
  id: string;
  category: 'Navigation' | 'Scenarios' | 'Actions';
  title: string;
  subtitle?: string;
  icon: React.ComponentType<any>;
  perform: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  setActiveTab: (tab: any) => void;
  onQuickScenario: (scenarioId: string) => void;
  onOpenWalkthrough: () => void;
  onResetDemo: () => void;
  isOnline: boolean;
  forceOffline: boolean;
  setForceOffline: (val: boolean) => void;
  onSimulateTamper: () => void;
  onExportReport?: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  setActiveTab,
  onQuickScenario,
  onOpenWalkthrough,
  onResetDemo,
  isOnline,
  forceOffline,
  setForceOffline,
  onSimulateTamper,
  onExportReport
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands: CommandItem[] = [
    // Navigation
    {
      id: 'nav-dashboard',
      category: 'Navigation',
      title: 'Operations Overview',
      subtitle: 'System KPI metrics, active pipeline status, and security architecture checklist',
      icon: Layers,
      perform: () => { setActiveTab('dashboard'); onClose(); }
    },
    {
      id: 'nav-recipients',
      category: 'Navigation',
      title: 'Recipient Registry',
      subtitle: 'Post-quantum public keys (ML-KEM-768, ML-DSA-65) and role management',
      icon: Users,
      perform: () => { setActiveTab('recipients'); onClose(); }
    },
    {
      id: 'nav-release',
      category: 'Navigation',
      title: 'Encrypted Releases',
      subtitle: 'Multi-recipient hybrid envelope encapsulation and release package generation',
      icon: FileText,
      perform: () => { setActiveTab('release'); onClose(); }
    },
    {
      id: 'nav-leak',
      category: 'Navigation',
      title: 'Forensic Attribution Workstation',
      subtitle: 'Multi-channel evidence fusion, Tardos matrix scoring, and fail-closed verdict',
      icon: ShieldAlert,
      perform: () => { setActiveTab('leak'); onClose(); }
    },
    {
      id: 'nav-attack',
      category: 'Navigation',
      title: 'Attack Laboratory',
      subtitle: 'Adversarial degradation benchmarks, print-camera recapture, and robustness proofs',
      icon: Zap,
      perform: () => { setActiveTab('attack_lab'); onClose(); }
    },
    {
      id: 'nav-ledger',
      category: 'Navigation',
      title: 'Audit Ledger & Hash-Chain',
      subtitle: 'Immutable cryptographic provenance events, block linkage, and tamper detection',
      icon: Database,
      perform: () => { setActiveTab('ledger'); onClose(); }
    },
    {
      id: 'nav-tardos',
      category: 'Navigation',
      title: 'Tardos Codeword Matrix',
      subtitle: 'Mathematical fingerprint distribution, collusion resistance, and symmetric bounds',
      icon: Cpu,
      perform: () => { setActiveTab('tardos'); onClose(); }
    },
    {
      id: 'nav-decrypt',
      category: 'Navigation',
      title: 'Client Decrypt & Sign',
      subtitle: 'Simulate recipient-side ML-KEM decapsulation and non-repudiation signing',
      icon: Unlock,
      perform: () => { setActiveTab('decrypt'); onClose(); }
    },

    // Scenarios
    {
      id: 'scen-clean-bob',
      category: 'Scenarios',
      title: 'Run: Clean Bob Leak (Direct Unaltered Leak)',
      subtitle: 'Evaluates direct leak with zero channel distortion; expects ATTRIBUTED to Bob',
      icon: ShieldAlert,
      perform: () => { onQuickScenario('clean_bob'); onClose(); }
    },
    {
      id: 'scen-camera-bob',
      category: 'Scenarios',
      title: 'Run: Print-Camera Recapture Leak (Bob)',
      subtitle: 'Physical recapture with perspective tilt and illumination noise; evaluates ArUco sync',
      icon: ShieldAlert,
      perform: () => { onQuickScenario('print_scan_camera'); onClose(); }
    },
    {
      id: 'scen-forged-hmac',
      category: 'Scenarios',
      title: 'Run: Forged Metadata Attack (Tampered Header)',
      subtitle: 'Evaluates adversarial signature forgery; expects fail-closed signature rejection',
      icon: AlertTriangle,
      perform: () => { onQuickScenario('forged_hmac'); onClose(); }
    },
    {
      id: 'scen-framed-identity',
      category: 'Scenarios',
      title: 'Run: Framed Identity Attack (Alice Claimed, Bob Embedded)',
      subtitle: 'Transplanted envelope header claiming Alice; forensic fusion resolves to true source',
      icon: AlertTriangle,
      perform: () => { onQuickScenario('framed_identity'); onClose(); }
    },
    {
      id: 'scen-conflict',
      category: 'Scenarios',
      title: 'Run: Collusion / Channel Conflict (Bob + Charlie)',
      subtitle: 'Two recipients collude; Tardos and carrier signals conflict, triggering CONFLICT state',
      icon: AlertTriangle,
      perform: () => { onQuickScenario('evidence_conflict_bob_charlie'); onClose(); }
    },
    {
      id: 'scen-review',
      category: 'Scenarios',
      title: 'Run: Severe Distortion Anomaly (Review Required)',
      subtitle: 'Heavy blur and cropping; confidence drops below threshold, triggering REVIEW_REQUIRED',
      icon: AlertTriangle,
      perform: () => { onQuickScenario('review_required_anomaly'); onClose(); }
    },

    // Actions
    {
      id: 'act-walkthrough',
      category: 'Actions',
      title: 'Start Interactive Judge Walkthrough',
      subtitle: 'Step-by-step guided evaluation tour through all cryptographic and forensic phases',
      icon: PlayCircle,
      perform: () => { onOpenWalkthrough(); onClose(); }
    },
    {
      id: 'act-tamper',
      category: 'Actions',
      title: 'Simulate Ledger Tamper (Block #1 Invalidation)',
      subtitle: 'Corrupts payload in block #1 to demonstrate real cryptographic hash-chain failure',
      icon: AlertTriangle,
      perform: () => { onSimulateTamper(); setActiveTab('ledger'); onClose(); }
    },
    {
      id: 'act-toggle-offline',
      category: 'Actions',
      title: isOnline ? 'Switch to Offline Simulation Mode' : 'Connect to Live Backend (:8000)',
      subtitle: 'Toggle between live FastAPI backend and standalone browser demo simulator',
      icon: isOnline ? WifiOff : Wifi,
      perform: () => { setForceOffline(!forceOffline); onClose(); }
    },
    {
      id: 'act-reset',
      category: 'Actions',
      title: 'Reset Demo State to Clean Baseline',
      subtitle: 'Restores initial documents, enrolled recipients, release packages, and verified ledger',
      icon: RotateCcw,
      perform: () => { onResetDemo(); onClose(); }
    }
  ];

  if (onExportReport) {
    commands.push({
      id: 'act-export',
      category: 'Actions',
      title: 'Export Forensic Evidence Package',
      subtitle: 'Generate formatted cryptographic audit report with proof hashes and verdicts',
      icon: FileCheck,
      perform: () => { onExportReport(); onClose(); }
    });
  }

  const filtered = commands.filter(cmd => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return (
      cmd.title.toLowerCase().includes(q) ||
      (cmd.subtitle && cmd.subtitle.toLowerCase().includes(q)) ||
      cmd.category.toLowerCase().includes(q)
    );
  });

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else {
          // Open palette
          (window as any).__openCommandPalette?.();
        }
      }

      if (!isOpen) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1 < filtered.length ? prev + 1 : 0));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => (prev - 1 >= 0 ? prev - 1 : filtered.length - 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          filtered[selectedIndex].perform();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filtered, selectedIndex, onClose, forceOffline, isOnline]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.12 }}
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 120,
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'center',
            paddingTop: '10vh',
            backgroundColor: 'rgba(0, 0, 0, 0.55)',
            backdropFilter: 'blur(4px)'
          }}
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: -8 }}
            transition={{ duration: 0.14, ease: 'easeOut' }}
            style={{
              width: '640px',
              maxWidth: '92vw',
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border-strong)',
              borderRadius: 'var(--radius-lg)',
              boxShadow: 'var(--shadow-lg)',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column'
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Search Input Bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
            padding: 'var(--space-4) var(--space-5)',
            borderBottom: '1px solid var(--border)',
            backgroundColor: 'var(--surface)'
          }}
        >
          <Search size={18} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search commands, views, forensic scenarios, actions... (↑↓ to select, Enter to run)"
            value={query}
            onChange={e => setQuery(e.target.value)}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text)',
              fontSize: 'var(--text-md)',
              fontFamily: 'inherit'
            }}
          />
          <kbd
            style={{
              padding: '2px 6px',
              fontSize: '11px',
              backgroundColor: 'var(--surface-hover)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-xs)',
              color: 'var(--text-tertiary)'
            }}
          >
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div
          style={{
            maxHeight: '400px',
            overflowY: 'auto',
            padding: 'var(--space-2)'
          }}
        >
          {filtered.length === 0 ? (
            <div
              style={{
                padding: 'var(--space-8)',
                textAlign: 'center',
                color: 'var(--text-tertiary)',
                fontSize: 'var(--text-base)'
              }}
            >
              No matching commands or actions found.
            </div>
          ) : (
            filtered.map((cmd, idx) => {
              const Icon = cmd.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={cmd.id}
                  onClick={() => cmd.perform()}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-3)',
                    padding: 'var(--space-3) var(--space-4)',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: isSelected ? 'var(--primary-subtle)' : 'transparent',
                    border: isSelected ? '1px solid var(--primary-border)' : '1px solid transparent',
                    cursor: 'pointer',
                    transition: 'background var(--transition-fast)'
                  }}
                >
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: isSelected ? 'var(--primary)' : 'var(--surface-hover)',
                      color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}
                  >
                    <Icon size={16} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          fontSize: 'var(--text-base)',
                          fontWeight: 600,
                          color: isSelected ? 'var(--primary-text)' : 'var(--text)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}
                      >
                        {cmd.title}
                      </span>
                      <span
                        style={{
                          fontSize: '10.5px',
                          padding: '1px 6px',
                          borderRadius: 'var(--radius-full)',
                          backgroundColor: 'var(--surface-hover)',
                          color: 'var(--text-tertiary)',
                          border: '1px solid var(--border)'
                        }}
                      >
                        {cmd.category}
                      </span>
                    </div>
                    {cmd.subtitle && (
                      <div
                        style={{
                          fontSize: 'var(--text-xs)',
                          color: 'var(--text-secondary)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          marginTop: '2px'
                        }}
                      >
                        {cmd.subtitle}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div
          style={{
            padding: 'var(--space-2) var(--space-4)',
            borderTop: '1px solid var(--border)',
            backgroundColor: 'var(--surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: 'var(--text-xs)',
            color: 'var(--text-tertiary)'
          }}
        >
          <div style={{ display: 'flex', gap: '12px' }}>
            <span><kbd>↑</kbd> <kbd>↓</kbd> Navigate</span>
            <span><kbd>↵</kbd> Execute</span>
            <span><kbd>ESC</kbd> Close</span>
          </div>
          <div>
            <span>AegisTrace Workstation</span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )}
</AnimatePresence>
  );
};

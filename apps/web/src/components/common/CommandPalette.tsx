import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Layers, 
  FileText, 
  Package, 
  ShieldAlert, 
  Building, 
  Users, 
  Network, 
  FileCheck, 
  GitFork, 
  Database, 
  Activity, 
  Server, 
  Play, 
  RotateCcw, 
  Wifi, 
  WifiOff, 
  ShieldCheck,
  FileSignature
} from 'lucide-react';

export interface CommandItem {
  id: string;
  category: 'Navigation' | 'Forensic Scenarios' | 'System Actions';
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
      id: 'nav-overview',
      category: 'Navigation',
      title: 'Operations Overview',
      subtitle: 'System posture, active releases, and operational summary',
      icon: Layers,
      perform: () => { setActiveTab('overview'); onClose(); }
    },
    {
      id: 'nav-documents',
      category: 'Navigation',
      title: 'Protected Documents',
      subtitle: 'Classified documents, hashes, owners, and releases',
      icon: FileText,
      perform: () => { setActiveTab('documents'); onClose(); }
    },
    {
      id: 'nav-releases',
      category: 'Navigation',
      title: 'Encrypted Releases',
      subtitle: 'Multi-recipient hybrid encapsulation (ML-KEM-768 + AES-256-GCM)',
      icon: Package,
      perform: () => { setActiveTab('releases'); onClose(); }
    },
    {
      id: 'nav-investigations',
      category: 'Navigation',
      title: 'Forensic Investigations',
      subtitle: 'Multi-channel Bayesian evidence fusion and attribution',
      icon: ShieldAlert,
      perform: () => { setActiveTab('investigations'); onClose(); }
    },
    {
      id: 'nav-directory',
      category: 'Navigation',
      title: 'Enterprise Directory',
      subtitle: 'Microsoft Entra ID, Okta, and LDAP identity synchronization',
      icon: Building,
      perform: () => { setActiveTab('directory'); onClose(); }
    },
    {
      id: 'nav-recipients',
      category: 'Navigation',
      title: 'Cryptographic Principals',
      subtitle: 'Enrolled PQC public keys (ML-KEM-768, ML-DSA-65)',
      icon: Users,
      perform: () => { setActiveTab('recipients'); onClose(); }
    },
    {
      id: 'nav-groups',
      category: 'Navigation',
      title: 'Security Groups',
      subtitle: 'Targeting groups with zero shared keys',
      icon: Network,
      perform: () => { setActiveTab('groups'); onClose(); }
    },
    {
      id: 'nav-evidence',
      category: 'Navigation',
      title: 'Cryptographic Evidence',
      subtitle: 'Multi-channel evidence repository and LLR proofs',
      icon: FileCheck,
      perform: () => { setActiveTab('evidence'); onClose(); }
    },
    {
      id: 'nav-provenance',
      category: 'Navigation',
      title: 'Custody & Provenance',
      subtitle: 'Lineage DAG from document genesis to leak attribution',
      icon: GitFork,
      perform: () => { setActiveTab('provenance'); onClose(); }
    },
    {
      id: 'nav-ledger',
      category: 'Navigation',
      title: 'Audit Ledger',
      subtitle: 'Immutable cryptographic hash-chain and block explorer',
      icon: Database,
      perform: () => { setActiveTab('ledger'); onClose(); }
    },
    {
      id: 'nav-security-testing',
      category: 'Navigation',
      title: 'Security Testing',
      subtitle: 'Adversarial degradation benchmarks and robustness suite',
      icon: ShieldCheck,
      perform: () => { setActiveTab('security_testing'); onClose(); }
    },
    {
      id: 'nav-health',
      category: 'Navigation',
      title: 'System Health',
      subtitle: 'Cryptographic runtime health and component diagnostics',
      icon: Server,
      perform: () => { setActiveTab('health'); onClose(); }
    },

    // Forensic Scenarios
    {
      id: 'scen-clean-bob',
      category: 'Forensic Scenarios',
      title: 'Evaluate Clean Digital Leak (Bob Martinez)',
      subtitle: 'Benchmark scenario with verified spatial marker and ML-DSA signature',
      icon: Play,
      perform: () => { onQuickScenario('clean_bob'); onClose(); }
    },
    {
      id: 'scen-recapture',
      category: 'Forensic Scenarios',
      title: 'Evaluate Optical Print-Camera Recapture',
      subtitle: 'Simulates geometric warp, lens distortion, and RANSAC rectification',
      icon: Play,
      perform: () => { onQuickScenario('recapture_camera'); onClose(); }
    },
    {
      id: 'scen-tardos-collusion',
      category: 'Forensic Scenarios',
      title: 'Evaluate Tardos 2-Party Collusion Attack',
      subtitle: '2-colluder coalition attack bounded by Tardos arcsine bias cutoff',
      icon: Play,
      perform: () => { onQuickScenario('tardos_collusion_2party'); onClose(); }
    },

    // System Actions
    {
      id: 'act-export-dossier',
      category: 'System Actions',
      title: 'Export Forensic Evidence Dossier',
      subtitle: 'Generate verifiable technical report with ML-DSA proofs and JSON export',
      icon: FileSignature,
      perform: () => { if (onExportReport) onExportReport(); onClose(); }
    },
    {
      id: 'act-tamper-test',
      category: 'System Actions',
      title: 'Simulate Ledger Block Tampering',
      subtitle: 'Inject intentional hash mismatch into block #1 to test fail-closed defense',
      icon: ShieldAlert,
      perform: () => { onSimulateTamper(); onClose(); }
    },
    {
      id: 'act-toggle-offline',
      category: 'System Actions',
      title: forceOffline ? 'Connect to Live API Gateway' : 'Switch to Standalone Offline Simulator',
      subtitle: 'Toggle between live Python backend and client-side simulator',
      icon: forceOffline ? Wifi : WifiOff,
      perform: () => { setForceOffline(!forceOffline); onClose(); }
    },
    {
      id: 'act-reset-demo',
      category: 'System Actions',
      title: 'Reset Demo State & Ledger',
      subtitle: 'Restore clean baseline state across all cryptographic subsystems',
      icon: RotateCcw,
      perform: () => { onResetDemo(); onClose(); }
    }
  ];

  const filtered = commands.filter(cmd => 
    cmd.title.toLowerCase().includes(query.toLowerCase()) ||
    cmd.category.toLowerCase().includes(query.toLowerCase()) ||
    (cmd.subtitle && cmd.subtitle.toLowerCase().includes(query.toLowerCase()))
  );

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % (filtered.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + (filtered.length || 1)) % (filtered.length || 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        filtered[selectedIndex].perform();
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  };

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
            zIndex: 120,
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'center',
            paddingTop: '12vh',
            backgroundColor: 'rgba(11, 16, 21, 0.7)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)'
          }}
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.98, y: -6 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: -6 }}
            transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
            style={{
              width: '100%',
              maxWidth: '600px',
              backgroundColor: 'var(--glass-surface-elevated)',
              backdropFilter: 'var(--glass-blur-md)',
              WebkitBackdropFilter: 'var(--glass-blur-md)',
              border: '1px solid var(--border-strong)',
              borderRadius: 'var(--radius-lg)',
              boxShadow: 'var(--shadow-lg)',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column'
            }}
            onClick={e => e.stopPropagation()}
            onKeyDown={handleKeyDown}
          >
            {/* Search Input Bar */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '14px 18px',
                borderBottom: '1px solid var(--border)'
              }}
            >
              <Search size={16} style={{ color: 'var(--primary-text)' }} />
              <input
                ref={inputRef}
                value={query}
                onChange={e => {
                  setQuery(e.target.value);
                  setSelectedIndex(0);
                }}
                placeholder="Type a command or search documents, evidence, ledger..."
                style={{
                  flex: 1,
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: 'var(--text)',
                  fontSize: 'var(--text-base)',
                  fontFamily: 'inherit'
                }}
              />
              <kbd
                style={{
                  fontSize: '10.5px',
                  fontFamily: 'var(--font-mono)',
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-xs)',
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-tertiary)'
                }}
              >
                ESC
              </kbd>
            </div>

            {/* Results List */}
            <div
              style={{
                maxHeight: '380px',
                overflowY: 'auto',
                padding: '8px'
              }}
            >
              {filtered.length === 0 ? (
                <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 'var(--text-sm)' }}>
                  No matching commands or navigation routes.
                </div>
              ) : (
                filtered.map((item, idx) => {
                  const Icon = item.icon;
                  const isSelected = idx === selectedIndex;

                  return (
                    <div
                      key={item.id}
                      onClick={() => item.perform()}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '9px 12px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: isSelected ? 'var(--primary-subtle)' : 'transparent',
                        border: isSelected ? '1px solid var(--primary-border)' : '1px solid transparent',
                        cursor: 'pointer',
                        transition: 'background-color var(--transition-fast)'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div
                          style={{
                            width: '28px',
                            height: '28px',
                            borderRadius: 'var(--radius-xs)',
                            backgroundColor: isSelected ? 'rgba(76, 154, 154, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: isSelected ? 'var(--primary-text)' : 'var(--text-secondary)'
                          }}
                        >
                          <Icon size={15} />
                        </div>
                        <div>
                          <div
                            style={{
                              fontSize: 'var(--text-sm)',
                              fontWeight: isSelected ? 600 : 500,
                              color: isSelected ? 'var(--text)' : 'var(--text-secondary)'
                            }}
                          >
                            {item.title}
                          </div>
                          {item.subtitle && (
                            <div
                              style={{
                                fontSize: '11px',
                                color: 'var(--text-tertiary)',
                                marginTop: '1px'
                              }}
                            >
                              {item.subtitle}
                            </div>
                          )}
                        </div>
                      </div>

                      <span
                        style={{
                          fontSize: '10.5px',
                          color: 'var(--text-tertiary)',
                          padding: '2px 6px',
                          borderRadius: 'var(--radius-xs)',
                          backgroundColor: 'rgba(255, 255, 255, 0.03)'
                        }}
                      >
                        {item.category}
                      </span>
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer Navigation Hints */}
            <div
              style={{
                padding: '8px 16px',
                borderTop: '1px solid var(--border-subtle)',
                backgroundColor: 'rgba(255, 255, 255, 0.01)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '11px',
                color: 'var(--text-tertiary)'
              }}
            >
              <div style={{ display: 'flex', gap: '12px' }}>
                <span>↑↓ Navigate</span>
                <span>↵ Select</span>
                <span>ESC Close</span>
              </div>
              <span>NIST FIPS 203/204</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  FileText, 
  Send, 
  SearchCheck, 
  ShieldCheck, 
  Database, 
  Fingerprint, 
  Moon, 
  Sun, 
  Zap,
  Layers,
  ArrowRight,
  Sparkles,
  Command,
  BookOpen,
  RotateCcw,
  AlertTriangle,
  FileSpreadsheet,
  Wifi,
  WifiOff,
  UserCheck,
  Users,
  Camera,
  Key,
  Eye,
  Award,
  Scale
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export interface CommandItem {
  id: string;
  title: string;
  category: 'Navigation' | 'Benchmark' | 'Action' | 'Audit' | 'Labs';
  description: string;
  shortcut?: string;
  icon: React.ReactNode;
  perform: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  setActiveTab?: (tab: any) => void;
  onNavigateTab?: (tab: string) => void;
  onQuickScenario?: (scenarioId: string) => void;
  onRunBenchmark?: (benchmarkId: string) => void;
  onOpenWalkthrough?: () => void;
  onResetDemo?: () => void;
  isOnline?: boolean;
  forceOffline?: boolean;
  setForceOffline?: (val: boolean) => void;
  onSimulateTamper?: () => void;
  onExportReport?: () => void;
  onToggleTheme?: () => void;
  onOpenVerify?: () => void;
  onOpenCollusionLab?: () => void;
  onOpenAirGapLab?: () => void;
  onOpenDecryptionLab?: () => void;
  onOpenComparatorLab?: () => void;
  onOpenCertificate?: () => void;
  onOpenCompliance?: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  setActiveTab,
  onNavigateTab,
  onQuickScenario,
  onRunBenchmark,
  onOpenWalkthrough,
  onResetDemo,
  isOnline,
  forceOffline,
  setForceOffline,
  onSimulateTamper,
  onExportReport,
  onToggleTheme,
  onOpenVerify,
  onOpenCollusionLab,
  onOpenAirGapLab,
  onOpenDecryptionLab,
  onOpenComparatorLab,
  onOpenCertificate,
  onOpenCompliance
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const { theme, toggleTheme } = useTheme();

  const navigate = (tabId: string) => {
    if (setActiveTab) setActiveTab(tabId);
    else if (onNavigateTab) onNavigateTab(tabId);
    onClose();
  };

  const runScenario = (scenarioId: string) => {
    navigate('investigations');
    if (onQuickScenario) onQuickScenario(scenarioId);
    else if (onRunBenchmark) onRunBenchmark(scenarioId);
    onClose();
  };

  const commands: CommandItem[] = [
    // Navigation
    {
      id: 'nav-overview',
      title: 'Overview Cockpit',
      category: 'Navigation',
      description: 'System operational status and activity summary',
      icon: <Layers size={16} className="text-emerald-400" />,
      perform: () => navigate('overview')
    },
    {
      id: 'nav-documents',
      title: 'Document Registry',
      category: 'Navigation',
      description: 'Ingest and protect multi-format documents (PDF, DOCX, XLSX, PPTX, PNG, JPEG)',
      icon: <FileText size={16} className="text-teal-400" />,
      perform: () => navigate('documents')
    },
    {
      id: 'nav-releases',
      title: 'Protected Releases',
      category: 'Navigation',
      description: 'Manage cryptographic distribution envelopes and recipient capsules',
      icon: <Send size={16} className="text-blue-400" />,
      perform: () => navigate('releases')
    },
    {
      id: 'nav-investigations',
      title: 'Forensic Investigations',
      category: 'Navigation',
      description: 'Autonomous multi-channel Bayesian leak attribution',
      icon: <SearchCheck size={16} className="text-amber-400" />,
      perform: () => navigate('investigations')
    },
    {
      id: 'nav-evidence',
      title: 'Evidence Records',
      category: 'Navigation',
      description: 'Cryptographic dossiers and Merkle chain of custody',
      icon: <ShieldCheck size={16} className="text-purple-400" />,
      perform: () => navigate('evidence')
    },
    {
      id: 'nav-verify',
      title: 'AegisTrace Verify (Zero-Server Standalone)',
      category: 'Navigation',
      description: 'Air-gapped offline evidence package audit workstation',
      icon: <Fingerprint size={16} className="text-teal-400" />,
      perform: () => {
        if (onOpenVerify) onOpenVerify();
        else navigate('verify');
      }
    },
    {
      id: 'nav-recipients',
      title: 'Recipient Management',
      category: 'Navigation',
      description: 'Enrolled post-quantum identities and key certificates',
      icon: <UserCheck size={16} className="text-blue-400" />,
      perform: () => navigate('recipients')
    },
    {
      id: 'nav-ledger',
      title: 'Tamper-Evident Ledger',
      category: 'Navigation',
      description: 'Immutable hash chain with zero-knowledge cryptographic integrity',
      icon: <Database size={16} className="text-emerald-400" />,
      perform: () => navigate('ledger')
    },

    // Benchmarks
    {
      id: 'bench-bob',
      title: 'Evaluate: Clean Digital Leak (Bob Martinez)',
      category: 'Benchmark',
      description: 'Evaluates baseline single-recipient leak with +18.08 LLR attribution',
      icon: <Zap size={16} className="text-amber-400" />,
      perform: () => runScenario('clean_bob')
    },
    {
      id: 'bench-photo',
      title: 'Evaluate: Smartphone Photograph (Bob)',
      category: 'Benchmark',
      description: 'Physical print-camera optical descreening and perspective correction',
      icon: <Zap size={16} className="text-amber-400" />,
      perform: () => runScenario('photo_bob')
    },
    {
      id: 'bench-forgery',
      title: 'Evaluate: Forged Token Injection (Adversarial)',
      category: 'Benchmark',
      description: 'Tests fail-closed defense against counterfeit token injection',
      icon: <Zap size={16} className="text-rose-400" />,
      perform: () => runScenario('forged_token')
    },
    {
      id: 'bench-unwatermarked',
      title: 'Evaluate: Unwatermarked Master Document',
      category: 'Benchmark',
      description: 'Verifies abstention guard against pre-release master artifacts',
      icon: <Zap size={16} className="text-amber-400" />,
      perform: () => runScenario('unwatermarked')
    },
    {
      id: 'bench-tamper-alice',
      title: 'Evaluate: Tampered Recipient Frame (Framing Alice)',
      category: 'Benchmark',
      description: 'Cross-validates cryptographic signature against watermarked carrier',
      icon: <Zap size={16} className="text-rose-400" />,
      perform: () => runScenario('tampered_alice')
    },

    // Actions & Tools
    {
      id: 'action-theme',
      title: `Switch Theme to ${theme === 'dark' ? 'Light (Warm Ivory)' : 'Dark (Graphite & Petrol)'}`,
      category: 'Action',
      description: 'Toggle interface theme mode',
      icon: theme === 'dark' ? <Sun size={16} className="text-amber-400" /> : <Moon size={16} className="text-slate-400" />,
      perform: () => {
        if (onToggleTheme) onToggleTheme();
        else toggleTheme();
        onClose();
      }
    },
    {
      id: 'action-walkthrough',
      title: 'Open System Architecture Guide',
      category: 'Action',
      description: 'Interactive reference on PQC encapsulation, Tardos codes, and Bayesian fusion',
      icon: <BookOpen size={16} className="text-teal-400" />,
      perform: () => {
        if (onOpenWalkthrough) onOpenWalkthrough();
        onClose();
      }
    },
    {
      id: 'action-offline',
      title: forceOffline ? 'Connect to Live Server API' : 'Switch to Offline Simulation Mode',
      category: 'Action',
      description: forceOffline ? 'Enable live backend synchronization' : 'Disconnect and operate purely client-side',
      icon: forceOffline ? <Wifi size={16} className="text-emerald-400" /> : <WifiOff size={16} className="text-amber-400" />,
      perform: () => {
        if (setForceOffline) setForceOffline(!forceOffline);
        onClose();
      }
    },
    {
      id: 'action-tamper',
      title: 'Simulate Ledger Tamper Attack',
      category: 'Audit',
      description: 'Mutates block payload to demonstrate cryptographic hash break detection',
      icon: <AlertTriangle size={16} className="text-rose-400" />,
      perform: () => {
        navigate('ledger');
        if (onSimulateTamper) onSimulateTamper();
        onClose();
      }
    },
    {
      id: 'action-export-report',
      title: 'Generate Full Forensic Investigation Dossier',
      category: 'Audit',
      description: 'Exports signed JSON-LD cryptographic evidence package',
      icon: <FileSpreadsheet size={16} className="text-purple-400" />,
      perform: () => {
        if (onExportReport) onExportReport();
        else navigate('evidence');
        onClose();
      }
    },

    // Interactive Forensic Labs & Simulators
    {
      id: 'lab-collusion',
      title: 'Collusion Resistance Lab (Tardos Code Simulator)',
      category: 'Labs',
      description: 'Simulate dynamic coalitions with averaging, minmax, and splicing attack vectors',
      icon: <Users size={16} className="text-purple-400" />,
      perform: () => {
        if (onOpenCollusionLab) onOpenCollusionLab();
        onClose();
      }
    },
    {
      id: 'lab-airgap',
      title: 'Air-Gap Optical Camera Lab (Smartphone Demodulation)',
      category: 'Labs',
      description: 'Live camera stream demodulation with homography rectification and print descreening',
      icon: <Camera size={16} className="text-amber-400" />,
      perform: () => {
        if (onOpenAirGapLab) onOpenAirGapLab();
        onClose();
      }
    },
    {
      id: 'lab-decryption',
      title: 'Recipient Decapsulation Enclave (ML-KEM-768)',
      category: 'Labs',
      description: 'Test NIST FIPS 203 post-quantum decapsulation and ephemeral watermark injection',
      icon: <Key size={16} className="text-sky-400" />,
      perform: () => {
        if (onOpenDecryptionLab) onOpenDecryptionLab();
        onClose();
      }
    },
    {
      id: 'lab-comparator',
      title: 'Proof of Visual Imperceptibility (Spectral Carrier Comparator)',
      category: 'Labs',
      description: 'Side-by-side DSSS spatial carrier comparator and difference heatmap (>45dB PSNR)',
      icon: <Eye size={16} className="text-teal-400" />,
      perform: () => {
        if (onOpenComparatorLab) onOpenComparatorLab();
        onClose();
      }
    },
    {
      id: 'lab-certificate',
      title: 'Section 65B Electronic Evidence Certificate Generator',
      category: 'Audit',
      description: 'Indian Evidence Act Section 65B certified chain of custody with downloadable proof archive',
      icon: <Scale size={16} className="text-emerald-400" />,
      perform: () => {
        if (onOpenCertificate) onOpenCertificate();
        onClose();
      }
    },
    {
      id: 'lab-compliance',
      title: 'Sovereign Defense Compliance Matrix',
      category: 'Audit',
      description: 'Review complete 10-pillar architecture verification matrix against Ministry requirements',
      icon: <Award size={16} className="text-amber-400" />,
      perform: () => {
        if (onOpenCompliance) onOpenCompliance();
        onClose();
      }
    }
  ];

  // Filtering
  const filtered = commands.filter((cmd) => {
    const matchesCategory = selectedCategory === 'All' || cmd.category === selectedCategory;
    const matchesQuery = 
      cmd.title.toLowerCase().includes(query.toLowerCase()) ||
      cmd.description.toLowerCase().includes(query.toLowerCase()) ||
      cmd.category.toLowerCase().includes(query.toLowerCase());
    return matchesCategory && matchesQuery;
  });

  useEffect(() => {
    setSelectedIndex(0);
  }, [query, selectedCategory]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery('');
      setSelectedCategory('All');
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1 < filtered.length ? prev + 1 : 0));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 >= 0 ? prev - 1 : filtered.length - 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          filtered[selectedIndex].perform();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filtered, selectedIndex, onClose]);

  if (!isOpen) return null;

  const categories = ['All', 'Navigation', 'Benchmark', 'Action', 'Audit'];

  return (
    <div className="command-palette-backdrop" onClick={onClose}>
      <div 
        className="command-palette-dialog" 
        onClick={(e) => e.stopPropagation()}
        style={{
          border: '1px solid var(--border-strong, rgba(255, 255, 255, 0.14))',
          background: 'var(--surface-elevated, #141D26)',
        }}
      >
        {/* Search Header */}
        <div 
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            padding: '12px 16px',
            borderBottom: '1px solid var(--border, rgba(255, 255, 255, 0.08))',
            gap: '12px'
          }}
        >
          <Search size={18} style={{ color: 'var(--primary, #4C9A9A)' }} />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command, jump to tab, or run benchmark..."
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text, #F2EFE8)',
              fontSize: '14px',
              fontFamily: 'var(--font-family)',
            }}
          />
          <kbd 
            style={{
              padding: '2px 6px',
              fontSize: '10px',
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.12))',
              borderRadius: '4px',
              color: 'var(--text-tertiary, #73808C)',
              fontFamily: 'var(--font-mono)'
            }}
          >
            ESC
          </kbd>
        </div>

        {/* Category Filter Pills */}
        <div 
          style={{ 
            display: 'flex', 
            gap: '6px', 
            padding: '8px 16px',
            borderBottom: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.05))',
            background: 'rgba(0, 0, 0, 0.18)'
          }}
        >
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              style={{
                padding: '3px 10px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: 500,
                border: selectedCategory === cat 
                  ? '1px solid rgba(76, 154, 154, 0.4)' 
                  : '1px solid transparent',
                background: selectedCategory === cat 
                  ? 'rgba(76, 154, 154, 0.15)' 
                  : 'transparent',
                color: selectedCategory === cat 
                  ? 'var(--primary-text, #68B7B0)' 
                  : 'var(--text-tertiary, #73808C)',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Command List */}
        <div 
          ref={listRef}
          style={{ 
            maxHeight: '360px', 
            overflowY: 'auto', 
            padding: '8px 0' 
          }}
        >
          {filtered.length === 0 ? (
            <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
              <p style={{ fontSize: '13px', margin: 0 }}>No matching commands found.</p>
              <p style={{ fontSize: '11px', marginTop: '4px' }}>Try searching "investigation", "verify", "benchmark", or "theme"</p>
            </div>
          ) : (
            filtered.map((cmd, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={cmd.id}
                  onClick={() => cmd.perform()}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '9px 16px',
                    cursor: 'pointer',
                    background: isSelected ? 'rgba(76, 154, 154, 0.12)' : 'transparent',
                    borderLeft: isSelected ? '3px solid var(--primary, #4C9A9A)' : '3px solid transparent',
                    transition: 'background 0.1s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                    <div 
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '28px',
                        height: '28px',
                        borderRadius: '6px',
                        background: isSelected ? 'rgba(76, 154, 154, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.08)'
                      }}
                    >
                      {cmd.icon}
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span 
                          style={{ 
                            fontSize: '13px', 
                            fontWeight: 500, 
                            color: isSelected ? '#FFFFFF' : 'var(--text, #F2EFE8)' 
                          }}
                        >
                          {cmd.title}
                        </span>
                        <span 
                          style={{
                            fontSize: '9px',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            padding: '1px 5px',
                            borderRadius: '3px',
                            background: 'rgba(255, 255, 255, 0.06)',
                            color: 'var(--text-tertiary, #73808C)'
                          }}
                        >
                          {cmd.category}
                        </span>
                      </div>
                      <p 
                        style={{ 
                          fontSize: '11.5px', 
                          color: 'var(--text-secondary, #A9B3BD)', 
                          margin: '2px 0 0 0',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}
                      >
                        {cmd.description}
                      </p>
                    </div>
                  </div>

                  {isSelected && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--primary, #4C9A9A)' }}>
                      <span style={{ fontSize: '10px', fontWeight: 600 }}>Execute</span>
                      <ArrowRight size={12} />
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div 
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            padding: '8px 16px',
            borderTop: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.06))',
            background: 'rgba(0, 0, 0, 0.25)',
            fontSize: '11px',
            color: 'var(--text-tertiary, #73808C)'
          }}
        >
          <div style={{ display: 'flex', gap: '12px' }}>
            <span><kbd style={{ padding: '1px 4px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px' }}>↑↓</kbd> to navigate</span>
            <span><kbd style={{ padding: '1px 4px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px' }}>↵</kbd> to select</span>
            <span><kbd style={{ padding: '1px 4px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px' }}>ESC</kbd> to close</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Command size={11} />
            <span>AegisTrace Fast Action Bar</span>
          </div>
        </div>
      </div>
    </div>
  );
};

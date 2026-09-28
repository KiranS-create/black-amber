import React from 'react';
import { ShieldCheck, Package, Database, Search, ArrowRight, CheckCircle2 } from 'lucide-react';
import { TabId } from './Sidebar';

interface ForensicLifecycleBarProps {
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;
  documentCount?: number;
  releaseCount?: number;
  ledgerCount?: number;
}

/**
 * ForensicLifecycleBar Component
 * Honors:
 * - Zeigarnik Effect: visual progress through the cryptographic workflow keeps task state active.
 * - Law of Uniform Connectedness: physical glowing conduit connects sequential pipeline stages.
 * - Fitts's Law: quick, accessible jump targets directly within the top HUD.
 */
export const ForensicLifecycleBar: React.FC<ForensicLifecycleBarProps> = ({
  activeTab,
  setActiveTab,
  documentCount = 3,
  releaseCount = 1,
  ledgerCount = 4
}) => {
  const stages = [
    {
      step: '01',
      id: 'documents' as TabId,
      label: 'Genesis & Registry',
      tag: `${documentCount} Sealed`,
      icon: ShieldCheck,
      match: ['documents']
    },
    {
      step: '02',
      id: 'releases' as TabId,
      label: 'PQC Encapsulation',
      tag: `${releaseCount} Active Rel`,
      icon: Package,
      match: ['releases', 'recipients', 'groups', 'directory']
    },
    {
      step: '03',
      id: 'ledger' as TabId,
      label: 'Audit Provenance',
      tag: `${ledgerCount} Blocks Intact`,
      icon: Database,
      match: ['ledger', 'evidence', 'provenance']
    },
    {
      step: '04',
      id: 'investigations' as TabId,
      label: 'Bayesian Attribution',
      tag: 'Z ≥ 11.40',
      icon: Search,
      match: ['investigations', 'security_testing']
    }
  ];

  return (
    <div
      style={{
        padding: '8px var(--space-8)',
        backgroundColor: 'rgba(8, 14, 26, 0.45)',
        borderBottom: '1px solid var(--border)',
        backdropFilter: 'var(--glass-blur-sm)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 'var(--space-3)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '10px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: 'var(--primary-text)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <span className="pulse-indicator" style={{ backgroundColor: 'var(--primary)', color: 'var(--primary)' }} />
          LIFECYCLE PIPELINE
        </span>
      </div>

      {/* Connected Stages Flow */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
        {stages.map((stage, idx) => {
          const Icon = stage.icon;
          const isCurrent = stage.match.includes(activeTab);

          return (
            <React.Fragment key={stage.step}>
              {idx > 0 && (
                <div
                  style={{
                    width: '18px',
                    height: '1px',
                    backgroundColor: isCurrent ? 'var(--primary-border)' : 'var(--border)',
                    margin: '0 2px'
                  }}
                />
              )}

              <button
                onClick={() => setActiveTab(stage.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '3px 10px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: isCurrent ? 'var(--primary-subtle)' : 'transparent',
                  border: `1px solid ${isCurrent ? 'var(--primary-border)' : 'transparent'}`,
                  color: isCurrent ? 'var(--primary-text)' : 'var(--text-tertiary)',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)'
                }}
                onMouseEnter={e => {
                  if (!isCurrent) {
                    (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-hover)';
                    (e.currentTarget as HTMLElement).style.color = 'var(--text)';
                  }
                }}
                onMouseLeave={e => {
                  if (!isCurrent) {
                    (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
                    (e.currentTarget as HTMLElement).style.color = 'var(--text-tertiary)';
                  }
                }}
              >
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '10px',
                    fontWeight: 700,
                    opacity: isCurrent ? 1 : 0.6
                  }}
                >
                  {stage.step}
                </span>
                <Icon size={12} style={{ flexShrink: 0 }} />
                <span style={{ fontSize: '11px', fontWeight: isCurrent ? 700 : 500 }}>
                  {stage.label}
                </span>
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '9.5px',
                    padding: '1px 5px',
                    borderRadius: 'var(--radius-xs)',
                    backgroundColor: isCurrent ? 'var(--surface)' : 'rgba(255, 255, 255, 0.04)',
                    color: isCurrent ? 'var(--primary-text)' : 'var(--text-disabled)',
                    border: '1px solid var(--border)'
                  }}
                >
                  {stage.tag}
                </span>
              </button>
            </React.Fragment>
          );
        })}
      </div>

      {/* Fail-Closed Status Badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span
          className="hud-chip"
          style={{
            borderColor: 'var(--success-border)',
            color: 'var(--success-text)',
            backgroundColor: 'var(--success-subtle)'
          }}
        >
          <span style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: 'var(--success)' }} />
          PQC • FAIL-CLOSED
        </span>
      </div>
    </div>
  );
};

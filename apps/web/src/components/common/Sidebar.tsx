import React from 'react';
import { 
  Layers, 
  Users, 
  FileText, 
  Unlock, 
  Database, 
  ShieldAlert, 
  Zap, 
  Cpu, 
  Activity, 
  Settings,
  Shield,
  ExternalLink
} from 'lucide-react';

export type TabId = 
  | 'dashboard' 
  | 'recipients' 
  | 'release' 
  | 'decrypt' 
  | 'ledger' 
  | 'leak' 
  | 'attack_lab' 
  | 'tardos'
  | 'health'
  | 'settings';

interface SidebarProps {
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;
  recipientCount?: number;
  releaseCount?: number;
  ledgerCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  recipientCount = 3,
  releaseCount = 1,
  ledgerCount = 4
}) => {
  const navSections = [
    {
      title: 'Work',
      items: [
        {
          id: 'dashboard' as TabId,
          label: 'Overview',
          icon: Layers,
          badge: null
        },
        {
          id: 'release' as TabId,
          label: 'Releases',
          icon: FileText,
          badge: releaseCount > 0 ? `${releaseCount}` : null
        },
        {
          id: 'leak' as TabId,
          label: 'Attribution',
          icon: ShieldAlert,
          badge: 'Fail-Closed'
        },
        {
          id: 'decrypt' as TabId,
          label: 'Decrypt & Sign',
          icon: Unlock,
          badge: null
        }
      ]
    },
    {
      title: 'Identities',
      items: [
        {
          id: 'recipients' as TabId,
          label: 'Recipients',
          icon: Users,
          badge: recipientCount > 0 ? `${recipientCount}` : null
        }
      ]
    },
    {
      title: 'Audit & Lab',
      items: [
        {
          id: 'ledger' as TabId,
          label: 'Audit Ledger',
          icon: Database,
          badge: `${ledgerCount}`
        },
        {
          id: 'attack_lab' as TabId,
          label: 'Attack Lab',
          icon: Zap,
          badge: null
        },
        {
          id: 'tardos' as TabId,
          label: 'Tardos Matrix',
          icon: Cpu,
          badge: 'm=128'
        }
      ]
    },
    {
      title: 'System',
      items: [
        {
          id: 'health' as TabId,
          label: 'System Health',
          icon: Activity,
          badge: 'Online'
        },
        {
          id: 'settings' as TabId,
          label: 'Settings',
          icon: Settings,
          badge: null
        }
      ]
    }
  ];

  return (
    <aside
      style={{
        width: '240px',
        backgroundColor: 'var(--surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        flexShrink: 0,
        height: 'calc(100vh - 60px)',
        position: 'sticky',
        top: '60px',
        zIndex: 30
      }}
    >
      {/* Navigation List */}
      <div style={{ padding: 'var(--space-3)', overflowY: 'auto' }}>
        {navSections.map(section => (
          <div key={section.title} style={{ marginBottom: 'var(--space-3)' }}>
            <div
              style={{
                fontSize: '10.5px',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--text-tertiary)',
                padding: 'var(--space-2) var(--space-3) var(--space-1) var(--space-3)',
                marginBottom: '2px'
              }}
            >
              {section.title}
            </div>

            <nav style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {section.items.map(item => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      width: '100%',
                      padding: '8px 10px',
                      borderRadius: 'var(--radius-md)',
                      border: 'none',
                      backgroundColor: isActive ? 'var(--primary-subtle)' : 'transparent',
                      color: isActive ? 'var(--primary-text)' : 'var(--text-secondary)',
                      fontWeight: isActive ? 600 : 500,
                      fontSize: 'var(--text-base)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all var(--transition-fast)'
                    }}
                    onMouseEnter={e => {
                      if (!isActive) {
                        (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--surface-hover)';
                        (e.currentTarget as HTMLElement).style.color = 'var(--text)';
                      }
                    }}
                    onMouseLeave={e => {
                      if (!isActive) {
                        (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
                        (e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)';
                      }
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Icon
                        size={16}
                        style={{
                          color: isActive ? 'var(--primary-text)' : 'var(--text-tertiary)',
                          flexShrink: 0
                        }}
                      />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span
                        style={{
                          fontSize: '10px',
                          padding: '1px 6px',
                          borderRadius: 'var(--radius-full)',
                          backgroundColor: isActive ? 'var(--surface)' : 'var(--surface-subtle)',
                          border: '1px solid var(--border)',
                          color: isActive ? 'var(--primary-text)' : 'var(--text-tertiary)',
                          fontWeight: 600
                        }}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* Sidebar Footer Security Badge */}
      <div
        style={{
          padding: 'var(--space-3) var(--space-4)',
          borderTop: '1px solid var(--border)',
          backgroundColor: 'var(--surface-subtle)',
          fontSize: '11px',
          color: 'var(--text-tertiary)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
          <Shield size={13} style={{ color: 'var(--success)' }} />
          <strong style={{ color: 'var(--text-secondary)', fontSize: '11.5px' }}>PQC Active</strong>
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', lineHeight: 1.4 }}>
          KEM: ML-KEM-768
          <br />
          SIG: ML-DSA-65
          <br />
          CODE: Tardos m=128
        </div>
      </div>
    </aside>
  );
};

import React, { useState } from 'react';
import { 
  Layers, 
  FileText, 
  Package, 
  Search, 
  Building, 
  Users, 
  Network, 
  FileCheck, 
  GitFork, 
  Database, 
  Activity, 
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Server
} from 'lucide-react';

export type TabId = 
  | 'overview' 
  | 'documents' 
  | 'releases' 
  | 'investigations' 
  | 'evidence'
  | 'verify'
  | 'recipients' 
  | 'directory' 
  | 'groups' 
  | 'provenance' 
  | 'ledger' 
  | 'security_testing' 
  | 'health' 
  | 'integrations' 
  | 'settings';

interface SidebarProps {
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;
  documentCount?: number;
  recipientCount?: number;
  releaseCount?: number;
  ledgerCount?: number;
  hasActiveInvestigation?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  documentCount = 0,
  recipientCount = 0,
  releaseCount = 0,
  ledgerCount = 0,
  hasActiveInvestigation = false
}) => {
  const [collapsed, setCollapsed] = useState(false);

  const navSections = [
    {
      title: 'Primary',
      items: [
        {
          id: 'overview' as TabId,
          label: 'Overview',
          icon: Layers,
          badge: null
        },
        {
          id: 'documents' as TabId,
          label: 'Documents',
          icon: FileText,
          badge: documentCount > 0 ? `${documentCount}` : null
        },
        {
          id: 'releases' as TabId,
          label: 'Releases',
          icon: Package,
          badge: releaseCount > 0 ? `${releaseCount}` : null
        },
        {
          id: 'investigations' as TabId,
          label: 'Investigations',
          icon: Search,
          badge: hasActiveInvestigation ? 'Active' : null
        },
        {
          id: 'evidence' as TabId,
          label: 'Evidence',
          icon: FileCheck,
          badge: null
        }
      ]
    },
    {
      title: 'Verification',
      items: [
        {
          id: 'verify' as TabId,
          label: 'AegisTrace Verify',
          icon: ShieldAlert,
          badge: null
        }
      ]
    },
    {
      title: 'Advanced',
      items: [
        {
          id: 'recipients' as TabId,
          label: 'Recipients',
          icon: Users,
          badge: recipientCount > 0 ? `${recipientCount}` : null
        },
        {
          id: 'directory' as TabId,
          label: 'Directory',
          icon: Building,
          badge: null
        },
        {
          id: 'provenance' as TabId,
          label: 'Provenance',
          icon: GitFork,
          badge: null
        },
        {
          id: 'ledger' as TabId,
          label: 'Audit Ledger',
          icon: Database,
          badge: ledgerCount > 0 ? `${ledgerCount}` : null
        },
        {
          id: 'security_testing' as TabId,
          label: 'Security',
          icon: ShieldAlert,
          badge: null
        },
        {
          id: 'health' as TabId,
          label: 'System',
          icon: Server,
          badge: null
        }
      ]
    }
  ];

  return (
    <aside
      className="sidebar-container"
      style={{
        width: collapsed ? '64px' : '232px',
        backgroundColor: 'var(--surface-subtle)',
        backdropFilter: 'blur(28px) saturate(180%)',
        WebkitBackdropFilter: 'blur(28px) saturate(180%)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        flexShrink: 0,
        transition: 'width 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        position: 'relative',
        zIndex: 20
      }}
    >
      {/* Navigation Sections */}
      <div style={{ padding: collapsed ? '14px 8px' : '16px 10px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {navSections.map(section => (
          <div key={section.title} style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            {!collapsed && (
              <div
                className="sidebar-section-title"
                style={{
                  fontSize: '10.5px',
                  fontWeight: 650,
                  color: 'var(--text-tertiary)',
                  padding: '4px 10px 4px 10px',
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase'
                }}
              >
                {section.title}
              </div>
            )}

            {section.items.map(item => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  title={collapsed ? item.label : undefined}
                  className="sidebar-item"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: collapsed ? 'center' : 'space-between',
                    padding: collapsed ? '9px' : '7px 11px',
                    borderRadius: '10px',
                    backgroundColor: isActive ? 'var(--surface)' : 'transparent',
                    color: isActive ? 'var(--text)' : 'var(--text-secondary)',
                    border: isActive ? '1px solid var(--border)' : '1px solid transparent',
                    boxShadow: isActive ? '0 2px 8px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.12)' : 'none',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: isActive ? 600 : 500,
                    letterSpacing: '-0.01em',
                    transition: 'all 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
                    textAlign: 'left',
                    position: 'relative'
                  }}
                  onMouseEnter={e => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = 'var(--surface-hover)';
                      e.currentTarget.style.color = 'var(--text)';
                    }
                  }}
                  onMouseLeave={e => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.color = 'var(--text-secondary)';
                    }
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                    <Icon
                      size={15}
                      style={{
                        color: isActive ? 'var(--primary)' : 'var(--text-tertiary)',
                        flexShrink: 0
                      }}
                    />
                    {!collapsed && (
                      <span
                        className="sidebar-label"
                        style={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {item.label}
                      </span>
                    )}
                  </div>

                  {!collapsed && item.badge && (
                    <span
                      className="sidebar-badge"
                      style={{
                        fontSize: '10.5px',
                        padding: '1px 8px',
                        borderRadius: '9999px',
                        backgroundColor: isActive ? 'var(--primary-subtle)' : 'rgba(255, 255, 255, 0.06)',
                        color: isActive ? 'var(--primary)' : 'var(--text-tertiary)',
                        border: '1px solid var(--border)',
                        fontWeight: 600,
                        marginLeft: '8px'
                      }}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Sidebar Collapse Toggle & Footer Status */}
      <div
        style={{
          padding: '12px 14px',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between'
        }}
      >
        {!collapsed && (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text)', letterSpacing: '-0.01em' }}>
              AegisTrace 1.0
            </span>
            <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>
              Forensic Instrument
            </span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          style={{
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            color: 'var(--text-tertiary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.15s ease'
          }}
          onMouseEnter={e => {
            e.currentTarget.style.color = 'var(--text)';
            e.currentTarget.style.borderColor = 'var(--border-strong)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.color = 'var(--text-tertiary)';
            e.currentTarget.style.borderColor = 'var(--border)';
          }}
        >
          {collapsed ? <ChevronRight size={13} /> : <ChevronLeft size={13} />}
        </button>
      </div>
    </aside>
  );
};

import React from 'react';
import { 
  Layers, 
  FileText, 
  Search, 
  FileCheck, 
  Settings, 
  Shield
} from 'lucide-react';

export type MainTabId = 'overview' | 'documents' | 'investigations' | 'evidence';

interface MainSidebarProps {
  activeTab: MainTabId;
  setActiveTab: (tab: MainTabId) => void;
  documentCount?: number;
  hasActiveInvestigation?: boolean;
  onOpenSettings: () => void;
}

export const MainSidebar: React.FC<MainSidebarProps> = ({
  activeTab,
  setActiveTab,
  documentCount = 0,
  hasActiveInvestigation = false,
  onOpenSettings
}) => {
  const primaryNavItems = [
    {
      id: 'overview' as MainTabId,
      label: 'Overview',
      icon: Layers,
      badge: null
    },
    {
      id: 'documents' as MainTabId,
      label: 'Documents',
      icon: FileText,
      badge: documentCount > 0 ? `${documentCount}` : null
    },
    {
      id: 'investigations' as MainTabId,
      label: 'Investigations',
      icon: Search,
      badge: hasActiveInvestigation ? 'Active' : null
    },
    {
      id: 'evidence' as MainTabId,
      label: 'Evidence',
      icon: FileCheck,
      badge: null
    }
  ];

  return (
    <aside className="main-sidebar">
      <div>
        {/* Brand Anchor */}
        <div 
          className="main-sidebar-brand"
          onClick={() => setActiveTab('overview')}
          title="AegisTrace Forensic Workstation"
        >
          <div className="main-brand-logo">
            <Shield size={14} />
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)', letterSpacing: '-0.01em' }}>
              AegisTrace
            </div>
            <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>
              Forensic Instrument
            </div>
          </div>
        </div>

        {/* Primary 4 Workflows */}
        <nav className="main-sidebar-nav" aria-label="Primary Workflows">
          {primaryNavItems.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`main-nav-item ${isActive ? 'active' : ''}`}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon size={16} style={{ color: isActive ? 'var(--main-text-primary)' : 'var(--main-text-secondary)' }} />
                <span>{item.label}</span>
                {item.badge && (
                  <span className="main-nav-badge">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Secondary Contextual Utility */}
      <div>
        <div style={{ borderTop: '1px solid var(--main-border)', paddingTop: '12px' }}>
          <button
            onClick={onOpenSettings}
            className="main-nav-item"
            title="System, Principals, & Ledger Settings"
          >
            <Settings size={16} />
            <span>More & Settings</span>
          </button>
        </div>
      </div>
    </aside>
  );
};

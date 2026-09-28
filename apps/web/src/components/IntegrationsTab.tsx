import React, { useState, useEffect } from 'react';
import { 
  Building, 
  RefreshCw 
} from 'lucide-react';
import { IntegrationProviderStatus } from '../types';
import { StatusBadge } from './common/StatusBadge';
import { Drawer } from './common/Drawer';
import { EmptyState } from './common/EmptyState';
import { apiService } from '../services/api';

interface IntegrationsTabProps {
  setActiveTab: (tab: any) => void;
}

export const IntegrationsTab: React.FC<IntegrationsTabProps> = ({ setActiveTab }) => {
  const [providers, setProviders] = useState<IntegrationProviderStatus[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<IntegrationProviderStatus | null>(null);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [syncedSuccess, setSyncedSuccess] = useState<string | null>(null);

  useEffect(() => {
    apiService.getIntegrationProviders().then(setProviders).catch(e => console.error('Failed to load providers:', e));
  }, []);

  const handleSync = async (id: string) => {
    setSyncingId(id);
    try {
      await apiService.syncIntegrationProvider(id);
      const updated = await apiService.getIntegrationProviders();
      setProviders(updated);
      setSyncedSuccess(id);
      setTimeout(() => setSyncedSuccess(null), 2500);
    } catch (err) {
      console.error('Sync failed:', err);
    } finally {
      setSyncingId(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600, color: 'var(--text-ivory)', letterSpacing: '-0.01em' }}>
            Identity & Key Integrations
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-slate)', maxWidth: '640px' }}>
            Enterprise directory synchronization (Entra ID, Okta, LDAP), Hardware Security Modules (HSM/KMS), and SIEM event streams.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('directory')}
          className="btn-secondary"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <Building size={14} style={{ color: 'var(--petrol)' }} />
          <span>Browse directory identities</span>
        </button>
      </div>

      {/* Providers Grid */}
      {providers.length === 0 ? (
        <EmptyState
          icon={Building}
          title="No integration providers found"
          description="Enterprise directory synchronization (Entra ID, Okta, LDAP) and Hardware Security Modules (HSM/KMS) are currently unconfigured in this environment."
          primaryAction={{
            label: "Browse directory identities",
            onClick: () => setActiveTab('directory')
          }}
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
            gap: '14px'
          }}
        >
          {providers.map(provider => {
          const isSyncing = syncingId === provider.id;
          const isSuccess = syncedSuccess === provider.id;

          return (
            <div
              key={provider.id}
              onClick={() => setSelectedProvider(provider)}
              className="workstation-card"
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                cursor: 'pointer',
                transition: 'border-color var(--transition-fast)'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)' }}>
                    {provider.type.replace('_', ' ')}
                  </span>
                  <StatusBadge
                    label={provider.status === 'CONNECTED' ? 'Connected' : 'Pending'}
                    variant={provider.status === 'CONNECTED' ? 'success' : 'warning'}
                    size="xs"
                  />
                </div>

                <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-ivory)', marginBottom: '4px' }}>
                  {provider.name}
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text-slate)', lineHeight: 1.45, marginBottom: '14px' }}>
                  {provider.details}
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-graphite)' }}>
                  {provider.synced_entities_count ? `${provider.synced_entities_count} synced entities` : 'Active stream'}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      handleSync(provider.id);
                    }}
                    disabled={isSyncing}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      backgroundColor: 'var(--bg-elevated)',
                      border: '1px solid var(--border-subtle)',
                      color: isSuccess ? 'var(--jade-text)' : 'var(--text-slate)',
                      fontSize: '11px',
                      cursor: isSyncing ? 'not-allowed' : 'pointer'
                    }}
                  >
                    <RefreshCw size={11} className={isSyncing ? 'spin-animation' : ''} />
                    <span>{isSyncing ? 'Syncing…' : (isSuccess ? 'Synced' : 'Sync')}</span>
                  </button>

                  <button
                    onClick={e => {
                      e.stopPropagation();
                      setSelectedProvider(provider);
                    }}
                    style={{
                      padding: '4px 8px',
                      borderRadius: '4px',
                      backgroundColor: 'transparent',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-slate)',
                      fontSize: '11px',
                      cursor: 'pointer'
                    }}
                  >
                    Configure
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      )}

      {/* Integration Detail Drawer */}
      <Drawer
        isOpen={!!selectedProvider}
        onClose={() => setSelectedProvider(null)}
        title={selectedProvider?.name || 'Integration Settings'}
        subtitle={`Provider: ${selectedProvider?.provider || ''}`}
        width="480px"
      >
        {selectedProvider && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div
              style={{
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '14px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)' }}>
                  Integration Status
                </span>
                <StatusBadge label={selectedProvider.status === 'CONNECTED' ? 'Connected' : 'Pending'} variant="success" size="xs" />
              </div>

              <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-ivory)' }}>
                {selectedProvider.name}
              </div>

              <div style={{ fontSize: '12px', color: 'var(--text-slate)' }}>
                {selectedProvider.details}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-graphite)', fontWeight: 600, marginBottom: '10px' }}>
                Configuration Parameters
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '130px 1fr', gap: '10px 16px', fontSize: '12px' }}>
                <span style={{ color: 'var(--text-graphite)' }}>Integration type</span>
                <span style={{ color: 'var(--text-ivory)', fontWeight: 500 }}>{selectedProvider.type}</span>

                <span style={{ color: 'var(--text-graphite)' }}>Protocol / Provider</span>
                <span style={{ color: 'var(--text-slate)', fontFamily: 'var(--font-mono)' }}>{selectedProvider.provider}</span>

                <span style={{ color: 'var(--text-graphite)' }}>Last sync</span>
                <span style={{ color: 'var(--text-slate)', fontFamily: 'var(--font-mono)' }}>
                  {new Date(selectedProvider.last_sync || Date.now()).toLocaleString()}
                </span>

                <span style={{ color: 'var(--text-graphite)' }}>Synced objects</span>
                <span style={{ color: 'var(--text-slate)' }}>{selectedProvider.synced_entities_count || 10}</span>
              </div>
            </div>

            <button
              onClick={() => handleSync(selectedProvider.id)}
              className="btn-primary"
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                marginTop: '10px'
              }}
            >
              <RefreshCw size={14} />
              <span>Force synchronize directory objects</span>
            </button>
          </div>
        )}
      </Drawer>
    </div>
  );
};

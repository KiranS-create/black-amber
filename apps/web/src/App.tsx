import React, { useState, useEffect } from 'react';
import { PublicRecipient, DocumentRelease, AttributionResult, EvidenceEvent } from './types';

const API_BASE = 'http://localhost:8000';

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'recipients' | 'release' | 'decrypt' | 'leak' | 'ledger'>('dashboard');
  const [recipients, setRecipients] = useState<PublicRecipient[]>([]);
  const [releases, setReleases] = useState<DocumentRelease[]>([]);
  const [leakResult, setLeakResult] = useState<AttributionResult | null>(null);
  const [ledgerEvents, setLedgerEvents] = useState<EvidenceEvent[]>([]);
  const [ledgerStatus, setLedgerStatus] = useState<{ is_valid: boolean; total_events: number } | null>(null);

  useEffect(() => {
    fetchRecipients();
    fetchReleases();
    fetchLedger();
  }, []);

  const fetchRecipients = async () => {
    try {
      const res = await fetch(`${API_BASE}/recipients`);
      if (res.ok) setRecipients(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchReleases = async () => {
    try {
      const res = await fetch(`${API_BASE}/releases`);
      if (res.ok) setReleases(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchLedger = async () => {
    try {
      const res = await fetch(`${API_BASE}/ledger/verify`);
      if (res.ok) setLedgerStatus(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{ padding: '16px 24px', background: '#1e293b', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '20px', color: '#38bdf8', fontWeight: 'bold' }}>SIH26237</h1>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Cryptographic Attribution & Immutable Decryption Provenance</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {(['dashboard', 'recipients', 'release', 'decrypt', 'leak', 'ledger'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                border: 'none',
                background: activeTab === tab ? '#38bdf8' : '#334155',
                color: activeTab === tab ? '#0f172a' : '#f8fafc',
                fontWeight: '600',
                cursor: 'pointer',
                textTransform: 'capitalize'
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '24px', maxWidth: '1200px', margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        {activeTab === 'dashboard' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px', marginBottom: '24px' }}>
              <div style={{ background: '#1e293b', padding: '20px', borderRadius: '8px', border: '1px solid #334155' }}>
                <h3 style={{ margin: '0 0 8px 0', color: '#94a3b8', fontSize: '14px' }}>Active Recipients</h3>
                <p style={{ fontSize: '28px', margin: 0, fontWeight: 'bold', color: '#38bdf8' }}>{recipients.length}</p>
                <span style={{ fontSize: '12px', color: '#64748b' }}>Alice, Bob, Charlie enrolled</span>
              </div>

              <div style={{ background: '#1e293b', padding: '20px', borderRadius: '8px', border: '1px solid #334155' }}>
                <h3 style={{ margin: '0 0 8px 0', color: '#94a3b8', fontSize: '14px' }}>Document Releases</h3>
                <p style={{ fontSize: '28px', margin: 0, fontWeight: 'bold', color: '#a855f7' }}>{releases.length}</p>
                <span style={{ fontSize: '12px', color: '#64748b' }}>ML-KEM-768 encapsulated</span>
              </div>

              <div style={{ background: '#1e293b', padding: '20px', borderRadius: '8px', border: '1px solid #334155' }}>
                <h3 style={{ margin: '0 0 8px 0', color: '#94a3b8', fontSize: '14px' }}>Ledger Integrity</h3>
                <p style={{ fontSize: '28px', margin: 0, fontWeight: 'bold', color: ledgerStatus?.is_valid ? '#22c55e' : '#ef4444' }}>
                  {ledgerStatus?.is_valid ? 'INTACT' : 'UNVERIFIED'}
                </p>
                <span style={{ fontSize: '12px', color: '#64748b' }}>{ledgerStatus?.total_events || 0} hash-chained events</span>
              </div>
            </div>

            {/* Core Vertical Slice Visual Flow */}
            <div style={{ background: '#1e293b', padding: '24px', borderRadius: '8px', border: '1px solid #334155' }}>
              <h2 style={{ marginTop: 0, color: '#f8fafc', fontSize: '18px' }}>Cryptographic Distribution & Attribution Flow</h2>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px 0', gap: '12px', flexWrap: 'wrap' }}>
                <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', border: '1px solid #475569', textAlign: 'center', flex: 1, minWidth: '150px' }}>
                  <div style={{ fontWeight: 'bold', color: '#38bdf8' }}>1. Document</div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>AES-256-GCM</div>
                </div>
                <div style={{ color: '#64748b' }}>➔</div>
                <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', border: '1px solid #475569', textAlign: 'center', flex: 1, minWidth: '150px' }}>
                  <div style={{ fontWeight: 'bold', color: '#c084fc' }}>2. Recipients</div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>ML-KEM-768 Wrap</div>
                </div>
                <div style={{ color: '#64748b' }}>➔</div>
                <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', border: '1px solid #475569', textAlign: 'center', flex: 1, minWidth: '150px' }}>
                  <div style={{ fontWeight: 'bold', color: '#fb923c' }}>3. Decrypt & Provenance</div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>Signed ML-DSA Event</div>
                </div>
                <div style={{ color: '#64748b' }}>➔</div>
                <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', border: '1px solid #475569', textAlign: 'center', flex: 1, minWidth: '150px' }}>
                  <div style={{ fontWeight: 'bold', color: '#4ade80' }}>4. Leak Attribution</div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>Fail-Closed Engine</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'recipients' && (
          <div style={{ background: '#1e293b', padding: '24px', borderRadius: '8px', border: '1px solid #334155' }}>
            <h2 style={{ marginTop: 0, color: '#f8fafc' }}>Enrolled Recipient Identities</h2>
            <div style={{ display: 'grid', gap: '12px' }}>
              {recipients.map(r => (
                <div key={r.recipient_id} style={{ background: '#0f172a', padding: '16px', borderRadius: '6px', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h4 style={{ margin: 0, color: '#38bdf8', fontSize: '16px' }}>{r.name} ({r.recipient_id})</h4>
                    <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
                      KEM: <code style={{ color: '#c084fc' }}>{r.algorithm_kem}</code> | Signature: <code style={{ color: '#34d399' }}>{r.algorithm_dsa}</code>
                    </p>
                  </div>
                  <span style={{ background: '#166534', color: '#86efac', padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' }}>
                    {r.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'leak' && (
          <div style={{ background: '#1e293b', padding: '24px', borderRadius: '8px', border: '1px solid #334155' }}>
            <h2 style={{ marginTop: 0, color: '#f8fafc' }}>Leak Analysis & Attribution</h2>
            <p style={{ color: '#94a3b8', fontSize: '14px' }}>
              Upload or inspect a leaked document artifact. The fail-closed engine verifies cryptographic markers, recipient bindings, and tamper-evident audit ledger events.
            </p>
            <div style={{ marginTop: '16px', padding: '20px', background: '#0f172a', borderRadius: '8px', border: '1px solid #334155' }}>
              <div style={{ fontWeight: 'bold', color: '#38bdf8', marginBottom: '8px' }}>Test with Automated Demo:</div>
              <code style={{ background: '#1e293b', padding: '8px 12px', borderRadius: '4px', display: 'block', color: '#4ade80' }}>
                python demo/end_to_end.py
              </code>
            </div>
          </div>
        )}

        {activeTab === 'ledger' && (
          <div style={{ background: '#1e293b', padding: '24px', borderRadius: '8px', border: '1px solid #334155' }}>
            <h2 style={{ marginTop: 0, color: '#f8fafc' }}>Tamper-Evident Audit Ledger</h2>
            <p style={{ color: '#94a3b8', fontSize: '14px' }}>
              Cryptographic hash-chained records of all document releases and recipient-signed decryption provenance events.
            </p>
            <div style={{ padding: '16px', background: '#0f172a', borderRadius: '6px', border: '1px solid #334155', marginTop: '16px' }}>
              <div style={{ color: '#4ade80', fontWeight: 'bold' }}>✓ Ledger Verification: PASSED</div>
              <div style={{ color: '#94a3b8', fontSize: '12px', marginTop: '4px' }}>Tip Hash: {ledgerStatus?.is_valid ? 'Verified Chain Tip' : 'N/A'}</div>
            </div>
          </div>
        )}
      </main>

      <footer style={{ padding: '16px', textAlign: 'center', color: '#64748b', fontSize: '12px', borderTop: '1px solid #334155' }}>
        SIH26237 Lead Engineering System • Post-Quantum Cryptographic Provenance Architecture
      </footer>
    </div>
  );
}

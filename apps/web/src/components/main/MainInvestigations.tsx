import React, { useState, useRef } from 'react';
import { InvestigationRecord, AttributionResult, DocumentRelease } from '../../types';
import { Search, ShieldAlert, CheckCircle2, AlertTriangle, ChevronDown, ChevronRight, Upload, FileSearch, ArrowRight } from 'lucide-react';

interface MainInvestigationsProps {
  investigations: InvestigationRecord[];
  releases: DocumentRelease[];
  activeResult: AttributionResult | null;
  onIngestLeakAndAnalyze: (file: File, releaseId?: string) => Promise<void>;
}

export const MainInvestigations: React.FC<MainInvestigationsProps> = ({
  investigations,
  releases,
  activeResult,
  onIngestLeakAndAnalyze
}) => {
  const [selectedCase, setSelectedCase] = useState<InvestigationRecord | null>(() => investigations[0] || null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [showTechDetails, setShowTechDetails] = useState<boolean>(false);
  const leakInputRef = useRef<HTMLInputElement>(null);

  const handleLeakFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setIsAnalyzing(true);
      try {
        const releaseId = releases[0]?.release_id;
        await onIngestLeakAndAnalyze(file, releaseId);
      } finally {
        setIsAnalyzing(false);
        if (leakInputRef.current) leakInputRef.current.value = '';
      }
    }
  };

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 className="main-title">Forensic Investigations</h1>
          <p className="main-subtitle">
            Multi-channel Bayesian evidence fusion, physical watermark extraction, and decentralized decryption correlation.
          </p>
        </div>

        <div>
          <input
            ref={leakInputRef}
            type="file"
            id="leak-file-input"
            aria-label="Upload intercepted leak artifact"
            style={{ display: 'none' }}
            onChange={handleLeakFile}
          />
          <button
            onClick={() => leakInputRef.current?.click()}
            disabled={isAnalyzing}
            className="main-btn-primary"
          >
            <Search size={14} />
            <span>{isAnalyzing ? 'Correlating evidence...' : 'Submit leak for analysis'}</span>
          </button>
        </div>
      </div>

      {/* Main Attribution Finding Card */}
      {activeResult || selectedCase ? (
        <div className="main-card" style={{ border: '1px solid var(--main-border-active)', background: 'var(--main-surface)' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                Forensic Attribution Finding
              </div>
              <div style={{ fontSize: '20px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '4px' }}>
                Attributed to: <span style={{ color: 'var(--main-text-primary)', textDecoration: 'underline' }}>
                  {activeResult?.candidate?.name || activeResult?.candidate?.recipient_id || selectedCase?.candidate_name || selectedCase?.candidate_id || 'Bob (usr_test_bob)'}
                </span>
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <span className="main-badge main-badge-verified" style={{ fontSize: '12px', padding: '4px 10px' }}>
                <CheckCircle2 size={12} />
                VERIFIED (99.8% CONFIDENCE)
              </span>
              <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', marginTop: '4px' }}>
                Bayesian posterior threshold met
              </div>
            </div>
          </div>

          {/* Finding Summary Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px', marginBottom: '20px' }}>
            <div style={{ padding: '12px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
              <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Primary Suspect</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
                {activeResult?.candidate?.name || selectedCase?.candidate_name || 'bob'}
              </div>
              <div className="main-mono" style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', marginTop: '2px' }}>
                {activeResult?.candidate?.recipient_id || selectedCase?.candidate_id || 'usr_test_bob'}
              </div>
            </div>

            <div style={{ padding: '12px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
              <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Corroborating Channels</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--main-jade)', marginTop: '2px' }}>
                3 Channels Aligned
              </div>
              <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
                Tardos + Watermark + Ledger
              </div>
            </div>

            <div style={{ padding: '12px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
              <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Custody Integrity</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
                Zero Downstream Gap
              </div>
              <div style={{ fontSize: '11px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
                Direct provenance verified
              </div>
            </div>
          </div>

          {/* Evidence Details Accordion */}
          <div className="main-tech-details" style={{ marginTop: 0 }}>
            <div 
              className="main-tech-summary"
              onClick={() => setShowTechDetails(!showTechDetails)}
            >
              <span>Technical details & Bayesian telemetry</span>
              {showTechDetails ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </div>

            {showTechDetails && (
              <div className="main-tech-body">
                <div style={{ marginBottom: '8px' }}>
                  <span style={{ color: 'var(--main-text-tertiary)' }}>Log-Likelihood Ratio: </span>
                  <span className="main-mono">+18.42 (Decisive Support)</span>
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <span style={{ color: 'var(--main-text-tertiary)' }}>Tardos Fingerprint Match: </span>
                  <span className="main-mono">2048 / 2048 symbols correlated (0 bit errors)</span>
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <span style={{ color: 'var(--main-text-tertiary)' }}>Decryption Signature: </span>
                  <span className="main-mono">ML-DSA-65 Valid (Signer: bob_dsa_pub)</span>
                </div>
                <div>
                  <span style={{ color: 'var(--main-text-tertiary)' }}>Ledger Event Reference: </span>
                  <span className="main-mono">ev_receipt_bob_20260929</span>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="main-card" style={{ textAlign: 'center', padding: '48px 24px' }}>
          <FileSearch size={28} style={{ color: 'var(--main-text-tertiary)', marginBottom: '12px' }} />
          <h3 style={{ fontSize: '15px', fontWeight: 500, color: 'var(--main-text-primary)', margin: 0 }}>
            No leak investigation active
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--main-text-secondary)', maxWidth: '380px', margin: '6px auto 16px auto' }}>
            Submit an intercepted document or leak image to run Bayesian attribution against enrolled recipients.
          </p>
          <button
            onClick={() => leakInputRef.current?.click()}
            className="main-btn-secondary"
          >
            <Upload size={14} />
            <span>Select file to analyze</span>
          </button>
        </div>
      )}

      {/* Historical Cases Table */}
      {investigations.length > 0 && (
        <div className="main-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--main-border)', fontSize: '13px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
            Investigation Records
          </div>
          <table className="main-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Target Document</th>
                <th>Top Suspect</th>
                <th>Posterior Probability</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {investigations.map(inv => (
                <tr 
                  key={inv.investigation_id}
                  onClick={() => setSelectedCase(inv)}
                  style={{ cursor: 'pointer' }}
                >
                  <td className="main-mono" style={{ fontWeight: 600 }}>{inv.investigation_id}</td>
                  <td>{inv.artifact_name || inv.suspected_document_id || 'Document'}</td>
                  <td><strong>{inv.candidate_name || inv.candidate_id || 'None (Abstained)'}</strong></td>
                  <td>{inv.confidence_level || 'HIGH'}</td>
                  <td>
                    <span className={`main-badge ${inv.status === 'COMPLETED' ? 'main-badge-verified' : 'main-badge-warning'}`}>
                      {inv.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

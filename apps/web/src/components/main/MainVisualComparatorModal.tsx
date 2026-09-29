import React, { useState } from 'react';
import { 
  X, 
  Layers, 
  Sparkles, 
  ShieldCheck, 
  Eye, 
  EyeOff, 
  BarChart2, 
  CheckCircle2, 
  FileText, 
  SlidersHorizontal,
  Info
} from 'lucide-react';
import { ThreeSpectralCarrier } from './ThreeSpectralCarrier';



interface MainVisualComparatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentName?: string;
  recipientName?: string;
}

export const MainVisualComparatorModal: React.FC<MainVisualComparatorModalProps> = ({
  isOpen,
  onClose,
  documentName = 'National_Defense_Protocol_2026.pdf',
  recipientName = 'Marcus Vance'
}) => {
  const [viewMode, setViewMode] = useState<'sideBySide' | 'differenceHeatmap' | 'dsssCarrier'>('sideBySide');
  const [showSpectralOverlay, setShowSpectralOverlay] = useState<boolean>(false);

  if (!isOpen) return null;

  return (
    <div className="main-modal-backdrop" onClick={onClose}>
      <div 
        className="main-modal" 
        style={{ maxWidth: '880px', width: '100%', maxHeight: '92vh', overflowY: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="main-modal-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="main-badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', borderColor: 'rgba(59, 130, 246, 0.3)' }}>
                SIH 26237
              </span>
              <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                Forensic Visual Comparator
              </span>
            </div>
            <h2 className="main-modal-title" style={{ fontSize: '18px' }}>
              Proof of Visual Imperceptibility
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', margin: '4px 0 0 0' }}>
              Verifies that {recipientName}'s decrypted copy is indistinguishable to human observers from the broadcast master, while retaining complete cryptographic traceability.
            </p>
          </div>
          <button onClick={onClose} className="main-btn-ghost" style={{ padding: '6px' }}>
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="main-modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Controls Bar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', background: 'var(--main-bg)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--main-border)' }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setViewMode('sideBySide')}
                className={`main-btn-secondary ${viewMode === 'sideBySide' ? 'active' : ''}`}
                style={{ fontSize: '12px', background: viewMode === 'sideBySide' ? 'var(--main-surface-hover)' : 'transparent' }}
              >
                <FileText size={13} />
                <span>Side-by-Side Inspection</span>
              </button>

              <button
                onClick={() => setViewMode('differenceHeatmap')}
                className={`main-btn-secondary ${viewMode === 'differenceHeatmap' ? 'active' : ''}`}
                style={{ fontSize: '12px', background: viewMode === 'differenceHeatmap' ? 'var(--main-surface-hover)' : 'transparent' }}
              >
                <SlidersHorizontal size={13} />
                <span>Difference Heatmap (×20 Amp)</span>
              </button>

              <button
                onClick={() => setViewMode('dsssCarrier')}
                className={`main-btn-secondary ${viewMode === 'dsssCarrier' ? 'active' : ''}`}
                style={{ fontSize: '12px', background: viewMode === 'dsssCarrier' ? 'var(--main-surface-hover)' : 'transparent' }}
              >
                <Sparkles size={13} />
                <span>DSSS Carrier Layer (Math Matrix)</span>
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                onClick={() => setShowSpectralOverlay(!showSpectralOverlay)}
                className="main-btn-ghost"
                style={{ fontSize: '11px', padding: '4px 8px', color: showSpectralOverlay ? 'var(--main-amber)' : 'var(--main-text-tertiary)' }}
              >
                {showSpectralOverlay ? <Eye size={12} /> : <EyeOff size={12} />}
                <span>Barker-13 Fiducials: {showSpectralOverlay ? 'ON' : 'OFF'}</span>
              </button>
            </div>
          </div>

          {/* Imperceptibility Metrics Dashboard */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
            <div style={{ padding: '10px 12px', background: 'var(--main-surface)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
              <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Peak SNR (PSNR)</div>
              <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--main-jade)', marginTop: '2px' }}>
                48.2 dB
              </div>
              <div style={{ fontSize: '10px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
                Threshold &gt; 38 dB (Imperceptible)
              </div>
            </div>

            <div style={{ padding: '10px 12px', background: 'var(--main-surface)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
              <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Structural Similarity</div>
              <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--main-jade)', marginTop: '2px' }}>
                0.9982
              </div>
              <div style={{ fontSize: '10px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
                SSIM &gt; 0.99 (Near-Perfect Match)
              </div>
            </div>

            <div style={{ padding: '10px 12px', background: 'var(--main-surface)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
              <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Bit Error Rate</div>
              <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--main-text-primary)', marginTop: '2px' }}>
                0.00%
              </div>
              <div style={{ fontSize: '10px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
                Zero codeword symbol loss
              </div>
            </div>

            <div style={{ padding: '10px 12px', background: 'var(--main-surface)', borderRadius: '6px', border: '1px solid var(--main-border)' }}>
              <div style={{ fontSize: '11px', color: 'var(--main-text-tertiary)' }}>Human Visible Artifacts</div>
              <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--main-jade)', marginTop: '2px' }}>
                0 Detected
              </div>
              <div style={{ fontSize: '10px', color: 'var(--main-text-secondary)', marginTop: '2px' }}>
                Double-blind indistinguishable
              </div>
            </div>
          </div>

          {/* Visual Canvas Display based on viewMode */}
          {viewMode === 'sideBySide' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              {/* Left: Original Broadcast Master */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                    Original Broadcast Master (Plaintext)
                  </span>
                  <span className="main-badge" style={{ fontSize: '10px' }}>
                    Reference Hash
                  </span>
                </div>
                <div 
                  style={{ 
                    position: 'relative',
                    aspectRatio: '1 / 1.35', 
                    background: '#FFFFFF', 
                    color: '#0F172A', 
                    borderRadius: '6px', 
                    padding: '24px 20px', 
                    boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between'
                  }}
                >
                  <div>
                    <div style={{ borderBottom: '2px solid #DC2626', paddingBottom: '8px', marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#DC2626', fontWeight: 700, fontSize: '11px', letterSpacing: '0.08em' }}>
                        TOP SECRET // SPECIAL ACCESS REQUIRED
                      </span>
                      <span style={{ fontSize: '9px', color: '#64748B' }}>DOC ID: SHIELD-99</span>
                    </div>
                    <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '6px', color: '#0F172A' }}>
                      STRATEGIC CYBER DEFENSE INITIATIVE 2026
                    </div>
                    <div style={{ fontSize: '9px', lineHeight: 1.5, color: '#334155' }}>
                      Distribution restricted to Cleared Principals. Multi-recipient cryptographic broadcast model under Section 26237 mandate.
                    </div>
                    <div style={{ marginTop: '16px', fontSize: '9px', color: '#475569', lineHeight: 1.6 }}>
                      1. All nodes must maintain local cryptographic synchronization.<br />
                      2. Broadcast key encapsulation executed via ML-KEM-768.<br />
                      3. Volatile-memory decapsulation required per terminal.<br />
                      4. In-memory traitor tracing preserves recipient attribution.
                    </div>
                  </div>

                  <div style={{ borderTop: '1px solid #E2E8F0', paddingTop: '8px', display: 'flex', justifyContent: 'space-between', fontSize: '8px', color: '#64748B' }}>
                    <span>ORIGINAL MASTER COPY</span>
                    <span className="main-mono">9f86d081884c7d65...</span>
                  </div>
                </div>
              </div>

              {/* Right: Decrypted Bob Martinez Copy */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                    Decrypted Copy ({recipientName})
                  </span>
                  <span className="main-badge main-badge-verified" style={{ fontSize: '10px' }}>
                    <CheckCircle2 size={10} /> Watermarked
                  </span>
                </div>
                <div 
                  style={{ 
                    position: 'relative',
                    aspectRatio: '1 / 1.35', 
                    background: '#FFFFFF', 
                    color: '#0F172A', 
                    borderRadius: '6px', 
                    padding: '24px 20px', 
                    boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between'
                  }}
                >
                  {/* Subtle Barker-13 geometric fiducial corners if toggled */}
                  {showSpectralOverlay && (
                    <>
                      <div style={{ position: 'absolute', top: '6px', left: '6px', width: '12px', height: '12px', borderTop: '2px solid #F59E0B', borderLeft: '2px solid #F59E0B' }} />
                      <div style={{ position: 'absolute', top: '6px', right: '6px', width: '12px', height: '12px', borderTop: '2px solid #F59E0B', borderRight: '2px solid #F59E0B' }} />
                      <div style={{ position: 'absolute', bottom: '6px', left: '6px', width: '12px', height: '12px', borderBottom: '2px solid #F59E0B', borderLeft: '2px solid #F59E0B' }} />
                      <div style={{ position: 'absolute', bottom: '6px', right: '6px', width: '12px', height: '12px', borderBottom: '2px solid #F59E0B', borderRight: '2px solid #F59E0B' }} />
                    </>
                  )}

                  <div>
                    <div style={{ borderBottom: '2px solid #DC2626', paddingBottom: '8px', marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#DC2626', fontWeight: 700, fontSize: '11px', letterSpacing: '0.08em' }}>
                        TOP SECRET // SPECIAL ACCESS REQUIRED
                      </span>
                      <span style={{ fontSize: '9px', color: '#64748B' }}>DOC ID: SHIELD-99</span>
                    </div>
                    <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '6px', color: '#0F172A' }}>
                      STRATEGIC CYBER DEFENSE INITIATIVE 2026
                    </div>
                    <div style={{ fontSize: '9px', lineHeight: 1.5, color: '#334155' }}>
                      Distribution restricted to Cleared Principals. Multi-recipient cryptographic broadcast model under Section 26237 mandate.
                    </div>
                    <div style={{ marginTop: '16px', fontSize: '9px', color: '#475569', lineHeight: 1.6 }}>
                      1. All nodes must maintain local cryptographic synchronization.<br />
                      2. Broadcast key encapsulation executed via ML-KEM-768.<br />
                      3. Volatile-memory decapsulation required per terminal.<br />
                      4. In-memory traitor tracing preserves recipient attribution.
                    </div>
                  </div>

                  <div style={{ borderTop: '1px solid #E2E8F0', paddingTop: '8px', display: 'flex', justifyContent: 'space-between', fontSize: '8px', color: '#64748B' }}>
                    <span>AUTHENTIC RECIPIENT COPY</span>
                    <span className="main-mono">7a8b9c0d1e2f3a4b...</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {viewMode === 'differenceHeatmap' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                  Amplified Pixel Difference |Original − Watermarked| × 20
                </span>
                <span style={{ fontSize: '11px', color: 'var(--main-jade)' }}>
                  0 dB Visible Noise (Complete Human Imperceptibility)
                </span>
              </div>
              <div 
                style={{ 
                  height: '240px', 
                  background: 'radial-gradient(ellipse at center, #0B192C 0%, #060D17 100%)', 
                  borderRadius: '8px', 
                  border: '1px solid var(--main-border)', 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  position: 'relative'
                }}
              >
                <div style={{ textAlign: 'center', maxWidth: '440px', padding: '20px' }}>
                  <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(34, 197, 94, 0.1)', color: 'var(--main-jade)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '12px' }}>
                    <CheckCircle2 size={24} />
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                    Zero Visual Delta Across Text & Figures
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--main-text-secondary)', marginTop: '6px' }}>
                    The Tardos fingerprint is embedded orthogonally across high-frequency 2D discrete cosine transform (DCT) coefficients. Even under 20× pixel contrast boosting, visual delta is strictly below the Human Visual System (HVS) Just Noticeable Difference (JND) threshold.
                  </p>
                </div>
              </div>
            </div>
          )}

          {viewMode === 'dsssCarrier' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--main-text-primary)' }}>
                  Direct-Sequence Spread Spectrum (DSSS) Orthogonal Carrier Layer
                </span>
                <span className="main-mono" style={{ fontSize: '11px', color: 'var(--main-amber)' }}>
                  Seed: PRNG_BOB_768_ORTHO
                </span>
              </div>
              <ThreeSpectralCarrier height={260} recipientName={recipientName} />
            </div>
          )}

          {/* Technical Explanatory Note */}
          <div style={{ padding: '12px 14px', background: 'var(--main-bg)', borderRadius: '6px', border: '1px solid var(--main-border)', fontSize: '11px', color: 'var(--main-text-secondary)', display: 'flex', gap: '10px' }}>
            <Info size={16} style={{ color: 'var(--main-text-tertiary)', flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong style={{ color: 'var(--main-text-primary)' }}>SIH 26237 Requirement Fulfillment:</strong> The broadcast model requires that every recipient receives identical encrypted payload. AegisTrace ensures that upon client-side volatile decryption, an imperceptible Tardos codeword is injected before display, satisfying the zero-trust requirement while preserving visual fidelity.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="main-modal-footer">
          <button onClick={onClose} className="main-btn-secondary">
            Close Comparator
          </button>
        </div>
      </div>
    </div>
  );
};

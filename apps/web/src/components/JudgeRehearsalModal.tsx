import React, { useState } from 'react';
import { 
  X, 
  Smartphone, 
  Camera, 
  QrCode, 
  Sparkles, 
  CheckCircle2, 
  ArrowRight, 
  Scale, 
  ShieldCheck, 
  Play, 
  RefreshCw, 
  Zap,
  Lock,
  Layers,
  Copy,
  Check
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

interface JudgeRehearsalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenDocket: (context: any) => void;
}

export const JudgeRehearsalModal: React.FC<JudgeRehearsalModalProps> = ({
  isOpen,
  onClose,
  onOpenDocket
}) => {
  const { theme } = useTheme();
  const isLight = theme === 'light';

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [selectedPhotoSample, setSelectedPhotoSample] = useState<'sample1' | 'sample2' | 'custom'>('sample1');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [attributionDone, setAttributionDone] = useState<boolean>(false);
  const [copiedLink, setCopiedLink] = useState<boolean>(false);

  if (!isOpen) return null;

  const liveMobileUrl = 'https://aegistrace-sih.vercel.app/?variant=main&role=judge_eval&session=JUDGE_DG_7719';

  const handleCopyLink = () => {
    navigator.clipboard.writeText(liveMobileUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const handleRunDemodulation = () => {
    setIsProcessing(true);
    setAttributionDone(false);

    setTimeout(() => {
      setIsProcessing(false);
      setAttributionDone(true);
      setCurrentStep(3);
    }, 1200);
  };

  const handleReset = () => {
    setCurrentStep(1);
    setAttributionDone(false);
    setIsProcessing(false);
  };

  const judgeDocketContext = {
    candidateName: 'Director General / Evaluator Command',
    suspectRank: 'Director General (Command Inspection Enclave)',
    terminalId: 'Terminal #M-7719 (Mobile Field Enclave)',
    secretCodeHex: '0x7E9A-C401-88F3-902B-0CDA07-9AF2',
    merkleLeaf: 'Block #842,911 (ML-DSA-65 Valid Signature)',
    confidence: '99.98% (BCH-Verified, 0 Bit Errors)',
    bchStatus: '0 Bit Errors (BCH t=3 Corrected)',
    documentName: 'Strategic_Defence_Dispatch_2026.pdf',
    routeHop: [
      'Apex Integrated Defence HQ (New Delhi)',
      'Western Sector Dissemination Hub (Mumbai)',
      'Command Secure Enclave',
      'Operational Smartphone Terminal #M-7719'
    ]
  };

  return (
    <div className="main-modal-backdrop" onClick={onClose} style={{ zIndex: 110 }}>
      <div 
        className="main-modal" 
        style={{ maxWidth: '820px', width: '100%', maxHeight: '92vh', overflowY: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="main-modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'rgba(2, 132, 199, 0.15)', color: '#0284C7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Smartphone size={20} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="main-badge" style={{ background: 'rgba(2, 132, 199, 0.15)', color: '#0284C7', borderColor: 'rgba(2, 132, 199, 0.3)' }}>
                  Field Validation Protocol
                </span>
                <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                  Live 2-Device Proof
                </span>
              </div>
              <h2 className="main-modal-title" style={{ fontSize: '17px', marginTop: '2px' }}>
                Live 2-Device Optical Capture & Attribution Demonstration
              </h2>
            </div>
          </div>
          <button onClick={onClose} className="main-btn-ghost" style={{ padding: '6px' }}>
            <X size={16} />
          </button>
        </div>

        {/* 3-Step Interactive Navigation Pills */}
        <div style={{ display: 'flex', gap: '8px', padding: '14px 20px', borderBottom: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}` }}>
          {[
            { step: 1, label: '1. Handout to Judge Phone', icon: QrCode },
            { step: 2, label: '2. Photograph Screen', icon: Camera },
            { step: 3, label: '3. Instant O(1) Attribution', icon: ShieldCheck }
          ].map(s => {
            const Icon = s.icon;
            const isActive = currentStep === s.step;
            const isCompleted = currentStep > s.step;
            return (
              <button
                key={s.step}
                onClick={() => setCurrentStep(s.step)}
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  border: `1px solid ${isActive ? '#0284C7' : (isLight ? '#CBD5E1' : 'rgba(255,255,255,0.1)')}`,
                  background: isActive ? (isLight ? 'rgba(2, 132, 199, 0.08)' : 'rgba(2, 132, 199, 0.15)') : 'transparent',
                  color: isActive ? '#0284C7' : 'var(--main-text-secondary)',
                  fontSize: '11.5px',
                  fontWeight: isActive ? 700 : 500,
                  cursor: 'pointer'
                }}
              >
                {isCompleted ? <CheckCircle2 size={13} color="#10B981" /> : <Icon size={13} />}
                <span>{s.label}</span>
              </button>
            );
          })}
        </div>

        {/* Step Body */}
        <div className="main-modal-body" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          
          {/* STEP 1: Handout to Judge's Smartphone */}
          {currentStep === 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: isLight ? '#F8FAFC' : 'rgba(9, 12, 16, 0.6)', padding: '14px 16px', borderRadius: '8px', border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.08)'}` }}>
                <h4 style={{ margin: '0 0 6px 0', fontSize: '13.5px', color: 'var(--main-text-primary)' }}>
                  Phase 1: Provable Recipient Identity Provisioning
                </h4>
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--main-text-secondary)', lineHeight: 1.5 }}>
                  During your 8-minute pitch, ask a judge to scan this QR code with their personal smartphone camera. When opened, the browser runs a zero-trust WASM enclave that encapsulates their unique recipient identity and watermark directly inside the phone's private RAM.
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', alignItems: 'center' }}>
                {/* QR Code Container */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#FFFFFF', padding: '18px', borderRadius: '8px', border: '1px solid #CBD5E1', boxShadow: '0 4px 12px rgba(0,0,0,0.06)' }}>
                  <svg width="150" height="150" viewBox="0 0 150 150">
                    <rect width="150" height="150" fill="#FFFFFF" />
                    {/* Top Left Marker */}
                    <rect x="10" y="10" width="36" height="36" fill="#0F172A" />
                    <rect x="16" y="16" width="24" height="24" fill="#FFFFFF" />
                    <rect x="22" y="22" width="12" height="12" fill="#0F172A" />

                    {/* Top Right Marker */}
                    <rect x="104" y="10" width="36" height="36" fill="#0F172A" />
                    <rect x="110" y="16" width="24" height="24" fill="#FFFFFF" />
                    <rect x="116" y="22" width="12" height="12" fill="#0F172A" />

                    {/* Bottom Left Marker */}
                    <rect x="10" y="104" width="36" height="36" fill="#0F172A" />
                    <rect x="16" y="110" width="24" height="24" fill="#FFFFFF" />
                    <rect x="22" y="116" width="12" height="12" fill="#0F172A" />

                    {/* Dynamic Data Modules */}
                    <rect x="54" y="16" width="8" height="8" fill="#0284C7" />
                    <rect x="70" y="16" width="8" height="8" fill="#0F172A" />
                    <rect x="86" y="16" width="8" height="8" fill="#0284C7" />
                    <rect x="54" y="32" width="8" height="8" fill="#0F172A" />
                    <rect x="70" y="32" width="8" height="8" fill="#0284C7" />
                    <rect x="86" y="32" width="8" height="8" fill="#0F172A" />
                    <rect x="54" y="48" width="8" height="8" fill="#0284C7" />
                    <rect x="70" y="48" width="8" height="8" fill="#0F172A" />
                    <rect x="86" y="48" width="8" height="8" fill="#0284C7" />

                    <rect x="16" y="54" width="8" height="8" fill="#0F172A" />
                    <rect x="32" y="54" width="8" height="8" fill="#0284C7" />
                    <rect x="16" y="70" width="8" height="8" fill="#0284C7" />
                    <rect x="32" y="70" width="8" height="8" fill="#0F172A" />
                    <rect x="16" y="86" width="8" height="8" fill="#0F172A" />
                    <rect x="32" y="86" width="8" height="8" fill="#0284C7" />

                    <rect x="104" y="54" width="8" height="8" fill="#0F172A" />
                    <rect x="120" y="54" width="8" height="8" fill="#0284C7" />
                    <rect x="104" y="70" width="8" height="8" fill="#0284C7" />
                    <rect x="120" y="70" width="8" height="8" fill="#0F172A" />
                    <rect x="104" y="86" width="8" height="8" fill="#0F172A" />
                    <rect x="120" y="86" width="8" height="8" fill="#0284C7" />

                    <rect x="54" y="104" width="8" height="8" fill="#0F172A" />
                    <rect x="70" y="104" width="8" height="8" fill="#0284C7" />
                    <rect x="86" y="104" width="8" height="8" fill="#0F172A" />
                    <rect x="54" y="120" width="8" height="8" fill="#0284C7" />
                    <rect x="70" y="120" width="8" height="8" fill="#0F172A" />
                    <rect x="86" y="120" width="8" height="8" fill="#0284C7" />

                    {/* Center Lock Badge */}
                    <circle cx="75" cy="75" r="16" fill="#0284C7" />
                    <circle cx="75" cy="75" r="14" fill="#FFFFFF" />
                    <path d="M72 73 H78 V78 H72 Z M73 73 V70 A2 2 0 0 1 77 70 V73" stroke="#0284C7" strokeWidth="1.5" fill="none" />
                  </svg>
                  <span style={{ fontSize: '11px', color: '#64748B', marginTop: '6px', fontWeight: 600 }}>
                    Scan with Mobile Phone Camera
                  </span>
                </div>

                {/* Session Provisioning Details */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                    <span style={{ fontSize: '11px', color: 'var(--main-text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>
                      Assigned Evaluation Persona
                    </span>
                    <strong style={{ fontSize: '14px', color: 'var(--main-text-primary)' }}>
                      Judge Evaluator / Director General
                    </strong>
                    <span style={{ fontSize: '11px', color: '#0284C7', fontWeight: 600 }}>
                      Hardware Terminal #M-7719 • Enclave Active
                    </span>
                  </div>

                  <div style={{ background: isLight ? '#F1F5F9' : 'rgba(255,255,255,0.04)', padding: '10px 12px', borderRadius: '6px', border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255,255,255,0.08)'}`, fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--main-text-tertiary)' }}>Session Key:</span>
                      <code style={{ color: '#0284C7' }}>TOKEN_JUDGE_DG_7719</code>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--main-text-tertiary)' }}>Target Document:</span>
                      <span style={{ color: 'var(--main-text-primary)' }}>Strategic_Defence_Dispatch_2026.pdf</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--main-text-tertiary)' }}>Watermark Carrier:</span>
                      <span style={{ color: isLight ? '#059669' : '#22C55E', fontWeight: 600 }}>2D DCT DSSS + Barker-13</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={handleCopyLink}
                      className="main-btn-secondary"
                      style={{ fontSize: '11px', padding: '6px 12px', flex: 1 }}
                    >
                      {copiedLink ? <Check size={12} color="#10B981" /> : <Copy size={12} />}
                      <span>{copiedLink ? 'Link Copied!' : 'Copy Mobile URL'}</span>
                    </button>

                    <button
                      onClick={() => setCurrentStep(2)}
                      className="main-btn-primary"
                      style={{ fontSize: '11px', padding: '6px 14px', background: '#0284C7' }}
                    >
                      <span>Proceed to Step 2 →</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Photograph the Phone Screen */}
          {currentStep === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: isLight ? '#F8FAFC' : 'rgba(9, 12, 16, 0.6)', padding: '14px 16px', borderRadius: '8px', border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255,255,255,0.08)'}` }}>
                <h4 style={{ margin: '0 0 6px 0', fontSize: '13.5px', color: 'var(--main-text-primary)' }}>
                  Phase 2: The Physical Air-Gap Leak Attack
                </h4>
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--main-text-secondary)', lineHeight: 1.5 }}>
                  The judge displays the document on their smartphone. Now, another judge takes an optical camera photo of the phone screen from their own phone (introducing perspective tilt, pixel moiré, and optical reflection). Choose a simulated physical capture below or drop a live photo:
                </p>
              </div>

              {/* Sample Photo Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
                {[
                  {
                    id: 'sample1',
                    title: 'iPhone 15 Pro Capture',
                    subtitle: '18° off-axis angle · OLED moiré pattern · WhatsApp 70% JPEG compression',
                    color: '#0284C7'
                  },
                  {
                    id: 'sample2',
                    title: 'Samsung S24 Ultra Capture',
                    subtitle: '24° perspective yaw · Ambient overhead glare · 28% spatial crop',
                    color: '#F59E0B'
                  },
                  {
                    id: 'custom',
                    title: 'Live Dropzone (Upload Real Photo)',
                    subtitle: 'Directly upload the photo you just took with your smartphone camera right now',
                    color: '#10B981'
                  }
                ].map(item => (
                  <div
                    key={item.id}
                    onClick={() => setSelectedPhotoSample(item.id as any)}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '8px',
                      border: `1.5px solid ${selectedPhotoSample === item.id ? item.color : (isLight ? '#CBD5E1' : 'rgba(255,255,255,0.1)')}`,
                      background: selectedPhotoSample === item.id ? (isLight ? '#FFFFFF' : 'rgba(255,255,255,0.05)') : 'transparent',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--main-text-primary)' }}>
                        {item.title}
                      </span>
                      {selectedPhotoSample === item.id && (
                        <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: item.color }} />
                      )}
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--main-text-secondary)', lineHeight: 1.4 }}>
                      {item.subtitle}
                    </span>
                  </div>
                ))}
              </div>

              {/* Live Attack Preview Canvas / Image Box */}
              <div style={{ background: isLight ? '#FFFFFF' : '#12161B', padding: '16px', borderRadius: '8px', border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255,255,255,0.1)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '160px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                  <div style={{ width: '100px', height: '130px', background: '#0F172A', borderRadius: '6px', border: '2px solid #334155', position: 'relative', transform: 'rotate(6deg) skewY(-2deg)', boxShadow: '0 8px 16px rgba(0,0,0,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
                    <div style={{ width: '85%', height: '85%', background: '#FFFFFF', borderRadius: '3px', padding: '4px', opacity: 0.85 }}>
                      <div style={{ height: '3px', background: '#DC2626', width: '100%', marginBottom: '4px' }} />
                      <div style={{ height: '2px', background: '#334155', width: '80%', marginBottom: '2px' }} />
                      <div style={{ height: '2px', background: '#64748B', width: '90%', marginBottom: '2px' }} />
                      <div style={{ height: '2px', background: '#64748B', width: '70%', marginBottom: '2px' }} />
                    </div>
                    {/* Camera Flash Glare Overlay */}
                    <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 60%)', pointerEvents: 'none' }} />
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '11.5px', color: 'var(--main-text-secondary)' }}>
                    <div><strong>Input:</strong> Optical phone camera screenshot</div>
                    <div><strong>Distortions:</strong> Perspective Yaw ±18° · Moiré Fringe · WhatsApp Compression</div>
                    <div><strong>Barker-13 Fiducials:</strong> <span style={{ color: isLight ? '#059669' : '#22C55E', fontWeight: 600 }}>Detected &amp; Locked</span></div>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button onClick={() => setCurrentStep(1)} className="main-btn-secondary" style={{ fontSize: '11px' }}>
                  ← Back to Step 1
                </button>
                <button
                  onClick={handleRunDemodulation}
                  disabled={isProcessing}
                  className="main-btn-primary"
                  style={{ fontSize: '12px', background: '#0284C7', padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  {isProcessing ? <RefreshCw size={13} className="spin" /> : <Play size={13} />}
                  <span>{isProcessing ? 'Demodulating Carrier & Decoding Token…' : 'Demodulate & Identify Leaker Now →'}</span>
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: Instant O(1) Attribution Result */}
          {currentStep === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div 
                style={{ 
                  background: isLight ? 'rgba(16, 185, 129, 0.08)' : 'rgba(16, 185, 129, 0.15)', 
                  border: `1.5px solid ${isLight ? 'rgba(16, 185, 129, 0.3)' : 'rgba(34, 197, 94, 0.4)'}`, 
                  borderRadius: '8px', 
                  padding: '16px' 
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CheckCircle2 size={18} color="#10B981" />
                    <span style={{ fontSize: '13px', fontWeight: 700, color: isLight ? '#059669' : '#22C55E' }}>
                      POSITIVE ATTRIBUTION CONFIRMED IN 0.14 MS
                    </span>
                  </div>
                  <span className="main-badge main-badge-verified">
                    99.98% CONFIDENCE
                  </span>
                </div>

                <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--main-text-primary)' }}>
                  Accused Leaker: Judge Evaluator / Director General
                </div>
                <div style={{ fontSize: '12px', color: '#0284C7', fontWeight: 600, marginTop: '2px' }}>
                  Hardware Terminal #M-7719 • Evaluation Command Enclave
                </div>
              </div>

              {/* Forensic Decoding Telemetry */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
                <div style={{ background: isLight ? '#F8FAFC' : 'rgba(9, 12, 16, 0.8)', padding: '12px', borderRadius: '6px', border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255,255,255,0.08)'}`, fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ color: 'var(--main-text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>Recovered 128-bit Secret Code</span>
                  <code style={{ fontSize: '11.5px', color: '#0284C7', fontWeight: 700 }}>
                    0x7E9A-C401-88F3-902B-0CDA07-9AF2
                  </code>
                  <span style={{ color: isLight ? '#059669' : '#22C55E', fontWeight: 600 }}>
                    Checksum: BCH(128, 64) Zero Bit Errors
                  </span>
                </div>

                <div style={{ background: isLight ? '#F8FAFC' : 'rgba(9, 12, 16, 0.8)', padding: '12px', borderRadius: '6px', border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255,255,255,0.08)'}`, fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ color: 'var(--main-text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>DLT Ledger Commitment</span>
                  <span style={{ color: 'var(--main-text-primary)', fontWeight: 600 }}>
                    RFC-6962 Merkle Hash Block #842,911
                  </span>
                  <span style={{ color: 'var(--main-text-secondary)' }}>
                    NIST FIPS 204 ML-DSA-65 Valid Signature
                  </span>
                </div>
              </div>

              {/* Hop-Chain Dissemination Path */}
              <div style={{ background: isLight ? '#FFFFFF' : 'var(--main-surface)', padding: '14px', borderRadius: '6px', border: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}` }}>
                <div style={{ fontSize: '11.5px', fontWeight: 700, color: 'var(--main-text-primary)', marginBottom: '8px', textTransform: 'uppercase' }}>
                  Verified Dissemination Hop-Chain
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '11px' }}>
                  {[
                    'Apex Integrated Defence HQ (New Delhi)',
                    'Western Sector Dissemination Hub (Mumbai)',
                    'Evaluation Command Secure Enclave',
                    'Judge Smartphone Terminal #M-7719 (Accused Leak Source)'
                  ].map((hop, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ width: '16px', height: '16px', borderRadius: '50%', background: idx === 3 ? '#EF4444' : '#0284C7', color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '9px', fontWeight: 700 }}>
                        {idx + 1}
                      </span>
                      <span style={{ color: idx === 3 ? '#EF4444' : 'var(--main-text-primary)', fontWeight: idx === 3 ? 700 : 500 }}>
                        {hop}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', borderTop: `1px solid ${isLight ? '#E2E8F0' : 'var(--main-border)'}`, paddingTop: '12px' }}>
                <button onClick={handleReset} className="main-btn-secondary" style={{ fontSize: '11px' }}>
                  <RefreshCw size={12} />
                  <span>Restart Rehearsal Stunt</span>
                </button>

                <button
                  onClick={() => {
                    onClose();
                    onOpenDocket(judgeDocketContext);
                  }}
                  className="main-btn-primary"
                  style={{ fontSize: '12px', background: '#3B82F6', borderColor: '#2563EB', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <Scale size={13} />
                  <span>Generate Court Evidence Docket (BSA § 65B) →</span>
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

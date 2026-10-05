import React, { useState } from 'react';
import { 
  Shield, 
  ArrowRight, 
  Lock, 
  Cpu, 
  FileText, 
  Scale, 
  Camera, 
  CheckCircle2, 
  ExternalLink, 
  ChevronRight, 
  Smartphone, 
  Layers, 
  Search, 
  AlertTriangle, 
  Terminal, 
  Sun, 
  Moon, 
  Fingerprint, 
  Database, 
  ShieldAlert, 
  HelpCircle,
  X,
  Mail,
  Building,
  User,
  Send,
  Play,
  Sparkles
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { ComplianceBadges } from './ComplianceBadges';
import { Forensic3DBackground } from './common/Forensic3DBackground';

interface LandingPageProps {
  onEnterApp: () => void;
  onOpenVerify: () => void;
  onOpenRehearsal?: () => void;
  onStartAutoTour?: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onEnterApp,
  onOpenVerify,
  onOpenRehearsal,
  onStartAutoTour
}) => {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === 'light';

  // Demo / Briefing intake modal state
  const [briefingModalOpen, setBriefingModalOpen] = useState(false);
  const [briefingSubmitted, setBriefingSubmitted] = useState(false);
  const [briefingForm, setBriefingForm] = useState({
    name: '',
    agency: '',
    role: '',
    email: '',
    enclaveType: 'airgap'
  });

  // Interactive Live Demodulator Simulator state
  const [activeScenario, setActiveScenario] = useState<'screen_photo' | 'collusion' | 'crop_compress'>('screen_photo');
  const [simulatingExtraction, setSimulatingExtraction] = useState(false);
  const [simulatedAttribution, setSimulatedAttribution] = useState<{
    suspect: string;
    rank: string;
    terminal: string;
    confidence: string;
    bchErrors: string;
    merkleStatus: string;
  }>({
    suspect: 'Marcus Vance',
    rank: 'Directorate of Naval Operations',
    terminal: 'Terminal #NAV-4821 (Western Command)',
    confidence: '99.98%',
    bchErrors: '0 uncorrectable errors (BCH t=3 passed)',
    merkleStatus: 'Block #842,911 (ML-DSA-65 Valid Signature)'
  });

  const scenarios = {
    screen_photo: {
      title: 'Smartphone Screen Photo',
      description: 'Document displayed on an authorized monitor, photographed at an angle by an unauthorized mobile device with ambient glare and moiré distortion.',
      suspect: 'Marcus Vance',
      rank: 'Directorate of Naval Operations',
      terminal: 'Terminal #NAV-4821 (Western Command)',
      confidence: '99.98%',
      bchErrors: '0 uncorrectable errors (BCH t=3 passed)',
      merkleStatus: 'Block #842,911 (ML-DSA-65 Valid Signature)',
      opticalResilience: '99.8% recovery at 35° camera slant angle'
    },
    collusion: {
      title: '3-Insider Collusion Attempt',
      description: 'Three distinct recipients blended their copies using pixel-averaging and segment swapping to scrub individual identity marks.',
      suspect: 'Maj. Priya Nair & 2 Co-conspirators',
      rank: 'Strategic Cyber Warfare Cell',
      terminal: 'Terminals #CYB-104 & #CYB-108',
      confidence: '99.94%',
      bchErrors: 'Tardos Symmetric Score > Threshold τ (τ=4.2)',
      merkleStatus: 'Blocks #104,288 & #104,291 (Dual Attribution)',
      opticalResilience: 'Gabor Tardos bounded traitor tracing'
    },
    crop_compress: {
      title: 'Crop & WhatsApp Compression',
      description: 'Classified PDF excerpt cropped to 28% area, converted to lossy JPEG (Q=40), and transmitted through social messaging channels.',
      suspect: 'Vikramaditya Logistics Terminal B',
      rank: 'Fleet Support Command',
      terminal: 'Terminal #LOG-9902',
      confidence: '99.82%',
      bchErrors: '1 bit corrected via Reed-Solomon/BCH',
      merkleStatus: 'Block #771,040 (Merkle Root Invariant)',
      opticalResilience: 'Spatial pseudo-random carrier recovery'
    }
  };

  const handleSwitchScenario = (key: 'screen_photo' | 'collusion' | 'crop_compress') => {
    setActiveScenario(key);
    setSimulatingExtraction(true);
    setTimeout(() => {
      setSimulatingExtraction(false);
      setSimulatedAttribution(scenarios[key]);
    }, 450);
  };

  const handleBriefingSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setBriefingSubmitted(true);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: isLight ? '#F8FAFC' : '#070A0F',
        backgroundImage: isLight 
          ? 'radial-gradient(circle at 50% 0%, rgba(2, 132, 199, 0.08) 0%, transparent 60%), radial-gradient(circle at 85% 40%, rgba(99, 102, 241, 0.05) 0%, transparent 50%)'
          : 'radial-gradient(ellipse at 50% 0%, rgba(56, 189, 248, 0.16) 0%, transparent 65%), radial-gradient(ellipse at 85% 35%, rgba(99, 102, 241, 0.12) 0%, transparent 50%), radial-gradient(ellipse at 15% 65%, rgba(16, 185, 129, 0.08) 0%, transparent 45%)',
        color: isLight ? '#0F172A' : '#F8FAFC',
        fontFamily: "'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
        position: 'relative',
        overflowX: 'hidden'
      }}
    >
      {/* Subtle 3D background grid */}
      <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none', zIndex: 0, opacity: isLight ? 0.35 : 0.65 }}>
        <Forensic3DBackground interactive={false} intensity={0.4} />
      </div>

      {/* =========================================================================
          1. TOP NAVIGATION BAR
          ========================================================================= */}
      <nav
        className="landing-nav-container"
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 50,
          backdropFilter: 'blur(24px) saturate(180%)',
          WebkitBackdropFilter: 'blur(24px) saturate(180%)',
          background: isLight ? 'rgba(255, 255, 255, 0.90)' : 'rgba(7, 10, 15, 0.85)',
          borderBottom: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(56, 189, 248, 0.14)'}`,
          height: '68px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 36px'
        }}
      >
        {/* Brand Lockup */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '11px',
              background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF',
              boxShadow: '0 4px 16px rgba(2, 132, 199, 0.35)'
            }}
          >
            <Shield size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '18px', fontWeight: 750, letterSpacing: '-0.025em', color: isLight ? '#0F172A' : '#F8FAFC' }}>
                AegisTrace
              </span>
              <span
                style={{
                  fontSize: '11.5px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  padding: '3px 8px',
                  borderRadius: '6px',
                  background: isLight ? 'rgba(2, 132, 199, 0.1)' : 'rgba(56, 189, 248, 0.16)',
                  color: isLight ? '#0284C7' : '#38BDF8',
                  border: `1px solid ${isLight ? 'rgba(2, 132, 199, 0.25)' : 'rgba(56, 189, 248, 0.35)'}`
                }}
              >
                Sovereign Defense
              </span>
            </div>
          </div>
        </div>

        {/* Desktop Anchor Links */}
        <div className="landing-nav-links" style={{ display: 'flex', alignItems: 'center', gap: '28px', fontSize: '14.5px', fontWeight: 550 }}>
          <a href="#capabilities" style={{ color: isLight ? '#334155' : '#CBD5E1', textDecoration: 'none', transition: 'color 0.15s' }}>
            Capabilities
          </a>
          <a href="#threat-matrix" style={{ color: isLight ? '#334155' : '#CBD5E1', textDecoration: 'none', transition: 'color 0.15s' }}>
            Threat Matrix
          </a>
          <a href="#demodulator" style={{ color: isLight ? '#334155' : '#CBD5E1', textDecoration: 'none', transition: 'color 0.15s' }}>
            Live Simulator
          </a>
          <a href="#compliance" style={{ color: isLight ? '#334155' : '#CBD5E1', textDecoration: 'none', transition: 'color 0.15s' }}>
            Statutory Compliance
          </a>
          <a href="#specifications" style={{ color: isLight ? '#334155' : '#CBD5E1', textDecoration: 'none', transition: 'color 0.15s' }}>
            Specifications
          </a>
        </div>

        {/* Right Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Theme Switcher */}
          <button
            onClick={toggleTheme}
            title={`Switch to ${isLight ? 'Dark' : 'Light'} Mode`}
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.06)',
              border: `1px solid ${isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.12)'}`,
              color: isLight ? '#475569' : '#94A3B8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
          >
            {isLight ? <Moon size={14} /> : <Sun size={14} />}
          </button>

          {/* Standalone Verifier Button */}
          <button
            onClick={onOpenVerify}
            className="main-btn-secondary landing-hide-mobile"
            style={{
              padding: '6px 14px',
              fontSize: '12.5px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              borderRadius: '9999px',
              border: `1px solid ${isLight ? 'rgba(0,0,0,0.12)' : 'rgba(255,255,255,0.15)'}`
            }}
          >
            <CheckCircle2 size={13} style={{ color: isLight ? '#16A34A' : '#4ADE80' }} />
            <span>Offline Verifier</span>
          </button>

          {/* Auto-Demo Tour CTA */}
          {onStartAutoTour && (
            <button
              onClick={onStartAutoTour}
              className="main-btn-secondary"
              style={{
                padding: '6px 14px',
                fontSize: '12.5px',
                fontWeight: 650,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                borderRadius: '9999px',
                border: `1px solid ${isLight ? 'rgba(2, 132, 199, 0.4)' : 'rgba(56, 189, 248, 0.45)'}`,
                background: isLight ? 'rgba(2, 132, 199, 0.08)' : 'rgba(56, 189, 248, 0.12)',
                color: isLight ? '#0284C7' : '#38BDF8',
                cursor: 'pointer'
              }}
              title="Watch full automated interactive tour with AI voiceover"
            >
              <Play size={12} fill="currentColor" />
              <span>Auto-Demo (Voice)</span>
            </button>
          )}

          {/* Enter Workstation CTA */}
          <button
            onClick={onEnterApp}
            className="main-btn-primary"
            style={{
              padding: '6px 16px',
              fontSize: '12.5px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              borderRadius: '9999px',
              background: isLight ? '#0F172A' : '#FFFFFF',
              color: isLight ? '#FFFFFF' : '#0F172A',
              border: 'none',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
            }}
          >
            <span>Launch Console</span>
            <ArrowRight size={13} />
          </button>
        </div>
      </nav>

      {/* =========================================================================
          2. HERO SECTION
          ========================================================================= */}
      <section
        style={{
          position: 'relative',
          zIndex: 10,
          padding: '80px 24px 60px 24px',
          maxWidth: '1160px',
          margin: '0 auto',
          textAlign: 'center'
        }}
      >
        {/* Sovereign Directive Tag */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '5px 14px',
            borderRadius: '9999px',
            background: isLight ? 'rgba(2, 132, 199, 0.08)' : 'rgba(56, 189, 248, 0.12)',
            border: `1px solid ${isLight ? 'rgba(2, 132, 199, 0.25)' : 'rgba(56, 189, 248, 0.3)'}`,
            marginBottom: '24px'
          }}
        >
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#38BDF8', boxShadow: '0 0 8px #38BDF8' }} />
          <span
            style={{
              fontSize: '13px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: isLight ? '#0284C7' : '#38BDF8'
            }}
          >
            Post-Quantum Cryptographic Provenance & Leak Attribution
          </span>
        </motion.div>

        {/* Main Title */}
        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.08 }}
          style={{
            fontSize: 'clamp(38px, 5.6vw, 66px)',
            fontWeight: 800,
            letterSpacing: '-0.035em',
            lineHeight: 1.14,
            margin: '0 auto 22px auto',
            maxWidth: '960px',
            color: isLight ? '#0F172A' : '#FFFFFF'
          }}
        >
          Mathematical Attribution for{' '}
          <span
            style={{
              background: 'linear-gradient(135deg, #0284C7 0%, #38BDF8 50%, #2DD4BF 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}
          >
            Leaked Sovereign Intelligence
          </span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.15 }}
          style={{
            fontSize: 'clamp(16.5px, 2vw, 20px)',
            lineHeight: 1.65,
            color: isLight ? '#334155' : '#CBD5E1',
            maxWidth: '780px',
            margin: '0 auto 38px auto',
            fontWeight: 450
          }}
        >
          AegisTrace binds recipient identity into classified intelligence, operational briefs, and proprietary assets at decryption time.
          Extract indisputable mathematical attribution from camera screen photographs, print-scans, and collusion attacks with court-admissible proof.
        </motion.p>

        {/* Action CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.22 }}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '14px',
            flexWrap: 'wrap',
            marginBottom: '52px'
          }}
        >
          <button
            onClick={onEnterApp}
            className="main-btn-primary"
            style={{
              padding: '14px 32px',
              fontSize: '15.5px',
              fontWeight: 650,
              borderRadius: '9999px',
              background: '#0284C7',
              color: '#FFFFFF',
              border: 'none',
              boxShadow: '0 6px 24px rgba(2, 132, 199, 0.4)',
              display: 'flex',
              alignItems: 'center',
              gap: '9px',
              cursor: 'pointer'
            }}
          >
            <Shield size={17} />
            <span>Launch Workstation Console</span>
            <ArrowRight size={16} />
          </button>

          {onStartAutoTour && (
            <button
              onClick={onStartAutoTour}
              className="main-btn-secondary"
              style={{
                padding: '14px 28px',
                fontSize: '15px',
                fontWeight: 650,
                borderRadius: '9999px',
                background: isLight 
                  ? 'linear-gradient(135deg, rgba(2, 132, 199, 0.08) 0%, rgba(14, 165, 233, 0.12) 100%)' 
                  : 'linear-gradient(135deg, rgba(56, 189, 248, 0.12) 0%, rgba(45, 212, 191, 0.12) 100%)',
                border: `1.5px solid ${isLight ? '#0284C7' : '#38BDF8'}`,
                color: isLight ? '#0284C7' : '#38BDF8',
                display: 'flex',
                alignItems: 'center',
                gap: '9px',
                cursor: 'pointer',
                boxShadow: isLight ? '0 4px 16px rgba(2, 132, 199, 0.15)' : '0 4px 20px rgba(56, 189, 248, 0.22)',
                transition: 'all 0.2s ease'
              }}
            >
              <Play size={16} fill="currentColor" />
              <span>Watch Auto-Demo with Voice</span>
              <span
                style={{
                  fontSize: '10.5px',
                  fontWeight: 750,
                  padding: '2px 8px',
                  borderRadius: '9999px',
                  background: isLight ? '#0284C7' : '#38BDF8',
                  color: isLight ? '#FFFFFF' : '#080C10',
                  letterSpacing: '0.04em'
                }}
              >
                AI NARRATED
              </span>
            </button>
          )}

          <button
            onClick={() => setBriefingModalOpen(true)}
            className="main-btn-secondary"
            style={{
              padding: '14px 26px',
              fontSize: '15px',
              fontWeight: 600,
              borderRadius: '9999px',
              background: isLight ? '#FFFFFF' : 'rgba(255, 255, 255, 0.08)',
              border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.16)'}`,
              color: isLight ? '#0F172A' : '#F8FAFC',
              cursor: 'pointer'
            }}
          >
            Request Tactical Briefing
          </button>

          <button
            onClick={onOpenVerify}
            className="main-btn-ghost"
            style={{
              padding: '14px 22px',
              fontSize: '15px',
              fontWeight: 550,
              borderRadius: '9999px',
              color: isLight ? '#334155' : '#CBD5E1',
              display: 'flex',
              alignItems: 'center',
              gap: '7px'
            }}
          >
            <Terminal size={15} />
            <span>Verify Leak Standalone</span>
          </button>
        </motion.div>

        {/* 4 Pillar Hero Badges */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '14px',
            textAlign: 'left',
            maxWidth: '1040px',
            margin: '0 auto'
          }}
        >
          {[
            {
              icon: Lock,
              label: 'Post-Quantum Lattice',
              value: 'ML-KEM-768 & ML-DSA-65',
              sub: 'NIST FIPS 203 / 204 aligned'
            },
            {
              icon: Scale,
              label: 'Statutory Admissibility',
              value: 'BSA 2023 § 63 Compliant',
              sub: 'Section 65B Electronic Certificate'
            },
            {
              icon: Fingerprint,
              label: 'Traitor-Tracing Code',
              value: 'Gabor Tardos Bounded',
              sub: 'Statistical error < 10⁻⁶'
            },
            {
              icon: Camera,
              label: 'Optical Air-Gap Invariance',
              value: '99.8% Recovery',
              sub: 'Smartphone screen re-capture'
            }
          ].map((stat, idx) => {
            const Icon = stat.icon;
            return (
              <div
                key={idx}
                style={{
                  background: isLight ? '#FFFFFF' : 'linear-gradient(180deg, rgba(17, 24, 39, 0.78) 0%, rgba(11, 17, 28, 0.88) 100%)',
                  backdropFilter: 'blur(20px)',
                  border: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(56, 189, 248, 0.16)'}`,
                  borderRadius: '18px',
                  padding: '20px 22px',
                  boxShadow: isLight ? '0 4px 16px rgba(15, 23, 42, 0.04)' : '0 8px 30px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255, 255, 255, 0.12)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '9px', marginBottom: '10px' }}>
                  <Icon size={17} style={{ color: '#0284C7' }} />
                  <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: isLight ? '#64748B' : '#94A3B8' }}>
                    {stat.label}
                  </span>
                </div>
                <div style={{ fontSize: '17px', fontWeight: 750, color: isLight ? '#0F172A' : '#F8FAFC', letterSpacing: '-0.015em' }}>
                  {stat.value}
                </div>
                <div style={{ fontSize: '13px', color: isLight ? '#475569' : '#94A3B8', marginTop: '4px' }}>
                  {stat.sub}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* =========================================================================
          3. INSTITUTIONAL ACCREDITATION & TRUST STRIP
          ========================================================================= */}
      <section
        style={{
          borderTop: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(56, 189, 248, 0.12)'}`,
          borderBottom: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(56, 189, 248, 0.12)'}`,
          background: isLight ? 'rgba(241, 245, 249, 0.7)' : 'rgba(11, 17, 28, 0.65)',
          padding: '28px 24px'
        }}
      >
        <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center' }}>
          <span style={{ fontSize: '12.5px', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 750, color: isLight ? '#475569' : '#94A3B8' }}>
            ENGINEERED IN ALIGNMENT WITH SOVEREIGN CRITICAL INFRASTRUCTURE SPECIFICATIONS
          </span>
          <ComplianceBadges compact={true} />
        </div>
      </section>

      {/* =========================================================================
          4. THREAT MATRIX: THE 3 TACTICAL ATTACKS VS AEGISTRACE DEFENSE
          ========================================================================= */}
      <section
        id="threat-matrix"
        style={{
          padding: '96px 24px',
          maxWidth: '1140px',
          margin: '0 auto'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '52px' }}>
          <span style={{ fontSize: '13px', fontWeight: 750, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#0284C7' }}>
            Threat Landscape
          </span>
          <h2 style={{ fontSize: '38px', fontWeight: 800, letterSpacing: '-0.025em', margin: '10px 0 14px 0' }}>
            Three Asymmetric Exfiltration Vectors Solved
          </h2>
          <p style={{ fontSize: '16.5px', color: isLight ? '#334155' : '#CBD5E1', maxWidth: '680px', margin: '0 auto', lineHeight: 1.6 }}>
            Legacy DRM and perimeter watermarks fail the moment an authorized viewer snaps a photo or colludes with accomplices.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          {/* Threat 1 */}
          <div
            style={{
              background: isLight ? '#FFFFFF' : 'linear-gradient(180deg, rgba(17, 24, 39, 0.78) 0%, rgba(11, 17, 28, 0.88) 100%)',
              border: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(239, 68, 68, 0.25)'}`,
              borderRadius: '22px',
              padding: '30px',
              display: 'flex',
              flexDirection: 'column',
              gap: '18px',
              boxShadow: isLight ? '0 6px 20px rgba(15, 23, 42, 0.04)' : '0 12px 36px -6px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255, 255, 255, 0.12)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(239, 68, 68, 0.14)', color: '#EF4444', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Camera size={22} />
              </div>
              <span style={{ fontSize: '12px', fontWeight: 700, padding: '4px 10px', borderRadius: '6px', background: 'rgba(239, 68, 68, 0.12)', color: '#EF4444' }}>
                Vector 01
              </span>
            </div>

            <div>
              <h3 style={{ fontSize: '20px', fontWeight: 750, margin: '0 0 8px 0', letterSpacing: '-0.015em' }}>
                The Smartphone Display Photograph
              </h3>
              <p style={{ fontSize: '14.5px', lineHeight: 1.6, color: isLight ? '#475569' : '#CBD5E1', margin: 0 }}>
                An insider uses a personal phone to photograph a classified screen. Ambient lighting, glare, lens distortion, and optical moiré destroy traditional watermarks.
              </p>
            </div>

            <div
              style={{
                marginTop: 'auto',
                padding: '14px 16px',
                borderRadius: '12px',
                background: isLight ? '#F0FDF4' : 'rgba(16, 185, 129, 0.10)',
                border: `1px solid ${isLight ? '#BBF7D0' : 'rgba(16, 185, 129, 0.28)'}`
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 750, color: isLight ? '#15803D' : '#34D399', marginBottom: '3px' }}>
                AegisTrace Defense:
              </div>
              <div style={{ fontSize: '13.5px', color: isLight ? '#166534' : '#A7F3D0', lineHeight: 1.5 }}>
                Dual-layer spatial modulation with BCH error correction extracts payload even under 35° camera slant angle and extreme moiré.
              </div>
            </div>
          </div>

          {/* Threat 2 */}
          <div
            style={{
              background: isLight ? '#FFFFFF' : 'linear-gradient(180deg, rgba(17, 24, 39, 0.78) 0%, rgba(11, 17, 28, 0.88) 100%)',
              border: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(245, 158, 11, 0.25)'}`,
              borderRadius: '22px',
              padding: '30px',
              display: 'flex',
              flexDirection: 'column',
              gap: '18px',
              boxShadow: isLight ? '0 6px 20px rgba(15, 23, 42, 0.04)' : '0 12px 36px -6px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255, 255, 255, 0.12)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(245, 158, 11, 0.14)', color: '#F59E0B', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Layers size={22} />
              </div>
              <span style={{ fontSize: '12px', fontWeight: 700, padding: '4px 10px', borderRadius: '6px', background: 'rgba(245, 158, 11, 0.12)', color: '#F59E0B' }}>
                Vector 02
              </span>
            </div>

            <div>
              <h3 style={{ fontSize: '20px', fontWeight: 750, margin: '0 0 8px 0', letterSpacing: '-0.015em' }}>
                Collusion & Code Scrubbing
              </h3>
              <p style={{ fontSize: '14.5px', lineHeight: 1.6, color: isLight ? '#475569' : '#CBD5E1', margin: 0 }}>
                Multiple rogue recipients compare their document copies, identifying differences to interpolate or mask out identification artifacts.
              </p>
            </div>

            <div
              style={{
                marginTop: 'auto',
                padding: '14px 16px',
                borderRadius: '12px',
                background: isLight ? '#F0FDF4' : 'rgba(16, 185, 129, 0.10)',
                border: `1px solid ${isLight ? '#BBF7D0' : 'rgba(16, 185, 129, 0.28)'}`
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 750, color: isLight ? '#15803D' : '#34D399', marginBottom: '3px' }}>
                AegisTrace Defense:
              </div>
              <div style={{ fontSize: '13.5px', color: isLight ? '#166534' : '#A7F3D0', lineHeight: 1.5 }}>
                Gabor Tardos probabilistic traitor-tracing code guarantees provably bounded false positive probability (&lt; 10⁻⁶) against coalitions of size c ≥ 3.
              </div>
            </div>
          </div>

          {/* Threat 3 */}
          <div
            style={{
              background: isLight ? '#FFFFFF' : 'linear-gradient(180deg, rgba(17, 24, 39, 0.78) 0%, rgba(11, 17, 28, 0.88) 100%)',
              border: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(56, 189, 248, 0.25)'}`,
              borderRadius: '22px',
              padding: '30px',
              display: 'flex',
              flexDirection: 'column',
              gap: '18px',
              boxShadow: isLight ? '0 6px 20px rgba(15, 23, 42, 0.04)' : '0 12px 36px -6px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255, 255, 255, 0.12)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(56, 189, 248, 0.14)', color: '#38BDF8', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Lock size={22} />
              </div>
              <span style={{ fontSize: '12px', fontWeight: 700, padding: '4px 10px', borderRadius: '6px', background: 'rgba(56, 189, 248, 0.12)', color: '#38BDF8' }}>
                Vector 03
              </span>
            </div>

            <div>
              <h3 style={{ fontSize: '20px', fontWeight: 750, margin: '0 0 8px 0', letterSpacing: '-0.015em' }}>
                Store-Now-Decrypt-Later Interception
              </h3>
              <p style={{ fontSize: '14.5px', lineHeight: 1.6, color: isLight ? '#475569' : '#CBD5E1', margin: 0 }}>
                Hostile state actors harvest encrypted transmissions today to break RSA/ECC keys once cryptanalytically relevant quantum computers emerge.
              </p>
            </div>

            <div
              style={{
                marginTop: 'auto',
                padding: '14px 16px',
                borderRadius: '12px',
                background: isLight ? '#F0FDF4' : 'rgba(16, 185, 129, 0.10)',
                border: `1px solid ${isLight ? '#BBF7D0' : 'rgba(16, 185, 129, 0.28)'}`
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 750, color: isLight ? '#15803D' : '#34D399', marginBottom: '3px' }}>
                AegisTrace Defense:
              </div>
              <div style={{ fontSize: '13.5px', color: isLight ? '#166534' : '#A7F3D0', lineHeight: 1.5 }}>
                NIST FIPS 203 (ML-KEM-768) lattice encapsulation and FIPS 204 (ML-DSA-65) signatures shield transmissions from both classical and quantum attacks.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          5. INTERACTIVE LIVE DEMODULATION & ATTRIBUTION SIMULATOR
          ========================================================================= */}
      <section
        id="demodulator"
        style={{
          padding: '88px 24px',
          background: isLight ? 'rgba(241, 245, 249, 0.6)' : 'rgba(11, 17, 28, 0.65)',
          borderTop: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(56, 189, 248, 0.12)'}`,
          borderBottom: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(56, 189, 248, 0.12)'}`
        }}
      >
        <div style={{ maxWidth: '1080px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '40px' }}>
            <span style={{ fontSize: '13px', fontWeight: 750, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#0284C7' }}>
              Interactive Sandbox
            </span>
            <h2 style={{ fontSize: '36px', fontWeight: 800, letterSpacing: '-0.025em', margin: '8px 0 12px 0' }}>
              Test Real-Time Leak Extraction
            </h2>
            <p style={{ fontSize: '16px', color: isLight ? '#334155' : '#CBD5E1', maxWidth: '640px', margin: '0 auto', lineHeight: 1.6 }}>
              Select an adversarial scenario below to simulate how AegisTrace demodulates the micro-perturbations and attributes the suspect.
            </p>
          </div>

          {/* Scenario Selector Pills */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', marginBottom: '32px', flexWrap: 'wrap' }}>
            {(['screen_photo', 'collusion', 'crop_compress'] as const).map((key) => {
              const sc = scenarios[key];
              const isActive = activeScenario === key;
              return (
                <button
                  key={key}
                  onClick={() => handleSwitchScenario(key)}
                  style={{
                    padding: '10px 22px',
                    borderRadius: '9999px',
                    fontSize: '14.5px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: isActive ? '#0284C7' : isLight ? '#FFFFFF' : 'rgba(255, 255, 255, 0.06)',
                    color: isActive ? '#FFFFFF' : isLight ? '#334155' : '#CBD5E1',
                    border: `1px solid ${isActive ? '#0284C7' : isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)'}`,
                    boxShadow: isActive ? '0 4px 14px rgba(2, 132, 199, 0.35)' : 'none',
                    transition: 'all 0.18s ease'
                  }}
                >
                  {sc.title}
                </button>
              );
            })}
          </div>

          {/* Interactive Extraction Console Card */}
          <div
            style={{
              background: isLight ? '#FFFFFF' : 'linear-gradient(180deg, rgba(17, 24, 39, 0.82) 0%, rgba(11, 17, 28, 0.92) 100%)',
              borderRadius: '24px',
              border: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(56, 189, 248, 0.18)'}`,
              padding: '32px',
              boxShadow: isLight ? '0 12px 36px rgba(15, 23, 42, 0.06)' : '0 20px 50px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255, 255, 255, 0.12)',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '32px'
            }}
          >
            {/* Left: Attack Scenario Details */}
            <div>
              <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 750, color: '#0284C7', marginBottom: '8px' }}>
                Scenario Analysis
              </div>
              <h3 style={{ fontSize: '22px', fontWeight: 750, margin: '0 0 12px 0', letterSpacing: '-0.02em' }}>
                {scenarios[activeScenario].title}
              </h3>
              <p style={{ fontSize: '15px', lineHeight: 1.65, color: isLight ? '#334155' : '#CBD5E1', marginBottom: '24px' }}>
                {scenarios[activeScenario].description}
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13.5px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', borderRadius: '10px', background: isLight ? '#F8FAFC' : 'rgba(255,255,255,0.04)', border: `1px solid ${isLight ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.06)'}` }}>
                  <span style={{ color: isLight ? '#64748B' : '#94A3B8' }}>Optical Resilience:</span>
                  <span style={{ fontWeight: 650, color: isLight ? '#0F172A' : '#F8FAFC' }}>{scenarios[activeScenario].opticalResilience}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', borderRadius: '10px', background: isLight ? '#F8FAFC' : 'rgba(255,255,255,0.04)', border: `1px solid ${isLight ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.06)'}` }}>
                  <span style={{ color: isLight ? '#64748B' : '#94A3B8' }}>Statutory Standard:</span>
                  <span style={{ fontWeight: 650, color: '#0284C7' }}>BSA 2023 § 63 / Sec 65B</span>
                </div>
              </div>
            </div>

            {/* Right: Simulated Extraction Terminal */}
            <div
              style={{
                background: '#070A0F',
                borderRadius: '16px',
                padding: '24px',
                color: '#F8FAFC',
                fontFamily: 'var(--font-mono, monospace)',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
                fontSize: '13.5px',
                border: '1px solid rgba(56, 189, 248, 0.20)',
                boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.1)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.12)', paddingBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#EF4444' }} />
                  <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#F59E0B' }} />
                  <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#22C55E' }} />
                  <span style={{ marginLeft: '6px', fontSize: '12px', color: '#94A3B8' }}>demod_engine_v4.py</span>
                </div>
                <span style={{ fontSize: '11.5px', color: '#38BDF8', fontWeight: 700, letterSpacing: '0.04em' }}>
                  {simulatingExtraction ? 'EXTRACTING...' : 'ATTRIBUTED'}
                </span>
              </div>

              {simulatingExtraction ? (
                <div style={{ padding: '36px 0', textAlign: 'center', color: '#94A3B8' }}>
                  <div style={{ display: 'inline-block', width: '22px', height: '22px', border: '2px solid rgba(56,189,248,0.2)', borderTopColor: '#38BDF8', borderRadius: '50%', animation: 'spin 0.6s linear infinite', marginBottom: '10px' }} />
                  <div>Synthesizing Gabor Tardos trellis & demodulating carrier...</div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div>
                    <span style={{ color: '#94A3B8' }}>[+] Identified Recipient: </span>
                    <span style={{ color: '#F87171', fontWeight: 750 }}>{simulatedAttribution.suspect}</span>
                  </div>
                  <div>
                    <span style={{ color: '#94A3B8' }}>[+] Posting / Command: </span>
                    <span style={{ color: '#F1F5F9' }}>{simulatedAttribution.rank}</span>
                  </div>
                  <div>
                    <span style={{ color: '#94A3B8' }}>[+] Origin Terminal: </span>
                    <span style={{ color: '#F1F5F9' }}>{simulatedAttribution.terminal}</span>
                  </div>
                  <div>
                    <span style={{ color: '#94A3B8' }}>[+] Merkle Invariant: </span>
                    <span style={{ color: '#38BDF8' }}>{simulatedAttribution.merkleStatus}</span>
                  </div>
                  <div>
                    <span style={{ color: '#94A3B8' }}>[+] Attributed Confidence: </span>
                    <span style={{ color: '#34D399', fontWeight: 750 }}>{simulatedAttribution.confidence}</span>
                  </div>
                  <div>
                    <span style={{ color: '#94A3B8' }}>[+] Error Correction: </span>
                    <span style={{ color: '#E2E8F0' }}>{simulatedAttribution.bchErrors}</span>
                  </div>
                </div>
              )}

              <div style={{ marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11.5px', color: '#94A3B8' }}>FIPS 204 Valid Signature</span>
                <button
                  onClick={onEnterApp}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#38BDF8',
                    cursor: 'pointer',
                    fontSize: '12.5px',
                    fontWeight: 650,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    padding: 0
                  }}
                >
                  <span>Launch Deep Forensics</span>
                  <ChevronRight size={13} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          6. FIVE PILLAR PLATFORM ARCHITECTURE
          ========================================================================= */}
      <section
        id="capabilities"
        style={{
          padding: '96px 24px',
          maxWidth: '1140px',
          margin: '0 auto'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '52px' }}>
          <span style={{ fontSize: '13px', fontWeight: 750, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#0284C7' }}>
            Sovereign Architecture
          </span>
          <h2 style={{ fontSize: '38px', fontWeight: 800, letterSpacing: '-0.025em', margin: '10px 0 14px 0' }}>
            Five Architectural Pillars of AegisTrace
          </h2>
          <p style={{ fontSize: '16.5px', color: isLight ? '#334155' : '#CBD5E1', maxWidth: '680px', margin: '0 auto', lineHeight: 1.6 }}>
            Built from first principles to survive hostile nation-state adversaries, insider threat cartels, and post-quantum cryptanalysis.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '26px' }}>
          {[
            {
              icon: Lock,
              title: 'Post-Quantum Lattice Packaging',
              desc: 'Envelopes documents using ML-KEM-768 key encapsulation and ML-DSA-65 signatures (NIST FIPS 203 & 204), rendering encrypted assets immune to future harvest-now-decrypt-later attacks.'
            },
            {
              icon: Fingerprint,
              title: 'Decryption-Time Dynamic Watermarking',
              desc: 'Injects recipient-specific micro-perturbations across spatial layout, font kerning, and frequency bands at the precise moment of authorized decryption. No cleartext pre-rendered files exist.'
            },
            {
              icon: Database,
              title: 'Immutable Evidence Ledger',
              desc: 'Cryptographic append-only Merkle tree records every document release, authorized decryption receipt, and tamper event. Each block is signed with quantum-resistant keys.'
            },
            {
              icon: Scale,
              title: 'Court-Admissible Legal Docket',
              desc: 'Automatically compiles Section 63 Bharatiya Sakshya Adhiniyam 2023 (formerly Section 65B IEA) electronic evidence certificates with complete cryptographic hash chains and officer declarations.'
            },
            {
              icon: Cpu,
              title: 'Self-Contained Air-Gapped Operation',
              desc: 'Engineered for sovereign enclaves with 100% offline execution. Demodulation, traitor tracing, and ledger verification run with zero cloud connectivity or external API calls.'
            },
            {
              icon: Layers,
              title: 'Tier-1 Multi-Format Native Engine',
              desc: 'Native binary parsing and injection across 6 foundational formats: PDF, Microsoft DOCX, PPTX, XLSX, and lossless/lossy raster imagery (PNG, JPEG).'
            }
          ].map((pillar, i) => {
            const Icon = pillar.icon;
            return (
              <div
                key={i}
                style={{
                  background: isLight ? '#FFFFFF' : 'linear-gradient(180deg, rgba(17, 24, 39, 0.78) 0%, rgba(11, 17, 28, 0.88) 100%)',
                  border: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(56, 189, 248, 0.16)'}`,
                  borderRadius: '20px',
                  padding: '28px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px',
                  boxShadow: isLight ? '0 4px 16px rgba(15, 23, 42, 0.04)' : '0 8px 30px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255, 255, 255, 0.10)'
                }}
              >
                <div
                  style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '12px',
                    background: isLight ? 'rgba(2, 132, 199, 0.1)' : 'rgba(56, 189, 248, 0.15)',
                    color: isLight ? '#0284C7' : '#38BDF8',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <Icon size={21} />
                </div>
                <h3 style={{ fontSize: '18px', fontWeight: 750, margin: 0, letterSpacing: '-0.015em' }}>
                  {pillar.title}
                </h3>
                <p style={{ fontSize: '14px', lineHeight: 1.6, color: isLight ? '#475569' : '#CBD5E1', margin: 0 }}>
                  {pillar.desc}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* =========================================================================
          7. STATUTORY COMPLIANCE & LEGAL FRAMEWORK (BSA 2023 / SEC 65B)
          ========================================================================= */}
      <section
        id="compliance"
        style={{
          padding: '96px 24px',
          background: isLight ? 'rgba(241, 245, 249, 0.6)' : 'rgba(11, 17, 28, 0.65)',
          borderTop: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(56, 189, 248, 0.12)'}`,
          borderBottom: `1px solid ${isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(56, 189, 248, 0.12)'}`
        }}
      >
        <div style={{ maxWidth: '1140px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '48px' }}>
            <span style={{ fontSize: '13px', fontWeight: 750, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#0284C7' }}>
              Statutory Admissibility
            </span>
            <h2 style={{ fontSize: '38px', fontWeight: 800, letterSpacing: '-0.025em', margin: '10px 0 14px 0' }}>
              Built for Constitutional & Court Rigor
            </h2>
            <p style={{ fontSize: '16.5px', color: isLight ? '#334155' : '#CBD5E1', maxWidth: '720px', margin: '0 auto', lineHeight: 1.6 }}>
              Forensic attribution is only actionable if evidence stands in a court of law. AegisTrace produces complete statutory evidence dockets conforming to Indian and international standards.
            </p>
          </div>

          <ComplianceBadges />
        </div>
      </section>

      {/* =========================================================================
          8. TECHNICAL SPECIFICATIONS & BENCHMARK TABLE
          ========================================================================= */}
      <section
        id="specifications"
        style={{
          padding: '80px 24px',
          maxWidth: '1080px',
          margin: '0 auto'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '44px' }}>
          <span style={{ fontSize: '12.5px', fontWeight: 750, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#0284C7' }}>
            System Specifications
          </span>
          <h2 style={{ fontSize: '36px', fontWeight: 800, letterSpacing: '-0.025em', margin: '10px 0 14px 0' }}>
            Format Support & Mathematical Invariants
          </h2>
          <p style={{ fontSize: '16.5px', color: isLight ? '#334155' : '#CBD5E1', maxWidth: '720px', margin: '0 auto', lineHeight: 1.6 }}>
            Rigorous performance benchmarks measured across physical hardware displays and air-gapped test vectors.
          </p>
        </div>

        <div
          style={{
            overflowX: 'auto',
            background: isLight ? '#FFFFFF' : 'rgba(15, 23, 34, 0.75)',
            borderRadius: '18px',
            border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(56, 189, 248, 0.16)'}`,
            boxShadow: isLight ? '0 4px 16px rgba(0,0,0,0.03)' : '0 12px 36px rgba(0,0,0,0.4), 0 0 24px rgba(56, 189, 248, 0.06)'
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14.5px', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255, 255, 255, 0.12)'}`, background: isLight ? '#F8FAFC' : 'rgba(255, 255, 255, 0.04)' }}>
                <th style={{ padding: '16px 22px', fontWeight: 700, fontSize: '13.5px', textTransform: 'uppercase', letterSpacing: '0.04em', color: isLight ? '#0F172A' : '#F8FAFC' }}>Format / Layer</th>
                <th style={{ padding: '16px 22px', fontWeight: 700, fontSize: '13.5px', textTransform: 'uppercase', letterSpacing: '0.04em', color: isLight ? '#0F172A' : '#F8FAFC' }}>Embedding Technique</th>
                <th style={{ padding: '16px 22px', fontWeight: 700, fontSize: '13.5px', textTransform: 'uppercase', letterSpacing: '0.04em', color: isLight ? '#0F172A' : '#F8FAFC' }}>Recovery Invariant</th>
                <th style={{ padding: '16px 22px', fontWeight: 700, fontSize: '13.5px', textTransform: 'uppercase', letterSpacing: '0.04em', color: isLight ? '#0F172A' : '#F8FAFC' }}>Latency / Overhead</th>
              </tr>
            </thead>
            <tbody>
              {[
                {
                  format: 'PDF (Defense Briefs)',
                  tech: 'Dual-Layer Spatial Lattice + Micro-Kerning',
                  inv: 'Slant Angle ≤ 35°, Contrast Compression Q ≥ 30',
                  speed: '< 240ms / 20-page document'
                },
                {
                  format: 'DOCX / PPTX (Office)',
                  tech: 'OpenXML Part Signature + Glyph Displacement',
                  inv: 'Format Conversion & Re-saving Proof',
                  speed: '< 180ms injection latency'
                },
                {
                  format: 'XLSX (Data Sheets)',
                  tech: 'Numerical Precision Shift + XML Hash Tree',
                  inv: 'Cell Sorting & Sheet Extraction Proof',
                  speed: '< 120ms injection latency'
                },
                {
                  format: 'PNG / JPEG (Imagery)',
                  tech: 'Spread-Spectrum DCT/DWT Transform Mod',
                  inv: 'Heavy Crop (≥ 25% area) & Resize',
                  speed: '< 90ms per 4K frame'
                },
                {
                  format: 'Cryptographic Core',
                  tech: 'ML-KEM-768 + ML-DSA-65 (FIPS 203/204)',
                  inv: 'Quantum Cryptanalysis Immunity',
                  speed: 'Sub-millisecond key encapsulation'
                }
              ].map((row, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: idx < 4 ? `1px solid ${isLight ? '#F1F5F9' : 'rgba(255, 255, 255, 0.06)'}` : 'none'
                  }}
                >
                  <td style={{ padding: '16px 22px', fontWeight: 650, color: isLight ? '#0F172A' : '#F8FAFC' }}>
                    {row.format}
                  </td>
                  <td style={{ padding: '16px 22px', color: isLight ? '#334155' : '#E2E8F0' }}>
                    {row.tech}
                  </td>
                  <td style={{ padding: '16px 22px', color: isLight ? '#16A34A' : '#34D399', fontFamily: 'var(--font-mono, monospace)', fontSize: '13px' }}>
                    {row.inv}
                  </td>
                  <td style={{ padding: '16px 22px', color: isLight ? '#475569' : '#94A3B8', fontFamily: 'var(--font-mono, monospace)', fontSize: '13px' }}>
                    {row.speed}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* =========================================================================
          9. BOTTOM CALL TO ACTION
          ========================================================================= */}
      <section
        style={{
          padding: '90px 24px',
          background: isLight 
            ? 'radial-gradient(ellipse at 50% 100%, rgba(2, 132, 199, 0.12) 0%, #FFFFFF 85%)' 
            : 'radial-gradient(ellipse at 50% 100%, rgba(2, 132, 199, 0.24) 0%, #070A0F 80%)',
          borderTop: `1px solid ${isLight ? '#E2E8F0' : 'rgba(56, 189, 248, 0.18)'}`,
          textAlign: 'center',
          position: 'relative'
        }}
      >
        <div style={{ maxWidth: '760px', margin: '0 auto' }}>
          <h2 style={{ fontSize: '38px', fontWeight: 800, letterSpacing: '-0.025em', margin: '0 0 16px 0' }}>
            Ready to Protect Sovereign Intelligence?
          </h2>
          <p style={{ fontSize: '17px', color: isLight ? '#334155' : '#CBD5E1', lineHeight: 1.6, margin: '0 auto 36px auto' }}>
            Deploy AegisTrace across sovereign air-gapped enclaves, naval commands, or enterprise IP distribution networks.
          </p>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <button
              onClick={onEnterApp}
              className="main-btn-primary"
              style={{
                padding: '14px 34px',
                fontSize: '16px',
                fontWeight: 700,
                borderRadius: '9999px',
                background: '#0284C7',
                color: '#FFFFFF',
                border: 'none',
                boxShadow: '0 8px 30px rgba(2, 132, 199, 0.5)',
                cursor: 'pointer'
              }}
            >
              Access Forensic Workstation
            </button>
            <button
              onClick={() => setBriefingModalOpen(true)}
              className="main-btn-secondary"
              style={{
                padding: '14px 28px',
                fontSize: '15.5px',
                fontWeight: 650,
                borderRadius: '9999px',
                background: isLight ? '#FFFFFF' : 'rgba(255, 255, 255, 0.08)',
                border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.2)'}`,
                color: isLight ? '#0F172A' : '#F8FAFC',
                cursor: 'pointer'
              }}
            >
              Schedule Sovereign Briefing
            </button>
          </div>
        </div>
      </section>

      {/* =========================================================================
          10. PRODUCTION ENTERPRISE FOOTER
          ========================================================================= */}
      <footer
        style={{
          borderTop: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255, 255, 255, 0.1)'}`,
          background: isLight ? '#FFFFFF' : '#070A0F',
          padding: '56px 32px 36px 32px',
          fontSize: '14px',
          color: isLight ? '#475569' : '#CBD5E1'
        }}
      >
        <div
          style={{
            maxWidth: '1120px',
            margin: '0 auto',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '36px',
            marginBottom: '44px'
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <Shield size={20} style={{ color: '#0284C7' }} />
              <span style={{ fontSize: '17px', fontWeight: 750, color: isLight ? '#0F172A' : '#F8FAFC' }}>
                AegisTrace
              </span>
            </div>
            <p style={{ margin: 0, lineHeight: 1.6, color: isLight ? '#475569' : '#94A3B8' }}>
              Post-quantum cryptographic document protection, dynamic watermarking, and court-admissible forensic attribution.
            </p>
          </div>

          <div>
            <h4 style={{ margin: '0 0 14px 0', fontSize: '13px', fontWeight: 750, textTransform: 'uppercase', letterSpacing: '0.06em', color: isLight ? '#0F172A' : '#F8FAFC' }}>
              Platform
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <a href="#capabilities" style={{ color: 'inherit', textDecoration: 'none' }}>Core Capabilities</a>
              <a href="#demodulator" style={{ color: 'inherit', textDecoration: 'none' }}>Extraction Sandbox</a>
              <a href="#specifications" style={{ color: 'inherit', textDecoration: 'none' }}>Technical Invariants</a>
              <button onClick={onOpenVerify} style={{ background: 'none', border: 'none', color: 'inherit', padding: 0, textAlign: 'left', cursor: 'pointer', font: 'inherit' }}>
                Offline Verifier
              </button>
            </div>
          </div>

          <div>
            <h4 style={{ margin: '0 0 14px 0', fontSize: '13px', fontWeight: 750, textTransform: 'uppercase', letterSpacing: '0.06em', color: isLight ? '#0F172A' : '#F8FAFC' }}>
              Compliance & Legal
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <span>Bharatiya Sakshya Adhiniyam 2023 § 63</span>
              <span>Section 65B Certificate Generation</span>
              <span>NIST FIPS 203 (ML-KEM) Aligned</span>
              <span>NIST FIPS 204 (ML-DSA) Aligned</span>
              <span>CERT-In CBOM Specifications</span>
            </div>
          </div>

          <div>
            <h4 style={{ margin: '0 0 14px 0', fontSize: '13px', fontWeight: 750, textTransform: 'uppercase', letterSpacing: '0.06em', color: isLight ? '#0F172A' : '#F8FAFC' }}>
              Sovereignty
            </h4>
            <p style={{ margin: 0, lineHeight: 1.6, color: isLight ? '#475569' : '#94A3B8' }}>
              Designed for Sovereign Enclaves, Ministry of Defence (MoD) / Naval Systems, and High-Assurance Enterprise Intellectual Property.
            </p>
            <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '16px' }}>🇮🇳</span>
              <span style={{ fontWeight: 650, color: isLight ? '#0F172A' : '#F8FAFC' }}>Atmanirbhar Bharat Initiative</span>
            </div>
          </div>
        </div>

        <div
          style={{
            maxWidth: '1120px',
            margin: '0 auto',
            paddingTop: '28px',
            borderTop: `1px solid ${isLight ? '#F1F5F9' : 'rgba(255, 255, 255, 0.08)'}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '14px',
            fontSize: '13px',
            color: isLight ? '#64748B' : '#94A3B8'
          }}
        >
          <div>
            © 2026 AegisTrace Sovereign Systems. All rights reserved.
          </div>
          <div style={{ display: 'flex', gap: '18px' }}>
            <span>Air-Gapped Deployment</span>
            <span>•</span>
            <span>Zero Telemetry Policy</span>
            <span>•</span>
            <span>Provable Traitor Tracing</span>
          </div>
        </div>
      </footer>

      {/* =========================================================================
          11. BRIEFING / CONSULTATION REQUEST MODAL
          ========================================================================= */}
      <AnimatePresence>
        {briefingModalOpen && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.75)',
              backdropFilter: 'blur(12px)',
              zIndex: 100,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '20px'
            }}
            onClick={() => setBriefingModalOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                width: '500px',
                maxWidth: '100%',
                background: isLight ? '#FFFFFF' : '#0C121D',
                borderRadius: '24px',
                border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(56, 189, 248, 0.2)'}`,
                padding: '36px',
                boxShadow: '0 24px 60px rgba(0,0,0,0.6), 0 0 30px rgba(56, 189, 248, 0.08)',
                position: 'relative'
              }}
            >
              <button
                onClick={() => setBriefingModalOpen(false)}
                style={{
                  position: 'absolute',
                  top: '22px',
                  right: '22px',
                  background: 'none',
                  border: 'none',
                  color: isLight ? '#94A3B8' : '#64748B',
                  cursor: 'pointer'
                }}
              >
                <X size={20} />
              </button>

              {briefingSubmitted ? (
                <div style={{ textAlign: 'center', padding: '28px 0' }}>
                  <div style={{ width: '52px', height: '52px', borderRadius: '50%', background: 'rgba(34, 197, 94, 0.15)', color: '#22C55E', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 18px auto' }}>
                    <CheckCircle2 size={28} />
                  </div>
                  <h3 style={{ fontSize: '22px', fontWeight: 800, margin: '0 0 10px 0' }}>
                    Briefing Request Registered
                  </h3>
                  <p style={{ fontSize: '14.5px', color: isLight ? '#475569' : '#CBD5E1', lineHeight: 1.6, marginBottom: '28px' }}>
                    Your cryptographic reservation docket has been recorded. An accredited defense technical representative will reach out via sovereign channels.
                  </p>
                  <button
                    onClick={() => {
                      setBriefingSubmitted(false);
                      setBriefingModalOpen(false);
                    }}
                    className="main-btn-primary"
                    style={{ padding: '12px 28px', borderRadius: '9999px', fontSize: '14.5px', fontWeight: 650 }}
                  >
                    Close
                  </button>
                </div>
              ) : (
                <form onSubmit={handleBriefingSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                  <div>
                    <h3 style={{ fontSize: '22px', fontWeight: 800, margin: '0 0 6px 0' }}>
                      Request Tactical Briefing
                    </h3>
                    <p style={{ fontSize: '14px', color: isLight ? '#64748B' : '#94A3B8', margin: 0 }}>
                      For defense commands, law enforcement, and sovereign enclaves.
                    </p>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 650, marginBottom: '6px' }}>
                      Full Name & Rank
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Marcus Vance / Dr. Aris Thorne"
                      value={briefingForm.name}
                      onChange={(e) => setBriefingForm({ ...briefingForm, name: e.target.value })}
                      style={{
                        width: '100%',
                        height: '44px',
                        borderRadius: '12px',
                        border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255,255,255,0.14)'}`,
                        background: isLight ? '#F8FAFC' : 'rgba(255,255,255,0.05)',
                        color: isLight ? '#0F172A' : '#F8FAFC',
                        padding: '0 14px',
                        fontSize: '14px',
                        boxSizing: 'border-box'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 650, marginBottom: '6px' }}>
                      Agency / Directorate / Organization
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Naval Enclave / CERT-In / Defence Labs"
                      value={briefingForm.agency}
                      onChange={(e) => setBriefingForm({ ...briefingForm, agency: e.target.value })}
                      style={{
                        width: '100%',
                        height: '44px',
                        borderRadius: '12px',
                        border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255,255,255,0.14)'}`,
                        background: isLight ? '#F8FAFC' : 'rgba(255,255,255,0.05)',
                        color: isLight ? '#0F172A' : '#F8FAFC',
                        padding: '0 14px',
                        fontSize: '14px',
                        boxSizing: 'border-box'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 650, marginBottom: '6px' }}>
                      Official Electronic Mail
                    </label>
                    <input
                      type="email"
                      required
                      placeholder="officer@defence.gov.in"
                      value={briefingForm.email}
                      onChange={(e) => setBriefingForm({ ...briefingForm, email: e.target.value })}
                      style={{
                        width: '100%',
                        height: '44px',
                        borderRadius: '12px',
                        border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255,255,255,0.14)'}`,
                        background: isLight ? '#F8FAFC' : 'rgba(255,255,255,0.05)',
                        color: isLight ? '#0F172A' : '#F8FAFC',
                        padding: '0 14px',
                        fontSize: '14px',
                        boxSizing: 'border-box'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 650, marginBottom: '6px' }}>
                      Deployment Enclave
                    </label>
                    <select
                      value={briefingForm.enclaveType}
                      onChange={(e) => setBriefingForm({ ...briefingForm, enclaveType: e.target.value })}
                      style={{
                        width: '100%',
                        height: '44px',
                        borderRadius: '12px',
                        border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255,255,255,0.14)'}`,
                        background: isLight ? '#F8FAFC' : '#111927',
                        color: isLight ? '#0F172A' : '#F8FAFC',
                        padding: '0 14px',
                        fontSize: '14px',
                        boxSizing: 'border-box'
                      }}
                    >
                      <option value="airgap">Air-Gapped Sovereign Hardware Enclave</option>
                      <option value="naval">Naval / Maritime Tactical Network</option>
                      <option value="govcloud">Government Sovereign Cloud (MeitY Empanelled)</option>
                      <option value="enterprise">Enterprise High-Assurance IP Infrastructure</option>
                    </select>
                  </div>

                  <button
                    type="submit"
                    className="main-btn-primary"
                    style={{
                      width: '100%',
                      height: '48px',
                      borderRadius: '9999px',
                      fontSize: '15px',
                      fontWeight: 700,
                      background: '#0284C7',
                      color: '#FFFFFF',
                      border: 'none',
                      marginTop: '8px',
                      cursor: 'pointer'
                    }}
                  >
                    Submit Tactical Request
                  </button>
                </form>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

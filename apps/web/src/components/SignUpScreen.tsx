import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  Loader2, 
  AlertCircle,
  Building,
  Mail,
  User,
  Lock,
  Sun,
  Moon
} from 'lucide-react';
import { motion } from 'framer-motion';
import { apiService } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { Forensic3DBackground } from './common/Forensic3DBackground';
import { MagneticCursor } from './common/MagneticCursor';

interface SignUpScreenProps {
  onSwitchToSignIn: () => void;
  onOpenVerifyStandalone?: () => void;
}

export const SignUpScreen: React.FC<SignUpScreenProps> = ({
  onSwitchToSignIn,
  onOpenVerifyStandalone
}) => {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === 'light';

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [organization, setOrganization] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim() || !email.trim() || !password.trim()) {
      setErrorMessage('Please provide your name, official email, and passphrase.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passphrases do not match.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      await apiService.register({
        name: name.trim(),
        email: email.trim(),
        organization: organization.trim() || undefined,
        password: password.trim()
      });
    } catch (err: any) {
      setErrorMessage(err.message || 'Registration unavailable in this deployment.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100vw',
        background: isLight 
          ? 'radial-gradient(ellipse at 50% 30%, #FFFFFF 0%, #F8FAFC 60%, #F1F5F9 100%)' 
          : 'radial-gradient(ellipse at 50% 30%, #0F1722 0%, #080C10 75%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        position: 'relative',
        overflow: 'hidden',
        transition: 'background 0.3s ease'
      }}
    >
      {/* 3D Animated Forensic Cryptographic Background Canvas */}
      <Forensic3DBackground interactive={true} intensity={1.0} />

      {/* Smooth Magnetic Tracking Cursor */}
      <MagneticCursor />

      {/* Top Header Floating Controls (Theme Toggle & SIH Badging) */}
      <div
        style={{
          position: 'absolute',
          top: '20px',
          right: '24px',
          zIndex: 30,
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '5px 12px',
            backgroundColor: isLight ? 'rgba(255, 255, 255, 0.90)' : 'rgba(18, 27, 35, 0.85)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.12)'}`,
            borderRadius: '20px',
            fontSize: '11.5px',
            fontWeight: 650,
            color: isLight ? '#0284C7' : '#38BDF8',
            letterSpacing: '0.02em',
            boxShadow: isLight ? '0 4px 12px rgba(15, 23, 42, 0.06)' : '0 4px 14px rgba(0,0,0,0.4)'
          }}
        >
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: '#10B981', display: 'inline-block', boxShadow: '0 0 8px #10B981' }} />
          <span>Post-Quantum Enclave Provisioning</span>
        </div>

        <button
          onClick={toggleTheme}
          title={`Switch to ${isLight ? 'Dark' : 'Light'} Mode`}
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            backgroundColor: isLight ? 'rgba(255, 255, 255, 0.90)' : 'rgba(18, 27, 35, 0.85)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.12)'}`,
            color: isLight ? '#334155' : '#CBD5E1',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: isLight ? '0 4px 12px rgba(15, 23, 42, 0.06)' : '0 4px 14px rgba(0,0,0,0.4)'
          }}
        >
          {isLight ? <Moon size={16} /> : <Sun size={16} />}
        </button>
      </div>

      {/* Account Creation Card */}
      <motion.div
        initial={{ opacity: 0, y: 14, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="workstation-card specular-border"
        style={{
          width: '100%',
          maxWidth: '464px',
          backgroundColor: isLight ? 'rgba(255, 255, 255, 0.92)' : 'rgba(18, 27, 35, 0.85)',
          backdropFilter: 'blur(36px) saturate(190%)',
          WebkitBackdropFilter: 'blur(36px) saturate(190%)',
          border: `1px solid ${isLight ? 'rgba(203, 213, 225, 0.95)' : 'rgba(255, 255, 255, 0.12)'}`,
          borderRadius: '16px',
          padding: '32px 28px',
          boxShadow: isLight 
            ? '0 1px 0 0 rgba(255, 255, 255, 1) inset, 0 24px 50px -12px rgba(15, 23, 42, 0.12), 0 4px 16px rgba(15, 23, 42, 0.04)'
            : '0 1px 0 0 rgba(255, 255, 255, 0.08) inset, 0 32px 64px -16px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.06)',
          position: 'relative',
          zIndex: 10
        }}
      >
        {/* Header & Cryptographic Emblem */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '22px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: isLight 
                ? 'linear-gradient(135deg, rgba(2, 132, 199, 0.14) 0%, rgba(15, 118, 110, 0.12) 100%)' 
                : 'linear-gradient(135deg, rgba(56, 189, 248, 0.16) 0%, rgba(45, 212, 191, 0.14) 100%)',
              border: `1px solid ${isLight ? 'rgba(2, 132, 199, 0.3)' : 'rgba(56, 189, 248, 0.35)'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isLight ? '#0284C7' : '#38BDF8',
              marginBottom: '12px',
              boxShadow: isLight ? '0 4px 12px rgba(2, 132, 199, 0.15)' : '0 4px 16px rgba(56, 189, 248, 0.2)'
            }}
          >
            <ShieldCheck size={26} strokeWidth={2.0} />
          </div>

          <h1
            style={{
              fontSize: '22px',
              fontWeight: 750,
              color: isLight ? '#0F172A' : '#F8FAFC',
              letterSpacing: '-0.025em',
              margin: '0 0 4px 0'
            }}
          >
            AegisTrace
          </h1>

          <p
            style={{
              fontSize: '13.5px',
              color: isLight ? '#475569' : '#94A3B8',
              margin: 0,
              textAlign: 'center',
              fontWeight: 500
            }}
          >
            Provision forensic officer workspace.
          </p>
        </div>

        {/* Security / Error State Banner */}
        {errorMessage && (
          <div
            role="alert"
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              padding: '12px 14px',
              backgroundColor: 'var(--danger-subtle)',
              border: '1px solid var(--danger-border)',
              borderRadius: '8px',
              marginBottom: '18px',
              fontSize: '12.5px',
              color: 'var(--danger)',
              lineHeight: 1.45
            }}
          >
            <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: 650 }}>Provisioning Notice</div>
              <div>{errorMessage}</div>
            </div>
          </div>
        )}

        {/* Sign-Up Form */}
        <form onSubmit={handleSubmit} noValidate>
          {/* Name */}
          <div style={{ marginBottom: '14px' }}>
            <label
              htmlFor="signup-name"
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: 650,
                color: isLight ? '#334155' : '#CBD5E1',
                marginBottom: '5px'
              }}
            >
              Full Name / Officer Title
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="signup-name"
                type="text"
                required
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="e.g. Commander Sarah Vance"
                disabled={isLoading}
                style={{
                  width: '100%',
                  height: '40px',
                  padding: '0 14px 0 38px',
                  backgroundColor: isLight ? '#FFFFFF' : 'rgba(11, 16, 21, 0.85)',
                  border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)'}`,
                  borderRadius: '8px',
                  color: isLight ? '#0F172A' : '#F8FAFC',
                  fontSize: '13px',
                  fontWeight: 500,
                  outline: 'none',
                  transition: 'border-color 0.15s ease, box-shadow 0.15s ease'
                }}
                onFocus={e => {
                  e.target.style.borderColor = isLight ? '#0284C7' : '#38BDF8';
                  e.target.style.boxShadow = isLight 
                    ? '0 0 0 3px rgba(2, 132, 199, 0.16)' 
                    : '0 0 0 3px rgba(56, 189, 248, 0.2)';
                }}
                onBlur={e => {
                  e.target.style.borderColor = isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)';
                  e.target.style.boxShadow = 'none';
                }}
              />
              <User size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: isLight ? '#64748B' : '#73808C' }} />
            </div>
          </div>

          {/* Email */}
          <div style={{ marginBottom: '14px' }}>
            <label
              htmlFor="signup-email"
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: 650,
                color: isLight ? '#334155' : '#CBD5E1',
                marginBottom: '5px'
              }}
            >
              Official Agency Email
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="signup-email"
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="officer@agency.gov"
                disabled={isLoading}
                style={{
                  width: '100%',
                  height: '40px',
                  padding: '0 14px 0 38px',
                  backgroundColor: isLight ? '#FFFFFF' : 'rgba(11, 16, 21, 0.85)',
                  border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)'}`,
                  borderRadius: '8px',
                  color: isLight ? '#0F172A' : '#F8FAFC',
                  fontSize: '13px',
                  fontWeight: 500,
                  outline: 'none',
                  transition: 'border-color 0.15s ease, box-shadow 0.15s ease'
                }}
                onFocus={e => {
                  e.target.style.borderColor = isLight ? '#0284C7' : '#38BDF8';
                  e.target.style.boxShadow = isLight 
                    ? '0 0 0 3px rgba(2, 132, 199, 0.16)' 
                    : '0 0 0 3px rgba(56, 189, 248, 0.2)';
                }}
                onBlur={e => {
                  e.target.style.borderColor = isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)';
                  e.target.style.boxShadow = 'none';
                }}
              />
              <Mail size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: isLight ? '#64748B' : '#73808C' }} />
            </div>
          </div>

          {/* Organization */}
          <div style={{ marginBottom: '14px' }}>
            <label
              htmlFor="signup-org"
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: 650,
                color: isLight ? '#334155' : '#CBD5E1',
                marginBottom: '5px'
              }}
            >
              Command / Forensic Lab (Optional)
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="signup-org"
                type="text"
                value={organization}
                onChange={e => setOrganization(e.target.value)}
                placeholder="Naval Cyber Command / CERT Lab"
                disabled={isLoading}
                style={{
                  width: '100%',
                  height: '40px',
                  padding: '0 14px 0 38px',
                  backgroundColor: isLight ? '#FFFFFF' : 'rgba(11, 16, 21, 0.85)',
                  border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)'}`,
                  borderRadius: '8px',
                  color: isLight ? '#0F172A' : '#F8FAFC',
                  fontSize: '13px',
                  fontWeight: 500,
                  outline: 'none',
                  transition: 'border-color 0.15s ease, box-shadow 0.15s ease'
                }}
                onFocus={e => {
                  e.target.style.borderColor = isLight ? '#0284C7' : '#38BDF8';
                  e.target.style.boxShadow = isLight 
                    ? '0 0 0 3px rgba(2, 132, 199, 0.16)' 
                    : '0 0 0 3px rgba(56, 189, 248, 0.2)';
                }}
                onBlur={e => {
                  e.target.style.borderColor = isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)';
                  e.target.style.boxShadow = 'none';
                }}
              />
              <Building size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: isLight ? '#64748B' : '#73808C' }} />
            </div>
          </div>

          {/* Password */}
          <div style={{ marginBottom: '14px' }}>
            <label
              htmlFor="signup-password"
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: 650,
                color: isLight ? '#334155' : '#CBD5E1',
                marginBottom: '5px'
              }}
            >
              Master Passphrase
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="signup-password"
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Choose high-entropy passphrase"
                disabled={isLoading}
                style={{
                  width: '100%',
                  height: '40px',
                  padding: '0 40px 0 38px',
                  backgroundColor: isLight ? '#FFFFFF' : 'rgba(11, 16, 21, 0.85)',
                  border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)'}`,
                  borderRadius: '8px',
                  color: isLight ? '#0F172A' : '#F8FAFC',
                  fontSize: '13px',
                  fontWeight: 500,
                  outline: 'none',
                  transition: 'border-color 0.15s ease, box-shadow 0.15s ease'
                }}
                onFocus={e => {
                  e.target.style.borderColor = isLight ? '#0284C7' : '#38BDF8';
                  e.target.style.boxShadow = isLight 
                    ? '0 0 0 3px rgba(2, 132, 199, 0.16)' 
                    : '0 0 0 3px rgba(56, 189, 248, 0.2)';
                }}
                onBlur={e => {
                  e.target.style.borderColor = isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)';
                  e.target.style.boxShadow = 'none';
                }}
              />
              <Lock size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: isLight ? '#64748B' : '#73808C' }} />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                aria-label={showPassword ? 'Hide passphrase' : 'Show passphrase'}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: isLight ? '#64748B' : '#73808C',
                  cursor: 'pointer',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Confirm Password */}
          <div style={{ marginBottom: '22px' }}>
            <label
              htmlFor="signup-confirm-password"
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: 650,
                color: isLight ? '#334155' : '#CBD5E1',
                marginBottom: '5px'
              }}
            >
              Confirm Master Passphrase
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="signup-confirm-password"
                type={showPassword ? 'text' : 'password'}
                required
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="Confirm your passphrase"
                disabled={isLoading}
                style={{
                  width: '100%',
                  height: '40px',
                  padding: '0 14px 0 38px',
                  backgroundColor: isLight ? '#FFFFFF' : 'rgba(11, 16, 21, 0.85)',
                  border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)'}`,
                  borderRadius: '8px',
                  color: isLight ? '#0F172A' : '#F8FAFC',
                  fontSize: '13px',
                  fontWeight: 500,
                  outline: 'none',
                  transition: 'border-color 0.15s ease, box-shadow 0.15s ease'
                }}
                onFocus={e => {
                  e.target.style.borderColor = isLight ? '#0284C7' : '#38BDF8';
                  e.target.style.boxShadow = isLight 
                    ? '0 0 0 3px rgba(2, 132, 199, 0.16)' 
                    : '0 0 0 3px rgba(56, 189, 248, 0.2)';
                }}
                onBlur={e => {
                  e.target.style.borderColor = isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)';
                  e.target.style.boxShadow = 'none';
                }}
              />
              <Lock size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: isLight ? '#64748B' : '#73808C' }} />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              height: '42px',
              borderRadius: '8px',
              fontSize: '13.5px',
              fontWeight: 650,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.75 : 1,
              background: isLight 
                ? 'linear-gradient(135deg, #0284C7 0%, #0F766E 100%)' 
                : 'linear-gradient(135deg, #0284C7 0%, #0E7490 100%)',
              color: '#FFFFFF',
              border: 'none',
              boxShadow: isLight ? '0 4px 14px rgba(2, 132, 199, 0.28)' : '0 4px 18px rgba(2, 132, 199, 0.35)',
              transition: 'transform 0.15s ease, box-shadow 0.15s ease'
            }}
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="spin" />
                <span>Provisioning workspace enclave…</span>
              </>
            ) : (
              <>
                <span>Create Workspace Enclave</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* Already have an account */}
        <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '12.5px', color: isLight ? '#64748B' : '#94A3B8' }}>
          Already have an officer credential?{' '}
          <button
            type="button"
            onClick={onSwitchToSignIn}
            style={{
              background: 'none',
              border: 'none',
              color: isLight ? '#0284C7' : '#38BDF8',
              cursor: 'pointer',
              fontWeight: 650,
              padding: 0,
              fontSize: '12.5px',
              textDecoration: 'underline'
            }}
          >
            Sign in
          </button>
        </div>

        {/* Standalone Verify link */}
        {onOpenVerifyStandalone && (
          <div 
            style={{ 
              marginTop: '16px', 
              paddingTop: '14px', 
              borderTop: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255, 255, 255, 0.08)'}`, 
              textAlign: 'center', 
              fontSize: '12px', 
              color: isLight ? '#64748B' : '#94A3B8' 
            }}
          >
            Judicial examiner or court auditor?{' '}
            <button
              type="button"
              onClick={onOpenVerifyStandalone}
              style={{
                background: 'none',
                border: 'none',
                color: isLight ? '#0F766E' : '#2DD4BF',
                cursor: 'pointer',
                fontWeight: 650,
                padding: 0,
                fontSize: '12px',
                textDecoration: 'underline'
              }}
            >
              Open AegisTrace Verify (Zero-Server) →
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
};

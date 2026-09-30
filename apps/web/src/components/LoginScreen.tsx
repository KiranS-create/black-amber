import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  Loader2, 
  AlertCircle,
  KeyRound,
  Lock,
  User,
  Sun,
  Moon,
  CheckCircle2
} from 'lucide-react';
import { motion } from 'framer-motion';
import { UserSession } from '../types';
import { apiService } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { Forensic3DBackground } from './common/Forensic3DBackground';
import { MagneticCursor } from './common/MagneticCursor';

interface LoginScreenProps {
  onLoginSuccess: (session: UserSession) => void;
  onSwitchToSignUp?: () => void;
  onOpenVerifyStandalone?: () => void;
  sessionExpired?: boolean;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({
  onLoginSuccess,
  onSwitchToSignUp,
  onOpenVerifyStandalone,
  sessionExpired = false
}) => {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === 'light';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [autofillApplied, setAutofillApplied] = useState(false);
  const [demoAuthAvailable, setDemoAuthAvailable] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(
    sessionExpired ? 'Session expired. Please sign in again.' : null
  );

  useEffect(() => {
    // Probe backend auth status
    apiService.getAuthStatus().then(status => {
      setDemoAuthAvailable(status.demo_auth_enabled);
    }).catch(() => {
      setDemoAuthAvailable(true);
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setErrorMessage('Please enter both username and password.');
      return;
    }

    const trimmedUser = username.trim();
    if (trimmedUser.includes('@')) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(trimmedUser)) {
        setErrorMessage('Please enter a valid email address (e.g., officer@agency.gov).');
        return;
      }
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const session = await apiService.login({
        email: username.trim(),
        password: password.trim()
      });
      onLoginSuccess(session);
    } catch (err: any) {
      if (err?.message?.includes('fetch') || err?.message?.includes('NetworkError') || err?.name === 'TypeError') {
        setErrorMessage('Unable to connect to the authentication service.');
      } else if (err?.message) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Invalid credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyDemoCredentials = () => {
    setUsername('admin');
    setPassword('admin');
    setErrorMessage(null);
    setAutofillApplied(true);
    setTimeout(() => setAutofillApplied(false), 2500);
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

      {/* Authentication Card (Layer 2 Elevated Frosted Glass Surface) */}
      <motion.div
        initial={{ opacity: 0, y: 14, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="workstation-card specular-border"
        style={{
          width: '100%',
          maxWidth: '436px',
          backgroundColor: isLight ? 'rgba(255, 255, 255, 0.92)' : 'rgba(18, 27, 35, 0.85)',
          backdropFilter: 'blur(36px) saturate(190%)',
          WebkitBackdropFilter: 'blur(36px) saturate(190%)',
          border: `1px solid ${isLight ? 'rgba(203, 213, 225, 0.95)' : 'rgba(255, 255, 255, 0.12)'}`,
          borderRadius: '16px',
          padding: '34px 28px',
          boxShadow: isLight 
            ? '0 1px 0 0 rgba(255, 255, 255, 1) inset, 0 24px 50px -12px rgba(15, 23, 42, 0.12), 0 4px 16px rgba(15, 23, 42, 0.04)'
            : '0 1px 0 0 rgba(255, 255, 255, 0.08) inset, 0 32px 64px -16px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.06)',
          position: 'relative',
          zIndex: 10
        }}
      >
        {/* Header & Cryptographic Emblem */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '24px' }}>
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
            Zero-trust forensic provenance workstation.
          </p>
        </div>

        {/* Security State Banner (Error / Session Expired) */}
        {errorMessage && (
          <div
            role="alert"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '10px 14px',
              backgroundColor: 'var(--danger-subtle)',
              border: '1px solid var(--danger-border)',
              borderRadius: '8px',
              marginBottom: '18px',
              fontSize: '12.5px',
              color: 'var(--danger)',
              lineHeight: 1.4
            }}
          >
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Authentication Form */}
        <form onSubmit={handleSubmit} noValidate>
          {/* Username / Email Input */}
          <div style={{ marginBottom: '16px' }}>
            <label
              htmlFor="login-username"
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: 650,
                color: isLight ? '#334155' : '#CBD5E1',
                marginBottom: '6px'
              }}
            >
              Username / Identity
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="login-username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="Enter username"
                disabled={isLoading}
                style={{
                  width: '100%',
                  height: '42px',
                  padding: '0 14px 0 38px',
                  backgroundColor: isLight ? '#FFFFFF' : 'rgba(11, 16, 21, 0.85)',
                  border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)'}`,
                  borderRadius: '8px',
                  color: isLight ? '#0F172A' : '#F8FAFC',
                  fontSize: '13.5px',
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
              <User size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: isLight ? '#64748B' : '#73808C' }} />
            </div>
          </div>

          {/* Password Input */}
          <div style={{ marginBottom: '22px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label
                htmlFor="login-password"
                style={{
                  fontSize: '12px',
                  fontWeight: 650,
                  color: isLight ? '#334155' : '#CBD5E1'
                }}
              >
                Passphrase
              </label>
            </div>
            <div style={{ position: 'relative' }}>
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Enter passphrase"
                disabled={isLoading}
                style={{
                  width: '100%',
                  height: '42px',
                  padding: '0 40px 0 38px',
                  backgroundColor: isLight ? '#FFFFFF' : 'rgba(11, 16, 21, 0.85)',
                  border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)'}`,
                  borderRadius: '8px',
                  color: isLight ? '#0F172A' : '#F8FAFC',
                  fontSize: '13.5px',
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
              <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: isLight ? '#64748B' : '#73808C' }} />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
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

          {/* Submit Action */}
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
                <span>Authenticating enclave…</span>
              </>
            ) : (
              <>
                <span>Sign in to Enclave</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* DEMO ACCESS Box (Natural, Elegant, SIH Judge Focused) */}
        {demoAuthAvailable && (
          <div
            style={{
              marginTop: '20px',
              padding: '12px 14px',
              backgroundColor: isLight ? 'rgba(241, 245, 249, 0.95)' : 'rgba(15, 22, 29, 0.90)',
              border: `1px solid ${autofillApplied ? (isLight ? '#0284C7' : '#38BDF8') : (isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.10)')}`,
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              transition: 'all 0.2s ease',
              boxShadow: isLight ? '0 2px 8px rgba(15, 23, 42, 0.04)' : 'none'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <KeyRound size={17} style={{ color: isLight ? '#0284C7' : '#38BDF8', flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: '11px', fontWeight: 750, color: isLight ? '#0369A1' : '#38BDF8', letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>SIH JUDGE EVALUATION ACCESS</span>
                  {autofillApplied && (
                    <span style={{ fontSize: '10.5px', color: '#10B981', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                      <CheckCircle2 size={12} /> Applied
                    </span>
                  )}
                </div>
                <div style={{ fontSize: '12px', color: isLight ? '#475569' : '#94A3B8', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                  User: <strong style={{ color: isLight ? '#0F172A' : '#F8FAFC' }}>admin</strong> &nbsp;|&nbsp; Pass: <strong style={{ color: isLight ? '#0F172A' : '#F8FAFC' }}>admin</strong>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleApplyDemoCredentials}
              className="btn-secondary"
              style={{
                fontSize: '11.5px',
                fontWeight: 600,
                padding: '5px 12px',
                height: '30px',
                borderRadius: '6px',
                flexShrink: 0,
                backgroundColor: autofillApplied 
                  ? (isLight ? 'rgba(2, 132, 199, 0.15)' : 'rgba(56, 189, 248, 0.2)') 
                  : (isLight ? '#FFFFFF' : 'rgba(255, 255, 255, 0.08)'),
                borderColor: autofillApplied ? (isLight ? '#0284C7' : '#38BDF8') : (isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.16)'),
                color: autofillApplied ? (isLight ? '#0284C7' : '#38BDF8') : (isLight ? '#334155' : '#E2E8F0'),
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {autofillApplied ? 'Loaded' : '1-Click Autofill'}
            </button>
          </div>
        )}

        {/* Create workspace link */}
        {onSwitchToSignUp && (
          <div style={{ marginTop: '18px', textAlign: 'center', fontSize: '12.5px', color: isLight ? '#64748B' : '#94A3B8' }}>
            Need an official workspace?{' '}
            <button
              type="button"
              onClick={onSwitchToSignUp}
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
              Enroll officer identity
            </button>
          </div>
        )}


      </motion.div>
    </div>
  );
};

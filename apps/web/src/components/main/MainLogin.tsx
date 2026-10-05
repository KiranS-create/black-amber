import React, { useState } from 'react';
import { Shield, ArrowRight, Eye, EyeOff, CheckCircle2, Lock, UserCheck, KeyRound, Sun, Moon } from 'lucide-react';
import { motion } from 'framer-motion';
import { apiService } from '../../services/api';
import { UserSession } from '../../types';
import { useTheme } from '../../context/ThemeContext';
import { Forensic3DBackground } from '../common/Forensic3DBackground';
import { MagneticCursor } from '../common/MagneticCursor';

interface MainLoginProps {
  onLoginSuccess: (session: UserSession) => void;
  onOpenVerifyStandalone: () => void;
  onOpenSignUp: () => void;
  onBackToLanding?: () => void;
}

export const MainLogin: React.FC<MainLoginProps> = ({
  onLoginSuccess,
  onOpenVerifyStandalone,
  onOpenSignUp,
  onBackToLanding
}) => {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === 'light';

  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [autofillApplied, setAutofillApplied] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setErrorMessage('Please enter both username and password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const session = await apiService.login({ email: username.trim(), password: password.trim() });
      onLoginSuccess(session);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAutofillCredentials = () => {
    setUsername('admin');
    setPassword('admin');
    setErrorMessage(null);
    setAutofillApplied(true);
    setTimeout(() => setAutofillApplied(false), 3000);
  };

  const handleQuickSignIn = async () => {
    setUsername('admin');
    setPassword('admin');
    setErrorMessage(null);
    setAutofillApplied(true);
    setIsLoading(true);
    try {
      const session = await apiService.login({ email: 'admin', password: 'admin' });
      onLoginSuccess(session);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: isLight 
          ? 'radial-gradient(ellipse at 50% 30%, #FFFFFF 0%, #F8FAFC 60%, #F1F5F9 100%)' 
          : 'radial-gradient(ellipse at 50% 30%, #0F1722 0%, #080C10 75%)',
        color: isLight ? '#0F172A' : '#EDEDE8',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        position: 'relative',
        overflow: 'hidden',
        fontFamily: "'Geist', system-ui, sans-serif",
        transition: 'background 0.3s ease, color 0.3s ease'
      }}
    >
      {/* 3D Animated Forensic Background */}
      <Forensic3DBackground interactive={true} intensity={1.0} />

      {/* Smooth Magnetic Tracking Cursor */}
      <MagneticCursor />

      {/* Top Header Floating Controls */}
      {onBackToLanding && (
        <div
          style={{
            position: 'absolute',
            top: '20px',
            left: '24px',
            zIndex: 30
          }}
        >
          <button
            onClick={onBackToLanding}
            style={{
              padding: '8px 16px',
              borderRadius: '9999px',
              backgroundColor: isLight ? 'rgba(255, 255, 255, 0.90)' : 'rgba(18, 27, 35, 0.85)',
              backdropFilter: 'blur(16px)',
              border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.12)'}`,
              color: isLight ? '#0F172A' : '#F8FAFC',
              fontSize: '12.5px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: isLight ? '0 4px 12px rgba(15, 23, 42, 0.06)' : '0 4px 14px rgba(0,0,0,0.4)'
            }}
          >
            ← Platform Overview
          </button>
        </div>
      )}

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

      <motion.div
        initial={{ opacity: 0, y: 14, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        style={{
          width: '436px',
          maxWidth: '100%',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
          position: 'relative',
          zIndex: 10
        }}
      >
        {/* Brand Anchor */}
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: isLight 
                ? 'linear-gradient(135deg, rgba(2, 132, 199, 0.14) 0%, rgba(15, 118, 110, 0.12) 100%)' 
                : 'linear-gradient(135deg, rgba(56, 189, 248, 0.16) 0%, rgba(45, 212, 191, 0.14) 100%)',
              border: `1px solid ${isLight ? 'rgba(2, 132, 199, 0.3)' : 'rgba(56, 189, 248, 0.35)'}`,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '12px',
              boxShadow: isLight ? '0 4px 12px rgba(2, 132, 199, 0.15)' : '0 4px 16px rgba(56, 189, 248, 0.2)'
            }}
          >
            <Shield size={24} style={{ color: isLight ? '#0284C7' : '#38BDF8' }} />
          </div>
          <h1 style={{ fontSize: '22px', fontWeight: 750, margin: 0, letterSpacing: '-0.025em', color: isLight ? '#0F172A' : '#F8FAFC' }}>
            AegisTrace Enterprise Workstation
          </h1>
          <p style={{ fontSize: '13.5px', color: isLight ? '#475569' : '#94A3B8', margin: '4px 0 0 0', fontWeight: 500 }}>
            Post-quantum cryptographic document attribution.
          </p>
        </div>

        {/* Login Box - Apple macOS Lock Screen Squircle */}
        <div
          style={{
            background: isLight ? 'rgba(255, 255, 255, 0.88)' : 'rgba(28, 28, 32, 0.78)',
            backdropFilter: 'blur(36px) saturate(200%)',
            WebkitBackdropFilter: 'blur(36px) saturate(200%)',
            border: `1px solid ${isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.16)'}`,
            borderRadius: '28px',
            padding: '36px 32px',
            boxShadow: isLight 
              ? 'inset 0 1px 1px 0 #FFFFFF, 0 24px 60px -12px rgba(0, 0, 0, 0.08), 0 4px 16px rgba(0, 0, 0, 0.03)' 
              : 'inset 0 1px 1px 0 rgba(255, 255, 255, 0.18), 0 32px 64px -16px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.04)'
          }}
        >
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            {errorMessage && (
              <div
                style={{
                  padding: '10px 14px',
                  borderRadius: '12px',
                  background: 'rgba(255, 69, 58, 0.12)',
                  border: '1px solid rgba(255, 69, 58, 0.25)',
                  color: '#FF453A',
                  fontSize: '12.5px',
                  fontWeight: 500
                }}
              >
                {errorMessage}
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: isLight ? '#1D1D1F' : '#F5F5F7', marginBottom: '7px', letterSpacing: '-0.01em' }}>
                Username / Principal ID
              </label>
              <input
                type="text"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                style={{
                  width: '100%',
                  height: '44px',
                  background: isLight ? 'rgba(0, 0, 0, 0.03)' : 'rgba(255, 255, 255, 0.06)',
                  border: `1px solid ${isLight ? 'rgba(0, 0, 0, 0.12)' : 'rgba(255, 255, 255, 0.14)'}`,
                  borderRadius: '14px',
                  padding: '0 16px',
                  color: isLight ? '#1D1D1F' : '#F5F5F7',
                  fontSize: '14px',
                  fontWeight: 450,
                  outline: 'none',
                  boxSizing: 'border-box',
                  transition: 'border-color 0.18s ease, box-shadow 0.18s ease'
                }}
                onFocus={e => {
                  e.target.style.borderColor = isLight ? '#0071E3' : '#2997FF';
                  e.target.style.boxShadow = isLight 
                    ? '0 0 0 3.5px rgba(0, 113, 227, 0.25)' 
                    : '0 0 0 3.5px rgba(41, 151, 255, 0.3)';
                }}
                onBlur={e => {
                  e.target.style.borderColor = isLight ? 'rgba(0, 0, 0, 0.12)' : 'rgba(255, 255, 255, 0.14)';
                  e.target.style.boxShadow = 'none';
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: isLight ? '#1D1D1F' : '#F5F5F7', marginBottom: '7px', letterSpacing: '-0.01em' }}>
                Passkey / Master Secret
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  style={{
                    width: '100%',
                    height: '44px',
                    background: isLight ? 'rgba(0, 0, 0, 0.03)' : 'rgba(255, 255, 255, 0.06)',
                    border: `1px solid ${isLight ? 'rgba(0, 0, 0, 0.12)' : 'rgba(255, 255, 255, 0.14)'}`,
                    borderRadius: '14px',
                    padding: '0 44px 0 16px',
                    color: isLight ? '#1D1D1F' : '#F5F5F7',
                    fontSize: '14px',
                    fontWeight: 450,
                    outline: 'none',
                    boxSizing: 'border-box',
                    transition: 'border-color 0.18s ease, box-shadow 0.18s ease'
                  }}
                  onFocus={e => {
                    e.target.style.borderColor = isLight ? '#0071E3' : '#2997FF';
                    e.target.style.boxShadow = isLight 
                      ? '0 0 0 3.5px rgba(0, 113, 227, 0.25)' 
                      : '0 0 0 3.5px rgba(41, 151, 255, 0.3)';
                  }}
                  onBlur={e => {
                    e.target.style.borderColor = isLight ? 'rgba(0, 0, 0, 0.12)' : 'rgba(255, 255, 255, 0.14)';
                    e.target.style.boxShadow = 'none';
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '14px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'transparent',
                    border: 'none',
                    color: isLight ? '#86868B' : '#A1A1A6',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    padding: 0
                  }}
                  title={showPassword ? 'Hide password' : 'Show password'}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              style={{
                width: '100%',
                height: '44px',
                borderRadius: '9999px',
                fontSize: '14px',
                fontWeight: 600,
                letterSpacing: '-0.01em',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.75 : 1,
                background: isLight 
                  ? '#0071E3' 
                  : '#2997FF',
                color: isLight ? '#FFFFFF' : '#000000',
                border: 'none',
                boxShadow: isLight ? '0 4px 14px rgba(0, 113, 227, 0.28)' : '0 4px 18px rgba(41, 151, 255, 0.35)',
                marginTop: '6px',
                transition: 'transform 0.15s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.15s ease'
              }}
              onMouseDown={e => (e.currentTarget.style.transform = 'scale(0.98)')}
              onMouseUp={e => (e.currentTarget.style.transform = 'scale(1)')}
            >
              {isLoading ? 'Authenticating...' : 'Sign In to Workstation'}
            </button>
          </form>

          {/* Quick Evaluator Access & Demo Autofill */}
          <div
            style={{
              marginTop: '22px',
              padding: '14px 16px',
              backgroundColor: isLight ? 'rgba(0, 0, 0, 0.03)' : 'rgba(255, 255, 255, 0.04)',
              border: `1px solid ${autofillApplied ? (isLight ? '#0071E3' : '#2997FF') : (isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255, 255, 255, 0.10)')}`,
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              transition: 'all 0.2s ease'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <KeyRound size={16} style={{ color: isLight ? '#0071E3' : '#2997FF', flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: '10.5px', fontWeight: 700, color: isLight ? '#0071E3' : '#2997FF', letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>EVALUATOR DEMO ACCESS</span>
                  {autofillApplied && (
                    <span style={{ fontSize: '10.5px', color: '#10B981', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                      <CheckCircle2 size={12} /> Credentials Applied
                    </span>
                  )}
                </div>
                <div style={{ fontSize: '12px', color: isLight ? '#64748B' : '#94A3B8', fontFamily: 'SF Mono, monospace', marginTop: '2px' }}>
                  User: <strong style={{ color: isLight ? '#0F172A' : '#F8FAFC' }}>admin</strong> &nbsp;|&nbsp; Pass: <strong style={{ color: isLight ? '#0F172A' : '#F8FAFC' }}>admin</strong>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <button
                type="button"
                onClick={handleAutofillCredentials}
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  padding: '5px 12px',
                  borderRadius: '9999px',
                  backgroundColor: autofillApplied 
                    ? (isLight ? 'rgba(0, 113, 227, 0.12)' : 'rgba(41, 151, 255, 0.2)') 
                    : (isLight ? '#FFFFFF' : 'rgba(255, 255, 255, 0.08)'),
                  border: `1px solid ${autofillApplied ? (isLight ? '#0071E3' : '#2997FF') : (isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255, 255, 255, 0.15)')}`,
                  color: autofillApplied ? (isLight ? '#0071E3' : '#2997FF') : (isLight ? '#0F172A' : '#F8FAFC'),
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                title="Autofill username 'admin' and password 'admin'"
              >
                {autofillApplied ? '✔ Filled' : 'Autofill'}
              </button>

              <button
                type="button"
                onClick={handleQuickSignIn}
                disabled={isLoading}
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  padding: '5px 12px',
                  borderRadius: '9999px',
                  backgroundColor: isLight ? '#0071E3' : '#2997FF',
                  border: 'none',
                  color: isLight ? '#FFFFFF' : '#000000',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.15s ease'
                }}
                title="Autofill and sign in immediately with demo clearance"
              >
                Quick Enter →
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Auxiliary Links */}
        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12.5px', color: isLight ? '#86868B' : '#A1A1A6' }}>
          <div>
            Need clearance registration?{' '}
            <button
              onClick={onOpenSignUp}
              style={{ background: 'transparent', border: 'none', color: isLight ? '#0071E3' : '#2997FF', cursor: 'pointer', padding: 0, textDecoration: 'underline', fontWeight: 500 }}
            >
              Create workspace
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

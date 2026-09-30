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
}

export const MainLogin: React.FC<MainLoginProps> = ({
  onLoginSuccess,
  onOpenVerifyStandalone,
  onOpenSignUp
}) => {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === 'light';

  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setErrorMessage('Please enter both username and password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const session = await apiService.login({ email: username, password });
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

        {/* Login Box */}
        <div
          style={{
            background: isLight ? 'rgba(255, 255, 255, 0.92)' : 'rgba(18, 27, 35, 0.85)',
            backdropFilter: 'blur(36px) saturate(190%)',
            WebkitBackdropFilter: 'blur(36px) saturate(190%)',
            border: `1px solid ${isLight ? 'rgba(203, 213, 225, 0.95)' : 'rgba(255, 255, 255, 0.12)'}`,
            borderRadius: '16px',
            padding: '32px 28px',
            boxShadow: isLight 
              ? '0 1px 0 0 rgba(255, 255, 255, 1) inset, 0 24px 50px -12px rgba(15, 23, 42, 0.12), 0 4px 16px rgba(15, 23, 42, 0.04)' 
              : '0 1px 0 0 rgba(255, 255, 255, 0.08) inset, 0 32px 64px -16px rgba(0,0,0,0.8), 0 0 0 1px rgba(255, 255, 255, 0.06)'
          }}
        >
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {errorMessage && (
              <div
                style={{
                  padding: '10px 12px',
                  borderRadius: '6px',
                  background: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  color: '#EF4444',
                  fontSize: '12px'
                }}
              >
                {errorMessage}
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 650, color: isLight ? '#334155' : '#CBD5E1', marginBottom: '6px' }}>
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
                  height: '42px',
                  background: isLight ? '#FFFFFF' : 'rgba(11, 16, 21, 0.85)',
                  border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)'}`,
                  borderRadius: '8px',
                  padding: '0 14px',
                  color: isLight ? '#0F172A' : '#F8FAFC',
                  fontSize: '13.5px',
                  fontWeight: 500,
                  outline: 'none',
                  boxSizing: 'border-box',
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
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 650, color: isLight ? '#334155' : '#CBD5E1', marginBottom: '6px' }}>
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
                    height: '42px',
                    background: isLight ? '#FFFFFF' : 'rgba(11, 16, 21, 0.85)',
                    border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.14)'}`,
                    borderRadius: '8px',
                    padding: '0 40px 0 14px',
                    color: isLight ? '#0F172A' : '#F8FAFC',
                    fontSize: '13.5px',
                    fontWeight: 500,
                    outline: 'none',
                    boxSizing: 'border-box',
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
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'transparent',
                    border: 'none',
                    color: isLight ? '#64748B' : '#94A3B8',
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
                marginTop: '6px',
                transition: 'transform 0.15s ease, box-shadow 0.15s ease'
              }}
            >
              {isLoading ? 'Authenticating...' : 'Sign In to Workstation'}
            </button>
          </form>

          {/* Quick Evaluator Access */}
          <div
            style={{
              marginTop: '18px',
              paddingTop: '16px',
              borderTop: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255, 255, 255, 0.08)'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '12px'
            }}
          >
            <div>
              <span style={{ color: isLight ? '#64748B' : '#5D6675', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block' }}>
                EVALUATOR CLEARANCE
              </span>
              <span style={{ color: isLight ? '#334155' : '#9BA3AF', fontSize: '12px', fontFamily: 'monospace' }}>
                admin / admin
              </span>
            </div>

            <button
              type="button"
              onClick={handleAutofillCredentials}
              style={{
                background: isLight ? '#F1F5F9' : 'rgba(255, 255, 255, 0.06)',
                border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255, 255, 255, 0.1)'}`,
                color: isLight ? '#0F172A' : '#EDEDE8',
                borderRadius: '4px',
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 500,
                cursor: 'pointer'
              }}
            >
              Autofill
            </button>
          </div>
        </div>

        {/* Bottom Auxiliary Links */}
        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px', color: isLight ? '#64748B' : '#5D6675' }}>
          <div>
            Need clearance registration?{' '}
            <button
              onClick={onOpenSignUp}
              style={{ background: 'transparent', border: 'none', color: '#0284C7', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
            >
              Create workspace
            </button>
          </div>

        </div>
      </motion.div>
    </div>
  );
};

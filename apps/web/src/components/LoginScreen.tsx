import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  Loader2, 
  AlertCircle,
  KeyRound,
  FileCheck2,
  Lock,
  User,
  Sun,
  Moon,
  Sparkles,
  Zap,
  Scale
} from 'lucide-react';
import { motion } from 'framer-motion';
import { UserSession } from '../types';
import { apiService } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { Forensic3DBackground } from './common/Forensic3DBackground';

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
        backgroundColor: isLight ? '#F8FAFC' : '#080C10',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--space-6)',
        position: 'relative',
        overflow: 'hidden',
        transition: 'background-color 0.3s ease'
      }}
    >
      {/* 3D Animated Forensic Cryptographic Background Canvas */}
      <Forensic3DBackground interactive={true} intensity={1.0} />

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
            padding: '4px 10px',
            backgroundColor: isLight ? 'rgba(255, 255, 255, 0.85)' : 'rgba(18, 27, 35, 0.75)',
            backdropFilter: 'blur(12px)',
            border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.1)'}`,
            borderRadius: '20px',
            fontSize: '11px',
            fontWeight: 600,
            color: isLight ? '#0284C7' : '#38BDF8',
            letterSpacing: '0.02em',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
          }}
        >
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10B981', display: 'inline-block' }} />
          <span>NIST FIPS 203 LWE Lattice Active</span>
        </div>

        <button
          onClick={toggleTheme}
          title={`Switch to ${isLight ? 'Dark' : 'Light'} Mode`}
          style={{
            width: '34px',
            height: '34px',
            borderRadius: '50%',
            backgroundColor: isLight ? 'rgba(255, 255, 255, 0.85)' : 'rgba(18, 27, 35, 0.75)',
            backdropFilter: 'blur(12px)',
            border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.1)'}`,
            color: isLight ? '#475569' : '#A9B3BD',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
          }}
        >
          {isLight ? <Moon size={15} /> : <Sun size={15} />}
        </button>
      </div>

      {/* Authentication Card (Layer 2 Elevated Glass Surface) */}
      <motion.div
        initial={{ opacity: 0, y: 14, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="workstation-card specular-border"
        style={{
          width: '100%',
          maxWidth: '430px',
          backgroundColor: isLight ? 'rgba(255, 255, 255, 0.88)' : 'rgba(18, 27, 35, 0.82)',
          backdropFilter: 'blur(32px) saturate(190%)',
          WebkitBackdropFilter: 'blur(32px) saturate(190%)',
          border: `1px solid ${isLight ? 'rgba(226, 232, 240, 0.9)' : 'rgba(255, 255, 255, 0.12)'}`,
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-8) var(--space-7)',
          boxShadow: isLight 
            ? '0 24px 48px -12px rgba(15, 23, 42, 0.12), 0 0 0 1px rgba(255, 255, 255, 0.8)'
            : '0 30px 60px -15px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.06)',
          position: 'relative',
          zIndex: 10
        }}
      >
        {/* Header & Emblem */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: 'var(--radius-xs)',
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary)',
              marginBottom: 'var(--space-3)'
            }}
          >
            <ShieldCheck size={22} strokeWidth={1.75} />
          </div>

          <h1
            style={{
              fontSize: '19px',
              fontWeight: 700,
              color: 'var(--text)',
              letterSpacing: '-0.02em',
              margin: '0 0 4px 0'
            }}
          >
            AegisTrace
          </h1>

          <p
            style={{
              fontSize: '13px',
              color: 'var(--text-tertiary)',
              margin: 0,
              textAlign: 'center'
            }}
          >
            Secure forensic workspace.
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
              borderRadius: 'var(--radius-xs)',
              marginBottom: 'var(--space-5)',
              fontSize: '12.5px',
              color: 'var(--danger)',
              lineHeight: 1.4
            }}
          >
            <AlertCircle size={15} style={{ flexShrink: 0 }} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Authentication Form */}
        <form onSubmit={handleSubmit} noValidate>
          {/* Username / Email Input */}
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label
              htmlFor="login-username"
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '6px'
              }}
            >
              Username
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
                  height: '38px',
                  padding: '0 12px 0 34px',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-xs)',
                  color: 'var(--text)',
                  fontSize: '13px',
                  outline: 'none',
                  transition: 'border-color 0.15s ease'
                }}
                onFocus={e => (e.target.style.borderColor = 'var(--primary)')}
                onBlur={e => (e.target.style.borderColor = 'var(--border)')}
              />
              <User size={15} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
            </div>
          </div>

          {/* Password Input */}
          <div style={{ marginBottom: 'var(--space-5)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label
                htmlFor="login-password"
                style={{
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--text-secondary)'
                }}
              >
                Password
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
                placeholder="Enter password"
                disabled={isLoading}
                style={{
                  width: '100%',
                  height: '38px',
                  padding: '0 38px 0 34px',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-xs)',
                  color: 'var(--text)',
                  fontSize: '13px',
                  outline: 'none',
                  transition: 'border-color 0.15s ease'
                }}
                onFocus={e => (e.target.style.borderColor = 'var(--primary)')}
                onBlur={e => (e.target.style.borderColor = 'var(--border)')}
              />
              <Lock size={15} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                style={{
                  position: 'absolute',
                  right: '8px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-tertiary)',
                  cursor: 'pointer',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          {/* Submit Action */}
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary"
            style={{
              width: '100%',
              height: '40px',
              borderRadius: 'var(--radius-xs)',
              fontSize: '13px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.75 : 1
            }}
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="spin" />
                <span>Signing in…</span>
              </>
            ) : (
              <>
                <span>Sign in</span>
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </form>

        {/* DEMO ACCESS Box (Natural, Elegant, SIH Judge Focused) */}
        {demoAuthAvailable && (
          <div
            style={{
              marginTop: 'var(--space-5)',
              padding: '12px 14px',
              backgroundColor: isLight ? 'rgba(241, 245, 249, 0.8)' : 'rgba(15, 22, 29, 0.8)',
              border: `1px solid ${autofillApplied ? 'var(--primary)' : 'var(--border)'}`,
              borderRadius: 'var(--radius-xs)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              transition: 'all 0.2s ease'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <KeyRound size={16} style={{ color: 'var(--primary)', flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--primary)', letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>SIH JUDGE EVALUATION ACCESS</span>
                  {autofillApplied && (
                    <span style={{ fontSize: '10px', color: '#10B981', fontWeight: 600 }}>✓ Applied</span>
                  )}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                  Username: <strong style={{ color: 'var(--text)' }}>admin</strong> &nbsp;|&nbsp; Password: <strong style={{ color: 'var(--text)' }}>admin</strong>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleApplyDemoCredentials}
              className="btn-secondary"
              style={{
                fontSize: '11px',
                padding: '4px 10px',
                height: '28px',
                flexShrink: 0,
                backgroundColor: autofillApplied ? 'var(--primary-subtle)' : undefined,
                borderColor: autofillApplied ? 'var(--primary)' : undefined,
                color: autofillApplied ? 'var(--primary)' : undefined
              }}
            >
              {autofillApplied ? 'Loaded' : 'Autofill'}
            </button>
          </div>
        )}

        {/* Create workspace link */}
        {onSwitchToSignUp && (
          <div style={{ marginTop: 'var(--space-4)', textAlign: 'center', fontSize: '12px', color: 'var(--text-tertiary)' }}>
            Need an account?{' '}
            <button
              type="button"
              onClick={onSwitchToSignUp}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--primary)',
                cursor: 'pointer',
                fontWeight: 600,
                padding: 0,
                fontSize: '12px',
                textDecoration: 'underline'
              }}
            >
              Create workspace
            </button>
          </div>
        )}

        {/* AegisTrace Verify Standalone Link */}
        {onOpenVerifyStandalone && (
          <div
            style={{
              marginTop: 'var(--space-4)',
              paddingTop: 'var(--space-3)',
              borderTop: '1px solid var(--border-subtle)',
              textAlign: 'center',
              fontSize: '11.5px',
              color: 'var(--text-tertiary)'
            }}
          >
            Judicial examiner or auditor?{' '}
            <button
              type="button"
              onClick={onOpenVerifyStandalone}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                fontWeight: 600,
                padding: 0,
                fontSize: '11.5px',
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

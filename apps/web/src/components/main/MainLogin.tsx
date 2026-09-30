import React, { useState } from 'react';
import { Shield, ArrowRight, Eye, EyeOff, CheckCircle2, Lock, UserCheck, KeyRound } from 'lucide-react';
import { apiService } from '../../services/api';
import { UserSession } from '../../types';
import { useTheme } from '../../context/ThemeContext';

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
  const { theme } = useTheme();
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
        backgroundColor: isLight ? '#F8FAFC' : '#090C0F',
        color: isLight ? '#0F172A' : '#EDEDE8',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        fontFamily: "'Geist', system-ui, sans-serif",
        transition: 'background-color 0.2s ease, color 0.2s ease'
      }}
    >
      <div
        style={{
          width: '380px',
          maxWidth: '100%',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px'
        }}
      >
        {/* Brand Anchor */}
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #0284C7, #0369A1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '12px'
            }}
          >
            <Shield size={18} style={{ color: '#FFFFFF' }} />
          </div>
          <h1 style={{ fontSize: '20px', fontWeight: 600, margin: 0, letterSpacing: '-0.02em', color: isLight ? '#0F172A' : '#EDEDE8' }}>
            AegisTrace Enterprise Workstation
          </h1>
          <p style={{ fontSize: '13px', color: isLight ? '#475569' : '#9BA3AF', margin: '4px 0 0 0' }}>
            Post-quantum cryptographic document attribution.
          </p>
        </div>

        {/* Login Box */}
        <div
          style={{
            background: isLight ? '#FFFFFF' : '#12161B',
            border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(255, 255, 255, 0.08)'}`,
            borderRadius: '10px',
            padding: '24px',
            boxShadow: isLight ? '0 4px 20px rgba(0,0,0,0.06)' : '0 8px 32px rgba(0,0,0,0.4)'
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
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: isLight ? '#475569' : '#9BA3AF', marginBottom: '6px' }}>
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
                  background: isLight ? '#F8FAFC' : '#090C0F',
                  border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.12)'}`,
                  borderRadius: '6px',
                  padding: '9px 12px',
                  color: isLight ? '#0F172A' : '#EDEDE8',
                  fontSize: '13px',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: isLight ? '#475569' : '#9BA3AF', marginBottom: '6px' }}>
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
                    background: isLight ? '#F8FAFC' : '#090C0F',
                    border: `1px solid ${isLight ? '#CBD5E1' : 'rgba(255, 255, 255, 0.12)'}`,
                    borderRadius: '6px',
                    padding: '9px 36px 9px 12px',
                    color: isLight ? '#0F172A' : '#EDEDE8',
                    fontSize: '13px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'transparent',
                    border: 'none',
                    color: isLight ? '#64748B' : '#9BA3AF',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    padding: 0
                  }}
                  title={showPassword ? 'Hide password' : 'Show password'}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              style={{
                width: '100%',
                background: isLight ? '#0F172A' : '#EDEDE8',
                color: isLight ? '#FFFFFF' : '#090C0F',
                border: 'none',
                borderRadius: '6px',
                padding: '9px 16px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                marginTop: '4px',
                transition: 'background 0.15s ease'
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

          <div>
            Judicial examiner or auditor?{' '}
            <button
              onClick={onOpenVerifyStandalone}
              style={{ background: 'transparent', border: 'none', color: isLight ? '#0F172A' : '#EDEDE8', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
            >
              Open AegisTrace Verify (Zero-Server) →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

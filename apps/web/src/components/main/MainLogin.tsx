import React, { useState } from 'react';
import { Shield, ArrowRight, Eye, EyeOff, CheckCircle2 } from 'lucide-react';
import { apiService } from '../../services/api';
import { UserSession } from '../../types';

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

  const handleAutofillDemo = () => {
    setUsername('admin');
    setPassword('admin');
    setErrorMessage(null);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: '#090C0F',
        color: '#EDEDE8',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        fontFamily: "'Geist', system-ui, sans-serif"
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
              background: 'linear-gradient(135deg, #1E293B, #0F172A)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '12px'
            }}
          >
            <Shield size={18} style={{ color: '#EDEDE8' }} />
          </div>
          <h1 style={{ fontSize: '20px', fontWeight: 600, margin: 0, letterSpacing: '-0.02em', color: '#EDEDE8' }}>
            AegisTrace
          </h1>
          <p style={{ fontSize: '13px', color: '#9BA3AF', margin: '4px 0 0 0' }}>
            Secure forensic workstation.
          </p>
        </div>

        {/* Login Box */}
        <div
          style={{
            background: '#12161B',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '10px',
            padding: '24px'
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
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#9BA3AF', marginBottom: '6px' }}>
                Username
              </label>
              <input
                type="text"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                style={{
                  width: '100%',
                  background: '#090C0F',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: '6px',
                  padding: '9px 12px',
                  color: '#EDEDE8',
                  fontSize: '13px',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#9BA3AF', marginBottom: '6px' }}>
                Password
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
                    background: '#090C0F',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    borderRadius: '6px',
                    padding: '9px 36px 9px 12px',
                    color: '#EDEDE8',
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
                    color: '#9BA3AF',
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
                background: '#EDEDE8',
                color: '#090C0F',
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
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          {/* Discreet Demo Access */}
          <div
            style={{
              marginTop: '18px',
              paddingTop: '16px',
              borderTop: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '12px'
            }}
          >
            <div>
              <span style={{ color: '#5D6675', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block' }}>
                DEMO ACCESS
              </span>
              <span style={{ color: '#9BA3AF', fontSize: '12px' }}>
                admin / admin
              </span>
            </div>

            <button
              type="button"
              onClick={handleAutofillDemo}
              style={{
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#EDEDE8',
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
        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px', color: '#5D6675' }}>
          <div>
            Need an account?{' '}
            <button
              onClick={onOpenSignUp}
              style={{ background: 'transparent', border: 'none', color: '#9BA3AF', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
            >
              Create workspace
            </button>
          </div>

          <div>
            Judicial examiner or auditor?{' '}
            <button
              onClick={onOpenVerifyStandalone}
              style={{ background: 'transparent', border: 'none', color: '#EDEDE8', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
            >
              Open AegisTrace Verify (Zero-Server) →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

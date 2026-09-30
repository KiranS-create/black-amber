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
  Moon,
  Sparkles
} from 'lucide-react';
import { motion } from 'framer-motion';
import { apiService } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { Forensic3DBackground } from './common/Forensic3DBackground';

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
          <span>Post-Quantum Enclave Provisioning</span>
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

      {/* Account Creation Card */}
      <motion.div
        initial={{ opacity: 0, y: 14, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="workstation-card specular-border"
        style={{
          width: '100%',
          maxWidth: '460px',
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
            Create your forensic workspace.
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
              borderRadius: 'var(--radius-xs)',
              marginBottom: 'var(--space-5)',
              fontSize: '12.5px',
              color: 'var(--danger)',
              lineHeight: 1.45
            }}
          >
            <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: 600 }}>Provisioning Notice</div>
              <div>{errorMessage}</div>
            </div>
          </div>
        )}

        {/* Sign-Up Form */}
        <form onSubmit={handleSubmit} noValidate>
          {/* Name */}
          <div style={{ marginBottom: 'var(--space-3)' }}>
            <label
              htmlFor="signup-name"
              style={{
                display: 'block',
                fontSize: '11.5px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
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

          {/* Email */}
          <div style={{ marginBottom: 'var(--space-3)' }}>
            <label
              htmlFor="signup-email"
              style={{
                display: 'block',
                fontSize: '11.5px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '5px'
              }}
            >
              Official Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="signup-email"
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="officer@defense.org"
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
              <Mail size={15} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
            </div>
          </div>

          {/* Organization */}
          <div style={{ marginBottom: 'var(--space-3)' }}>
            <label
              htmlFor="signup-org"
              style={{
                display: 'block',
                fontSize: '11.5px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '5px'
              }}
            >
              Command / Organization (Optional)
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="signup-org"
                type="text"
                value={organization}
                onChange={e => setOrganization(e.target.value)}
                placeholder="Naval Cyber Command / Forensic Lab"
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
              <Building size={15} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
            </div>
          </div>

          {/* Password */}
          <div style={{ marginBottom: 'var(--space-3)' }}>
            <label
              htmlFor="signup-password"
              style={{
                display: 'block',
                fontSize: '11.5px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
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
                aria-label={showPassword ? 'Hide passphrase' : 'Show passphrase'}
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

          {/* Confirm Password */}
          <div style={{ marginBottom: 'var(--space-5)' }}>
            <label
              htmlFor="signup-confirm-password"
              style={{
                display: 'block',
                fontSize: '11.5px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
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
              <Lock size={15} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
            </div>
          </div>

          {/* Submit Button */}
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
                <span>Provisioning workspace…</span>
              </>
            ) : (
              <>
                <span>Create workspace</span>
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </form>

        {/* Already have an account */}
        <div style={{ marginTop: 'var(--space-5)', textAlign: 'center', fontSize: '12px', color: 'var(--text-tertiary)' }}>
          Already have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToSignIn}
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
            Sign in
          </button>
        </div>

        {/* Standalone Verify link */}
        {onOpenVerifyStandalone && (
          <div style={{ marginTop: 'var(--space-4)', paddingTop: 'var(--space-3)', borderTop: '1px solid var(--border-subtle)', textAlign: 'center', fontSize: '11px', color: 'var(--text-tertiary)' }}>
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
                fontSize: '11px',
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

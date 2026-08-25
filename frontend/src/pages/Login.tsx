import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { Shield, Eye, EyeOff, AlertCircle, WifiOff, Clock, Lock } from 'lucide-react';
import axios from 'axios';

type ErrorType = 'credentials' | 'unavailable' | 'timeout' | 'generic' | null;

interface ErrorConfig {
  icon: React.ReactNode;
  message: string;
}

function classifyError(err: unknown): ErrorType {
  if (axios.isAxiosError(err)) {
    if (err.response?.status === 401 || err.response?.status === 403) return 'credentials';
    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) return 'timeout';
    if (!err.response) return 'unavailable';
  }
  return 'generic';
}

const ERROR_CONFIGS: Record<Exclude<ErrorType, null>, ErrorConfig> = {
  credentials: {
    icon: <Lock size={14} />,
    message: 'Invalid badge ID or password.',
  },
  unavailable: {
    icon: <WifiOff size={14} />,
    message: 'Unable to connect to screening server. Please verify the backend is running.',
  },
  timeout: {
    icon: <Clock size={14} />,
    message: 'Request timed out. Please try again.',
  },
  generic: {
    icon: <AlertCircle size={14} />,
    message: 'Sign-in failed. Please try again.',
  },
};

// Animated security nodes for left panel
function SecurityIllustration() {
  return (
    <svg
      viewBox="0 0 300 280"
      style={{ width: '100%', maxWidth: 280, opacity: 0.85 }}
      aria-hidden="true"
    >
      {/* Central shield */}
      <defs>
        <radialGradient id="shieldGrad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="shieldFill" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3b82f6" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>
      </defs>

      {/* Outer rings */}
      <circle cx="150" cy="140" r="100" fill="none" stroke="rgba(59,130,246,0.12)" strokeWidth="1" />
      <circle cx="150" cy="140" r="75" fill="none" stroke="rgba(59,130,246,0.15)" strokeWidth="1" />
      <circle cx="150" cy="140" r="50" fill="url(#shieldGrad)" />

      {/* Document nodes */}
      {[
        { x: 90, y: 60, label: 'OCR' },
        { x: 210, y: 60, label: 'AI' },
        { x: 240, y: 160, label: 'Face' },
        { x: 60, y: 160, label: 'Risk' },
        { x: 150, y: 230, label: 'Done' },
      ].map((node, i) => (
        <g key={i}>
          <line x1={node.x} y1={node.y} x2="150" y2="140"
            stroke="rgba(59,130,246,0.18)" strokeWidth="1" strokeDasharray="4 3" />
          <circle cx={node.x} cy={node.y} r={18} fill="rgba(59,130,246,0.08)"
            stroke="rgba(59,130,246,0.25)" strokeWidth="1" />
          <text x={node.x} y={node.y + 4} textAnchor="middle"
            fontSize="8" fill="rgba(99,163,246,0.9)" fontWeight="600" fontFamily="Inter, sans-serif">
            {node.label}
          </text>
        </g>
      ))}

      {/* Shield */}
      <path
        d="M150 115 L175 128 L175 153 Q175 170 150 178 Q125 170 125 153 L125 128 Z"
        fill="url(#shieldFill)"
        opacity="0.9"
      />
      <path
        d="M143 149 L148 154 L160 140"
        stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none"
      />

      {/* Scanner beam animation */}
      <rect x="125" y="115" width="50" height="2" rx="1" fill="rgba(99,220,220,0.5)">
        <animateTransform
          attributeName="transform" type="translate"
          values="0,0; 0,65; 0,0" dur="3s" repeatCount="indefinite"
          calcMode="ease-in-out"
        />
        <animate attributeName="opacity" values="0;0.8;0" dur="3s" repeatCount="indefinite" />
      </rect>
    </svg>
  );
}

export default function Login() {
  const [badgeId, setBadgeId] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorType, setErrorType] = useState<ErrorType>(null);
  const [submitting, setSubmitting] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErrorType(null);
    setSubmitting(true);
    try {
      await login(badgeId, password);
      navigate('/dashboard');
    } catch (err) {
      setErrorType(classifyError(err));
    } finally {
      setSubmitting(false);
    }
  }

  function useDemoCredentials() {
    setBadgeId('OFFICER001');
    setPassword('Demo@123');
  }

  const errorConfig = errorType ? ERROR_CONFIGS[errorType] : null;

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        background: 'var(--bg-primary)',
        fontFamily: 'Inter, system-ui, sans-serif',
      }}
    >
      {/* ── Left Panel ──────────────────────────────────────── */}
      <div
        style={{
          flex: '1 1 50%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '3rem 2rem',
          background: 'linear-gradient(145deg, var(--bg-secondary) 0%, var(--bg-primary) 100%)',
          borderRight: '1px solid var(--border-default)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Subtle background pattern */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `radial-gradient(circle at 30% 30%, rgba(59,130,246,0.06) 0%, transparent 60%),
                              radial-gradient(circle at 70% 70%, rgba(99,102,241,0.05) 0%, transparent 60%)`,
          }}
        />

        <div style={{ position: 'relative', textAlign: 'center', maxWidth: 360 }}>
          {/* Brand */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                background: 'linear-gradient(135deg, var(--accent-primary), #6366f1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 20px rgba(59,130,246,0.3)',
              }}
            >
              <Shield size={22} color="white" />
            </div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.03em', color: 'var(--text-primary)', lineHeight: 1 }}>
                SentinelID
              </div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', letterSpacing: '0.04em', textTransform: 'uppercase', marginTop: '0.125rem' }}>
                Sashastra Seema Bal · MHA
              </div>
            </div>
          </div>

          {/* Tagline */}
          <div style={{ marginBottom: '2rem' }}>
            <div style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              AI-Powered Identity & Document Intelligence
            </div>
            <div style={{
              fontSize: '0.75rem',
              letterSpacing: '0.2em',
              textTransform: 'uppercase',
              color: 'var(--accent-primary)',
              fontWeight: 600,
              opacity: 0.8,
            }}>
              Detect · Verify · Assess · Decide
            </div>
          </div>

          {/* Illustration */}
          <SecurityIllustration />

          {/* SIH context */}
          <div style={{ marginTop: '1.5rem', padding: '0.625rem 1rem', borderRadius: 8, background: 'var(--accent-subtle)', border: '1px solid var(--border-accent)' }}>
            <div style={{ fontSize: '0.6875rem', color: 'var(--accent-primary)', letterSpacing: '0.03em' }}>
              SIH 2026 · Problem Statement ID: 26188
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.125rem' }}>
              Ministry of Home Affairs
            </div>
          </div>
        </div>
      </div>

      {/* ── Right Panel ─────────────────────────────────────── */}
      <div
        style={{
          flex: '0 0 420px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '3rem 2.5rem',
          background: 'var(--bg-primary)',
        }}
      >
        <div style={{ width: '100%', maxWidth: 360 }}>
          {/* Header */}
          <div style={{ marginBottom: '2rem' }}>
            <h1 style={{
              fontSize: '1.25rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: 0,
              marginBottom: '0.375rem',
              letterSpacing: '-0.02em',
            }}>
              Officer Sign-In
            </h1>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0 }}>
              Authorized personnel only
            </p>
          </div>

          {/* Login Card */}
          <div
            className="card-glass"
            style={{ padding: '1.75rem' }}
          >
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.125rem' }}>
              {/* Badge ID */}
              <div>
                <label
                  htmlFor="badgeId"
                  style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.375rem', letterSpacing: '0.02em' }}
                >
                  OFFICER ID / BADGE ID
                </label>
                <input
                  id="badgeId"
                  type="text"
                  value={badgeId}
                  onChange={(e) => setBadgeId(e.target.value)}
                  required
                  placeholder="e.g. OFFICER001"
                  className="input-field font-mono"
                  autoComplete="username"
                  autoCapitalize="characters"
                  style={{ textTransform: 'uppercase' }}
                />
              </div>

              {/* Password */}
              <div>
                <label
                  htmlFor="password"
                  style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.375rem', letterSpacing: '0.02em' }}
                >
                  PASSWORD
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder="Enter your password"
                    className="input-field"
                    autoComplete="current-password"
                    style={{ paddingRight: '2.5rem' }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: 'absolute',
                      right: '0.75rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      color: 'var(--text-muted)',
                      padding: 0,
                      display: 'flex',
                    }}
                    tabIndex={-1}
                    aria-label="Toggle password visibility"
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {/* Error Message */}
              {errorConfig && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.5rem',
                    padding: '0.625rem 0.75rem',
                    borderRadius: 8,
                    background: 'var(--risk-critical-bg)',
                    border: '1px solid rgba(239,68,68,0.25)',
                    color: 'var(--risk-critical)',
                    fontSize: '0.8125rem',
                  }}
                  role="alert"
                >
                  <span style={{ flexShrink: 0, marginTop: '0.125rem' }}>{errorConfig.icon}</span>
                  <span>{errorConfig.message}</span>
                </div>
              )}

              {/* Submit */}
              <button
                id="login-submit"
                type="submit"
                disabled={submitting}
                className="btn btn-primary btn-lg"
                style={{ width: '100%', marginTop: '0.25rem' }}
              >
                {submitting ? (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span
                      style={{
                        width: 14,
                        height: 14,
                        border: '2px solid rgba(255,255,255,0.3)',
                        borderTopColor: 'white',
                        borderRadius: '50%',
                        animation: 'spin 0.8s linear infinite',
                        display: 'inline-block',
                      }}
                    />
                    Authenticating…
                  </span>
                ) : (
                  <>
                    <Lock size={15} />
                    Secure Sign In
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Demo credentials helper */}
          <div
            style={{
              marginTop: '1.25rem',
              padding: '0.875rem 1rem',
              borderRadius: 10,
              background: 'var(--violet-subtle)',
              border: '1px dashed rgba(139,92,246,0.25)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: '#8b5cf6', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                Demo Officer
              </div>
              <button
                type="button"
                onClick={useDemoCredentials}
                style={{
                  fontSize: '0.6875rem',
                  color: '#8b5cf6',
                  background: 'rgba(139,92,246,0.12)',
                  border: '1px solid rgba(139,92,246,0.25)',
                  borderRadius: 6,
                  padding: '0.2rem 0.5rem',
                  cursor: 'pointer',
                  fontWeight: 500,
                }}
              >
                Use Demo Credentials
              </button>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Badge: OFFICER001 &nbsp;·&nbsp; Pass: Demo@123
            </div>
          </div>

          {/* Footer */}
          <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              Authorized Personnel Only
            </div>
            <div style={{ fontSize: '0.625rem', color: 'var(--text-muted)', opacity: 0.5, marginTop: '0.25rem' }}>
              All access is monitored and audited
            </div>
          </div>
        </div>
      </div>

      {/* Spinner keyframe */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

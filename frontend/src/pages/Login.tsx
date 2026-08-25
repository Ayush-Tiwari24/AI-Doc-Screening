import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export default function Login() {
  const [badgeId, setBadgeId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(badgeId, password);
      navigate('/');
    } catch {
      setError('Invalid badge ID or password.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-sm rounded-lg border border-border bg-surface p-8">
        <h1 className="mb-1 text-xl font-semibold text-text-primary">
          Document Screening System
        </h1>
        <p className="mb-6 text-sm text-text-secondary">Officer sign-in</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-text-secondary" htmlFor="badgeId">
              Badge ID
            </label>
            <input
              id="badgeId"
              type="text"
              value={badgeId}
              onChange={(e) => setBadgeId(e.target.value)}
              required
              className="w-full rounded border border-border bg-background px-3 py-2 text-text-primary outline-none focus:border-accent"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-text-secondary" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full rounded border border-border bg-background px-3 py-2 text-text-primary outline-none focus:border-accent"
            />
          </div>

          {error && <p className="text-sm text-risk-critical">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded bg-accent px-4 py-2 font-medium text-white transition hover:bg-blue-600 disabled:opacity-50"
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}

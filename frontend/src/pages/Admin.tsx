import { Shield, Users, AlertTriangle } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { Navigate } from 'react-router-dom';

export default function Admin() {
  const { user } = useAuthStore();

  if (user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="page-enter" style={{ maxWidth: 700, margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>Administration</h1>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>
          Officer management and system administration
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {[
          { icon: <Users size={20} />, title: 'Officer Management', desc: 'Manage officer accounts, badge IDs, roles, and checkpoint assignments.' },
          { icon: <Shield size={20} />, title: 'Audit Logs', desc: 'View complete audit trail of all screening sessions and officer actions.' },
          { icon: <AlertTriangle size={20} />, title: 'Blacklist Management', desc: 'Manage document numbers and identities on the screening watchlist.' },
        ].map((c) => (
          <div
            key={c.title}
            style={{
              padding: '1.25rem',
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: 12,
              display: 'flex',
              gap: '0.875rem',
            }}
          >
            <div style={{ width: 40, height: 40, borderRadius: 10, background: 'var(--accent-subtle)', border: '1px solid var(--border-accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-primary)', flexShrink: 0 }}>
              {c.icon}
            </div>
            <div>
              <div style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: '0.375rem' }}>{c.title}</div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{c.desc}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: '1.25rem', padding: '0.875rem 1rem', background: 'var(--risk-medium-bg)', border: '1px solid rgba(245,158,11,0.25)', borderRadius: 10, fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
        <AlertTriangle size={14} style={{ display: 'inline', marginRight: '0.375rem', color: 'var(--risk-medium)', verticalAlign: 'middle' }} />
        Admin panel endpoints are not yet exposed by the backend. These features are planned for production deployment.
      </div>
    </div>
  );
}

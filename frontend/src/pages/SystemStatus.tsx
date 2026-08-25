import { useEffect, useState } from 'react';
import api from '../lib/api';
import { CheckCircle, XCircle, Loader2, AlertTriangle, RefreshCw } from 'lucide-react';

interface ServiceStatus {
  name: string;
  description: string;
  status: 'operational' | 'degraded' | 'unavailable' | 'unknown' | 'checking';
  detail?: string;
  fromBackend?: boolean;
}

const BACKEND_SERVICES: Omit<ServiceStatus, 'status'>[] = [
  { name: 'API Server', description: 'FastAPI application', fromBackend: true },
  { name: 'PostgreSQL', description: 'Primary database', fromBackend: false, detail: 'Health not individually exposed by /health' },
  { name: 'Redis', description: 'Pub/sub broker + cache', fromBackend: false, detail: 'Health not individually exposed by /health' },
  { name: 'Celery Workers', description: 'Background task queue', fromBackend: false, detail: 'Health not individually exposed by /health' },
  { name: 'MinIO', description: 'Document object storage', fromBackend: false, detail: 'Health not individually exposed by /health' },
  { name: 'OCR Engine', description: 'Text extraction pipeline', fromBackend: false, detail: 'Configured — status not individually exposed' },
  { name: 'Face Engine', description: 'InsightFace biometrics', fromBackend: false, detail: 'Configured — status not individually exposed' },
];

type OverallHealth = 'checking' | 'ok' | 'degraded' | 'unavailable';

function StatusIcon({ status }: { status: ServiceStatus['status'] }) {
  switch (status) {
    case 'checking': return <Loader2 size={16} style={{ animation: 'spin 1s linear infinite', color: 'var(--text-muted)' }} />;
    case 'operational': return <CheckCircle size={16} style={{ color: 'var(--risk-low)' }} />;
    case 'unavailable': return <XCircle size={16} style={{ color: 'var(--risk-critical)' }} />;
    case 'degraded': return <AlertTriangle size={16} style={{ color: 'var(--risk-medium)' }} />;
    default: return <div style={{ width: 16, height: 16, borderRadius: '50%', background: 'var(--border-default)' }} />;
  }
}

function StatusLabel({ status }: { status: ServiceStatus['status'] }) {
  const map = {
    checking: { text: 'Checking…', color: 'var(--text-muted)' },
    operational: { text: 'Operational', color: 'var(--risk-low)' },
    unavailable: { text: 'Unavailable', color: 'var(--risk-critical)' },
    degraded: { text: 'Degraded', color: 'var(--risk-medium)' },
    unknown: { text: 'Unknown', color: 'var(--text-muted)' },
  };
  const cfg = map[status] ?? map.unknown;
  return <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: cfg.color }}>{cfg.text}</span>;
}

export default function SystemStatus() {
  const [services, setServices] = useState<ServiceStatus[]>(
    BACKEND_SERVICES.map((s) => ({ ...s, status: 'checking' as const }))
  );
  const [overall, setOverall] = useState<OverallHealth>('checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  async function checkHealth() {
    setOverall('checking');
    setServices((prev) => prev.map((s) => ({ ...s, status: 'checking' })));

    try {
      const res = await api.get('/health');
      const apiOk = res.data?.status === 'ok';

      setServices(
        BACKEND_SERVICES.map((s) => ({
          ...s,
          status: s.fromBackend
            ? (apiOk ? 'operational' : 'unavailable')
            : 'unknown',
        }))
      );
      setOverall(apiOk ? 'ok' : 'unavailable');
    } catch {
      setServices(
        BACKEND_SERVICES.map((s) => ({
          ...s,
          status: s.fromBackend ? 'unavailable' : 'unknown',
        }))
      );
      setOverall('unavailable');
    }

    setLastChecked(new Date());
  }

  useEffect(() => { checkHealth(); }, []);

  const overallColor =
    overall === 'ok' ? 'var(--risk-low)' :
    overall === 'unavailable' ? 'var(--risk-critical)' :
    overall === 'checking' ? 'var(--text-muted)' :
    'var(--risk-medium)';

  const overallText =
    overall === 'ok' ? 'All Systems Operational' :
    overall === 'unavailable' ? 'Backend Unreachable' :
    overall === 'checking' ? 'Checking Systems…' :
    'Degraded';

  return (
    <div className="page-enter" style={{ maxWidth: 700, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>System Status</h1>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>
            Backend service health
          </p>
        </div>
        <button onClick={checkHealth} className="btn btn-secondary btn-sm">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Overall status banner */}
      <div
        style={{
          padding: '1rem 1.25rem',
          borderRadius: 12,
          background: overallColor + '12',
          border: `1px solid ${overallColor}33`,
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          marginBottom: '1.25rem',
        }}
      >
        <div style={{ width: 14, height: 14, borderRadius: '50%', background: overallColor, flexShrink: 0, boxShadow: overall === 'ok' ? `0 0 8px ${overallColor}` : 'none' }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: overallColor }}>{overallText}</div>
          {lastChecked && (
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.125rem' }}>
              Last checked: {lastChecked.toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>

      {/* Services table */}
      <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, overflow: 'hidden' }}>
        {services.map((svc, i) => (
          <div
            key={svc.name}
            style={{
              padding: '0.875rem 1.125rem',
              borderBottom: i < services.length - 1 ? '1px solid var(--border-subtle)' : 'none',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.875rem',
            }}
          >
            <StatusIcon status={svc.status} />
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.125rem' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>{svc.name}</span>
                {!svc.fromBackend && svc.status === 'unknown' && (
                  <span className="badge badge-info" style={{ fontSize: '0.5rem' }}>Not individually exposed</span>
                )}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{svc.description}</div>
              {svc.detail && (
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.125rem', opacity: 0.75 }}>{svc.detail}</div>
              )}
            </div>
            <StatusLabel status={svc.status} />
          </div>
        ))}
      </div>

      {/* Notes */}
      <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 10, fontSize: '0.6875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
        <div style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Note</div>
        The <code style={{ fontFamily: 'var(--font-mono)', background: 'var(--bg-primary)', padding: '0.0625rem 0.375rem', borderRadius: 4 }}>GET /health</code> endpoint
        returns overall API health only. Individual service status for PostgreSQL, Redis, Celery, MinIO, and
        ML engines is not currently exposed. Extending <code style={{ fontFamily: 'var(--font-mono)', background: 'var(--bg-primary)', padding: '0.0625rem 0.375rem', borderRadius: 4 }}>/health</code> with
        sub-service probes is recommended for production.
      </div>
    </div>
  );
}

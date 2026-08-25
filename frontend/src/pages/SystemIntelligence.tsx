import { Brain, ArrowRight, Database, Cpu, Eye, BarChart3, Shield, Users, FileText, ScanFace } from 'lucide-react';

function ArchNode({ icon, label, active = false, demo = false }: { icon: React.ReactNode; label: string; active?: boolean; demo?: boolean }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '0.375rem',
      padding: '0.875rem',
      borderRadius: 10,
      border: demo
        ? '1px dashed rgba(139,92,246,0.35)'
        : active
          ? '1px solid var(--border-accent)'
          : '1px solid var(--border-default)',
      background: demo
        ? 'rgba(139,92,246,0.06)'
        : active
          ? 'var(--accent-subtle)'
          : 'var(--bg-elevated)',
      minWidth: 100,
    }}>
      <div style={{ color: demo ? '#8b5cf6' : active ? 'var(--accent-primary)' : 'var(--text-muted)' }}>
        {icon}
      </div>
      <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: demo ? '#8b5cf6' : active ? 'var(--accent-primary)' : 'var(--text-secondary)', textAlign: 'center' }}>
        {label}
      </div>
      {demo && <span className="badge badge-demo" style={{ fontSize: '0.5rem', padding: '0.0625rem 0.375rem' }}>DEMO</span>}
    </div>
  );
}

function FlowArrow({ label }: { label?: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.125rem', padding: '0 0.5rem' }}>
      <ArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
      {label && <span style={{ fontSize: '0.5625rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{label}</span>}
    </div>
  );
}

function PrincipleCard({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div style={{ padding: '1rem', background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 10, display: 'flex', gap: '0.875rem' }}>
      <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--accent-subtle)', border: '1px solid var(--border-accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'var(--accent-primary)' }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.25rem' }}>{title}</div>
        <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{desc}</div>
      </div>
    </div>
  );
}

export default function SystemIntelligence() {
  return (
    <div className="page-enter" style={{ maxWidth: 1000, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.5rem' }}>
          <Brain size={20} style={{ color: 'var(--accent-primary)' }} />
          <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>System Intelligence</h1>
        </div>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0 }}>
          Architecture, AI modules, and design principles of SentinelID
        </p>
      </div>

      {/* Pipeline Architecture */}
      <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 14, padding: '1.5rem', marginBottom: '1.25rem' }}>
        <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '1.25rem' }}>
          Verification Pipeline Architecture
        </div>
        <div style={{ overflowX: 'auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 0, flexWrap: 'nowrap', minWidth: 650, padding: '0.5rem 0' }}>
            <ArchNode icon={<FileText size={18} />} label="Document Input" active />
            <FlowArrow />
            <ArchNode icon={<Cpu size={18} />} label="OCR Engine" active />
            <FlowArrow />
            <ArchNode icon={<Eye size={18} />} label="Field Extraction" active />
            <FlowArrow />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <ArchNode icon={<Shield size={18} />} label="Validation" active />
              <ArchNode icon={<Database size={18} />} label="Tampering Detection" active />
              <ArchNode icon={<Database size={16} />} label="DigiLocker / Issuer Verify" demo />
            </div>
            <FlowArrow />
            <ArchNode icon={<ScanFace size={18} />} label="Face Verification" active />
            <FlowArrow />
            <ArchNode icon={<BarChart3 size={18} />} label="Risk Engine" active />
            <FlowArrow />
            <ArchNode icon={<Users size={18} />} label="Officer Decision" active />
          </div>
        </div>

        <div style={{
          marginTop: '1.25rem',
          padding: '0.625rem 0.875rem',
          background: 'rgba(139,92,246,0.06)',
          border: '1px dashed rgba(139,92,246,0.25)',
          borderRadius: 8,
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          lineHeight: 1.6,
        }}>
          <span style={{ color: '#8b5cf6', fontWeight: 600 }}>DigiLocker / Issuer Verification</span>
          {' '}is shown as a future integration branch. In this prototype, a sandbox simulation demonstrates how
          field-level comparison with an authoritative source would appear.
          Production integration would require authorized government APIs and compliance review.
        </div>
      </div>

      {/* AI Modules */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, padding: '1.25rem' }}>
          <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '1rem' }}>
            AI Modules
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {[
              { name: 'OCR Engine', desc: 'Text extraction + MRZ parsing from document images', tech: 'Tesseract / CV pipeline' },
              { name: 'Image Forensics', desc: 'ELA, metadata analysis, CNN classifier, photo-swap detection', tech: 'OpenCV + CNN' },
              { name: 'Face Verification', desc: 'Biometric comparison of document photo vs live capture', tech: 'InsightFace' },
              { name: 'Risk Scoring Engine', desc: 'Weighted factor aggregation with explainable breakdown', tech: 'Rules + ML hybrid' },
            ].map((m) => (
              <div key={m.name} style={{ display: 'flex', gap: '0.625rem', alignItems: 'flex-start' }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-primary)', marginTop: '0.375rem', flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>{m.name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.125rem' }}>{m.desc}</div>
                  <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.125rem', fontFamily: 'var(--font-mono)' }}>{m.tech}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, padding: '1.25rem' }}>
          <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '1rem' }}>
            Infrastructure Stack
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
            {[
              { layer: 'API', tech: 'FastAPI + PostgreSQL + Alembic' },
              { layer: 'Queue', tech: 'Celery + Redis broker' },
              { layer: 'Storage', tech: 'MinIO (S3-compatible object store)' },
              { layer: 'Real-time', tech: 'Redis pub/sub → WebSocket' },
              { layer: 'Auth', tech: 'JWT Bearer + refresh token rotation' },
              { layer: 'Frontend', tech: 'React + Vite + Zustand + Tailwind CSS v4' },
            ].map((r) => (
              <div key={r.layer} style={{ display: 'flex', gap: '0.75rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
                <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', width: 72, flexShrink: 0, letterSpacing: '0.04em', textTransform: 'uppercase', paddingTop: '0.0625rem' }}>{r.layer}</div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>{r.tech}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Design principles */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.875rem' }}>
          Security & Design Principles
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          <PrincipleCard icon={<Users size={16} />} title="Human-in-the-Loop" desc="AI provides analysis and risk scores; final pass/hold/escalate decisions are always made by a trained officer." />
          <PrincipleCard icon={<Eye size={16} />} title="Explainability" desc="Every risk score includes a ranked factor breakdown. No black-box decisions." />
          <PrincipleCard icon={<Database size={16} />} title="Auditability" desc="All officer actions and pipeline events are logged to an immutable audit trail." />
          <PrincipleCard icon={<Shield size={16} />} title="Privacy by Design" desc="Document images are stored on-premises in MinIO. No data leaves the SSB network." />
        </div>
      </div>

      {/* Prototype notice */}
      <div style={{
        padding: '1.125rem 1.25rem',
        background: 'var(--risk-medium-bg)',
        border: '1px solid rgba(245,158,11,0.25)',
        borderRadius: 12,
        fontSize: '0.8125rem',
        color: 'var(--text-secondary)',
        lineHeight: 1.7,
      }}>
        <div style={{ fontWeight: 700, color: 'var(--risk-medium)', marginBottom: '0.375rem' }}>Prototype Scope Notice</div>
        This SIH 2026 prototype uses synthetic and demo data for external authoritative source verification (DigiLocker sandbox).
        Production deployment would require: authorized government API access, compliance and security review, independent
        model validation, audited infrastructure, and integration with Ministry of Home Affairs approved data sources.
      </div>
    </div>
  );
}

import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import {
  PlusCircle, FileText, Cpu, ScanFace, AlertTriangle,
  FileCheck, ChevronRight, Play, FlaskConical
} from 'lucide-react';
import { DEMO_METRICS, DEMO_SCREENING_HISTORY, DEMO_SCENARIOS } from '../lib/demoData';
import { getRiskBadgeClass, getRiskLabel, getDocTypeLabel, formatDateTime } from '../lib/utils';
import RiskBadge from '../components/shared/RiskBadge';

const WORKFLOW_STEPS = [
  { icon: <FileText size={16} />, label: 'Upload Document', desc: 'Image or PDF' },
  { icon: <Cpu size={16} />, label: 'Extract Identity', desc: 'OCR + MRZ parse' },
  { icon: <FileCheck size={16} />, label: 'Analyze Integrity', desc: 'Validation + tampering' },
  { icon: <ScanFace size={16} />, label: 'Verify Face', desc: 'InsightFace biometric' },
  { icon: <AlertTriangle size={16} />, label: 'Risk Report', desc: 'Explainable AI score' },
];

const METRIC_CARDS = [
  { label: 'Screenings Today', value: DEMO_METRICS.screeningsToday, accent: 'var(--accent-primary)' },
  { label: 'Cleared', value: DEMO_METRICS.cleared, accent: 'var(--risk-low)' },
  { label: 'Flagged', value: DEMO_METRICS.flagged, accent: 'var(--risk-high)' },
  { label: 'Avg. Screening Time', value: DEMO_METRICS.avgTime, accent: 'var(--risk-medium)' },
];

function MetricCard({ label, value, accent }: { label: string; value: string; accent: string }) {
  return (
    <div
      style={{
        flex: '1 1 0',
        minWidth: 120,
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-default)',
        borderRadius: 10,
        padding: '1rem 1.125rem',
      }}
    >
      <div style={{ fontSize: '1.375rem', fontWeight: 700, color: accent, marginBottom: '0.25rem', letterSpacing: '-0.02em' }}>
        {value}
      </div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>
        {label}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [demoOpen, setDemoOpen] = React.useState(false);

  return (
    <div className="page-enter" style={{ maxWidth: 1100, margin: '0 auto' }}>
      {/* ── Header ──────────────────────────────────────────── */}
      <div style={{ marginBottom: '1.75rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            Screening Operations
          </h1>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>
            AI-assisted identity and document verification control centre
            {user && (
              <span style={{ color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                · Welcome, {user.name.split(' ')[0]}
              </span>
            )}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => setDemoOpen(!demoOpen)}
            className="btn btn-secondary btn-sm"
            title="Demo scenarios for jury presentation"
          >
            <FlaskConical size={14} />
            Demo Mode
          </button>
          <button
            id="start-screening-btn"
            onClick={() => navigate('/screening/new')}
            className="btn btn-primary"
          >
            <PlusCircle size={16} />
            Start New Screening
          </button>
        </div>
      </div>

      {/* ── Demo Mode Panel ─────────────────────────────────── */}
      {demoOpen && (
        <div
          style={{
            marginBottom: '1.5rem',
            padding: '1rem 1.25rem',
            background: 'var(--violet-subtle)',
            border: '1px dashed rgba(139,92,246,0.3)',
            borderRadius: 12,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.875rem' }}>
            <FlaskConical size={14} color="#8b5cf6" />
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#8b5cf6' }}>Demo Scenarios</span>
            <span className="badge badge-demo" style={{ fontSize: '0.6rem' }}>DEMO ONLY</span>
            <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              These visualize prototype capability — real screening uses the backend pipeline.
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.625rem' }}>
            {DEMO_SCENARIOS.map((s) => (
              <button
                key={s.id}
                onClick={() => navigate('/screening/new', { state: { demoScenario: s } })}
                style={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 8,
                  padding: '0.75rem',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                }}
                className="glass-hover"
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>{s.label}</span>
                  <RiskBadge level={s.simulatedRiskLevel} size="sm" />
                </div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                  {s.description}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Central Workflow Panel ───────────────────────────── */}
      <div
        style={{
          marginBottom: '1.5rem',
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-default)',
          borderRadius: 14,
          padding: '1.5rem',
        }}
      >
        <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '1.25rem' }}>
          Verification Pipeline
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0',
            flexWrap: 'wrap',
            rowGap: '0.75rem',
          }}
        >
          {WORKFLOW_STEPS.map((step, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', flex: '1 1 0' }}>
              <div
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.875rem 0.625rem',
                  background: 'var(--bg-glass)',
                  borderRadius: 10,
                  border: '1px solid var(--border-default)',
                  transition: 'all var(--transition-base)',
                  cursor: 'default',
                }}
                className="glass-hover"
              >
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: '50%',
                    background: 'var(--accent-subtle)',
                    border: '1px solid var(--border-accent)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--accent-primary)',
                  }}
                >
                  {step.icon}
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.125rem' }}>
                    {step.label}
                  </div>
                  <div style={{ fontSize: '0.6625rem', color: 'var(--text-muted)' }}>
                    {step.desc}
                  </div>
                </div>
              </div>
              {i < WORKFLOW_STEPS.length - 1 && (
                <ChevronRight size={16} style={{ color: 'var(--text-muted)', flexShrink: 0, margin: '0 0.25rem' }} />
              )}
            </div>
          ))}
        </div>

        <div style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'center' }}>
          <button
            onClick={() => navigate('/screening/new')}
            className="btn btn-primary"
          >
            <Play size={15} />
            Begin Screening
          </button>
        </div>
      </div>

      {/* ── Metric Cards ──────────────────────────────────── */}
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        {METRIC_CARDS.map((m) => (
          <MetricCard key={m.label} {...m} />
        ))}
      </div>
      <div
        style={{
          fontSize: '0.6875rem',
          color: 'var(--text-muted)',
          marginTop: '-1rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.375rem',
        }}
      >
        <span style={{ color: 'var(--risk-medium)' }}>ℹ</span>
        {DEMO_METRICS.note}
      </div>

      {/* ── Recent Screenings ─────────────────────────────── */}
      <div
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-default)',
          borderRadius: 14,
          overflow: 'hidden',
        }}
      >
        <div style={{
          padding: '1rem 1.25rem',
          borderBottom: '1px solid var(--border-default)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            Recent Screenings
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="badge badge-demo" style={{ fontSize: '0.6rem' }}>Demo Data</span>
            <button
              onClick={() => navigate('/history')}
              className="btn btn-ghost btn-sm"
              style={{ fontSize: '0.75rem' }}
            >
              View All →
            </button>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Document Type</th>
                <th>Date &amp; Time</th>
                <th>Risk Level</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {DEMO_SCREENING_HISTORY.slice(0, 5).map((row) => (
                <tr key={row.id}>
                  <td>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text-primary)' }}>
                      {row.travelerRef}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>
                    {getDocTypeLabel(row.docType as never)}
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    {formatDateTime(row.date)}
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <RiskBadge level={row.riskLevel} />
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {row.riskScore}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${row.status === 'complete' ? 'badge-success' : 'badge-warning'}`}>
                      {row.status}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-ghost btn-sm" style={{ color: 'var(--accent-primary)', fontSize: '0.75rem' }}>
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Need React for useState
import React from 'react';
void getRiskBadgeClass; void getRiskLabel;

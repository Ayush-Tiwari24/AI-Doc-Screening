import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useScreeningStore } from '../store/screeningStore';
import api from '../lib/api';
import type { RiskReportOut } from '../types/api';
import { getRiskColor, formatDateTime, shortId } from '../lib/utils';
import RiskBadge from '../components/shared/RiskBadge';
import DigiLockerVerificationCard from '../components/digilocker/DigiLockerVerificationCard';
import { DIGILOCKER_MATCH_DEMO } from '../lib/demoData';
import {
  AlertTriangle, CheckCircle, XCircle, Loader2,
  ChevronDown, ChevronUp, ExternalLink, Shield
} from 'lucide-react';

// ─── Risk Gauge ────────────────────────────────────────────────
function RiskGauge({ score, level }: { score: number; level: string }) {
  const clamped = Math.max(0, Math.min(100, score));
  const radius = 70;
  const circumference = Math.PI * radius; // semi-circle
  const strokeDashoffset = circumference - (clamped / 100) * circumference;
  const color = getRiskColor(level);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
      <div style={{ position: 'relative' }}>
        <svg width="200" height="110" viewBox="0 0 200 110">
          {/* Track */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="var(--border-default)"
            strokeWidth="12"
            strokeLinecap="round"
          />
          {/* Fill */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            style={{
              transition: 'stroke-dashoffset 1.5s cubic-bezier(0.25,0.46,0.45,0.94), stroke 0.5s',
              filter: `drop-shadow(0 0 6px ${color}66)`,
            }}
          />
          {/* Score text */}
          <text x="100" y="88" textAnchor="middle" fontSize="28" fontWeight="800"
            fill={color} fontFamily="Inter, sans-serif" letterSpacing="-1">
            {Math.round(clamped)}
          </text>
          <text x="100" y="104" textAnchor="middle" fontSize="9" fill="var(--text-muted)"
            fontFamily="Inter, sans-serif" fontWeight="600" letterSpacing="1">
            RISK SCORE
          </text>
        </svg>
      </div>
      <div style={{ textAlign: 'center' }}>
        <RiskBadge level={level} size="lg" />
      </div>
    </div>
  );
}

// ─── Breakdown Item ────────────────────────────────────────────
function BreakdownItem({ factor, points, isHighest }: { factor: string; points: number; isHighest: boolean }) {
  const maxBar = 30;
  const barWidth = Math.min(100, (Math.abs(points) / maxBar) * 100);

  return (
    <div style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', marginBottom: '0.25rem' }}>
          <span style={{ fontSize: '0.8125rem', fontWeight: isHighest ? 600 : 400, color: 'var(--text-primary)' }}>
            {factor.replace(/_/g, ' ')}
          </span>
          {isHighest && <span className="badge badge-critical" style={{ fontSize: '0.5rem' }}>HIGHEST</span>}
        </div>
        <div className="progress-bar" style={{ height: 3 }}>
          <div className="progress-fill" style={{
            width: `${barWidth}%`,
            background: points > 15 ? 'var(--risk-critical)' : points > 8 ? 'var(--risk-high)' : points > 3 ? 'var(--risk-medium)' : 'var(--risk-low)',
          }} />
        </div>
      </div>
      <div style={{
        fontSize: '0.875rem',
        fontWeight: 700,
        fontFamily: 'var(--font-mono)',
        color: points > 10 ? 'var(--risk-critical)' : points > 5 ? 'var(--risk-medium)' : 'var(--text-secondary)',
        flexShrink: 0,
        minWidth: 36,
        textAlign: 'right',
      }}>
        +{points.toFixed(1)}
      </div>
    </div>
  );
}

// ─── Decision Panel ────────────────────────────────────────────
type LocalDecision = 'clear' | 'review' | 'escalate' | null;

function DecisionPanel({ riskLevel }: { riskLevel: string }) {
  const [decision, setDecision] = useState<LocalDecision>(null);

  return (
    <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, padding: '1.25rem' }}>
      <div style={{ marginBottom: '0.875rem' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 700, margin: 0, marginBottom: '0.25rem' }}>Officer Decision</h3>
        <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
          Human-in-the-loop — final decision rests with the officer
        </div>
      </div>

      {decision && (
        <div style={{
          marginBottom: '0.875rem',
          padding: '0.625rem 0.875rem',
          borderRadius: 8,
          background: decision === 'clear' ? 'var(--risk-low-bg)' : decision === 'review' ? 'var(--risk-medium-bg)' : 'var(--risk-critical-bg)',
          border: `1px solid ${decision === 'clear' ? 'rgba(16,185,129,0.25)' : decision === 'review' ? 'rgba(245,158,11,0.25)' : 'rgba(239,68,68,0.25)'}`,
          fontSize: '0.8125rem',
          color: decision === 'clear' ? 'var(--risk-low)' : decision === 'review' ? 'var(--risk-medium)' : 'var(--risk-critical)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          {decision === 'clear' ? <CheckCircle size={15} /> : decision === 'review' ? <AlertTriangle size={15} /> : <XCircle size={15} />}
          Decision recorded: {decision === 'clear' ? 'Cleared' : decision === 'review' ? 'Secondary Review' : 'Escalated'}
          <span style={{ marginLeft: 'auto', fontSize: '0.6875rem', opacity: 0.7 }}>Frontend demo — backend decision endpoint pending</span>
        </div>
      )}

      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button
          onClick={() => setDecision('clear')}
          className="btn btn-sm"
          style={{
            flex: 1,
            background: decision === 'clear' ? 'var(--risk-low)' : 'var(--risk-low-bg)',
            border: '1px solid rgba(16,185,129,0.3)',
            color: decision === 'clear' ? 'white' : 'var(--risk-low)',
          }}
        >
          <CheckCircle size={13} /> Clear
        </button>
        <button
          onClick={() => setDecision('review')}
          className="btn btn-sm"
          style={{
            flex: 1,
            background: decision === 'review' ? 'var(--risk-medium)' : 'var(--risk-medium-bg)',
            border: '1px solid rgba(245,158,11,0.3)',
            color: decision === 'review' ? 'white' : 'var(--risk-medium)',
          }}
        >
          <AlertTriangle size={13} /> Secondary Review
        </button>
        <button
          onClick={() => setDecision('escalate')}
          className="btn btn-sm"
          style={{
            flex: 1,
            background: decision === 'escalate' ? 'var(--risk-critical)' : 'var(--risk-critical-bg)',
            border: '1px solid rgba(239,68,68,0.3)',
            color: decision === 'escalate' ? 'white' : 'var(--risk-critical)',
          }}
        >
          <XCircle size={13} /> Escalate
        </button>
      </div>

      {riskLevel === 'critical' && !decision && (
        <div style={{ marginTop: '0.625rem', fontSize: '0.6875rem', color: 'var(--risk-critical)', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <AlertTriangle size={11} />
          Critical risk detected — immediate action recommended
        </div>
      )}
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────
export default function RiskReport() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const store = useScreeningStore();

  const [report, setReport] = useState<RiskReportOut | null>(store.riskReport);
  const [loading, setLoading] = useState(!store.riskReport);
  const [error, setError] = useState<string | null>(null);
  const [breakdownExpanded, setBreakdownExpanded] = useState(true);

  useEffect(() => {
    if (report || !sessionId) return;
    async function load() {
      setLoading(true);
      try {
        const res = await api.get<RiskReportOut>(`/sessions/${sessionId}/risk-report`);
        setReport(res.data);
        store.setRiskReport(res.data);
      } catch (e) {
        const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        setError(msg ?? 'Risk report unavailable. The session may still be processing.');
      } finally {
        setLoading(false);
      }
    }
    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 300, gap: '0.75rem', color: 'var(--text-secondary)' }}>
        <Loader2 size={22} style={{ animation: 'spin 1s linear infinite', color: 'var(--accent-primary)' }} />
        <div>Loading risk report…</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Session {shortId(sessionId ?? '')}</div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div style={{ maxWidth: 500, margin: '4rem auto', textAlign: 'center' }}>
        <AlertTriangle size={28} style={{ color: 'var(--risk-medium)', marginBottom: '0.75rem' }} />
        <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>
          {error ?? 'Risk report not yet available'}
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', marginBottom: '1.25rem' }}>
          The screening pipeline may still be processing. Check system status or retry.
        </p>
        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
          <button onClick={() => { setError(null); setLoading(true); }} className="btn btn-secondary btn-sm">Retry</button>
          <button onClick={() => navigate(`/screening/${sessionId}/processing`)} className="btn btn-primary btn-sm">Back to Pipeline</button>
        </div>
      </div>
    );
  }

  const sortedBreakdown = [...report.breakdown].sort((a, b) => b.points - a.points);
  const highestFactor = sortedBreakdown[0]?.factor;

  return (
    <div className="page-enter" style={{ maxWidth: 1000, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>Risk Report</h1>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>
            Session {shortId(sessionId ?? '')} · {formatDateTime(new Date().toISOString())}
          </p>
        </div>
        <button onClick={() => navigate('/history')} className="btn btn-ghost btn-sm">
          ← All Sessions
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '1.25rem', alignItems: 'start' }}>
        {/* ── Left: Score ──────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card" style={{ textAlign: 'center', padding: '1.5rem' }}>
            <RiskGauge score={report.risk_score} level={report.risk_level} />
            {report.hard_override && (
              <div style={{ marginTop: '0.875rem', padding: '0.5rem 0.625rem', background: 'var(--risk-critical-bg)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 8, fontSize: '0.6875rem', color: 'var(--risk-critical)', display: 'flex', alignItems: 'center', gap: '0.375rem', justifyContent: 'center' }}>
                <Shield size={12} /> Hard override applied
              </div>
            )}
          </div>

          {/* Recommended action */}
          <div style={{
            padding: '0.875rem',
            background: getRiskColor(report.risk_level) + '14',
            border: `1px solid ${getRiskColor(report.risk_level)}33`,
            borderRadius: 10,
          }}>
            <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.375rem', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              Recommended Action
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: getRiskColor(report.risk_level) }}>
              {report.risk_level === 'low' && 'Proceed — clear for passage'}
              {report.risk_level === 'medium' && 'Secondary review recommended'}
              {report.risk_level === 'high' && 'Hold — escalate to supervisor'}
              {report.risk_level === 'critical' && 'Detain — immediate escalation'}
            </div>
          </div>

          {/* Decision panel */}
          <DecisionPanel riskLevel={report.risk_level} />
        </div>

        {/* ── Right: Details ──────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Why this score */}
          <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, overflow: 'hidden' }}>
            <button
              onClick={() => setBreakdownExpanded(!breakdownExpanded)}
              style={{
                width: '100%',
                padding: '0.875rem 1rem',
                background: 'none',
                border: 'none',
                borderBottom: breakdownExpanded ? '1px solid var(--border-default)' : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
                color: 'var(--text-primary)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 700 }}>Why This Score</span>
                <span className="badge badge-info" style={{ fontSize: '0.5625rem' }}>{report.breakdown.length} factors</span>
              </div>
              {breakdownExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>

            {breakdownExpanded && (
              <div style={{ padding: '0.625rem 1rem' }}>
                {sortedBreakdown.map((item) => (
                  <BreakdownItem
                    key={item.factor}
                    factor={item.factor}
                    points={item.points}
                    isHighest={item.factor === highestFactor}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Stored extracted data summary */}
          {store.extractedData && (
            <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, overflow: 'hidden' }}>
              <div style={{ padding: '0.875rem 1rem', borderBottom: '1px solid var(--border-default)' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 700 }}>Identity Summary</span>
              </div>
              <div style={{ padding: '0.875rem 1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem 1.5rem' }}>
                {[
                  { label: 'Name', value: store.extractedData.full_name },
                  { label: 'Document No.', value: store.extractedData.doc_number },
                  { label: 'Nationality', value: store.extractedData.nationality },
                  { label: 'Date of Birth', value: store.extractedData.dob?.split('T')[0] },
                ].map((f) => f.value && (
                  <div key={f.label}>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' }}>{f.label}</div>
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', marginTop: '0.125rem' }}>{f.value}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Face verification summary */}
          {store.faceVerification && (
            <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, overflow: 'hidden' }}>
              <div style={{ padding: '0.875rem 1rem', borderBottom: '1px solid var(--border-default)' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 700 }}>Face Verification</span>
              </div>
              <div style={{ padding: '0.875rem 1rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                <div>
                  <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Result</div>
                  <span className={`badge ${store.faceVerification.match ? 'badge-success' : 'badge-critical'}`}>
                    {store.faceVerification.match ? 'Match' : 'Mismatch'}
                  </span>
                </div>
                <div>
                  <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Similarity</div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>
                    {store.faceVerification.similarity_score !== null ? `${Math.round((store.faceVerification.similarity_score ?? 0) * 100)}%` : '—'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* DigiLocker Demo */}
          <DigiLockerVerificationCard record={DIGILOCKER_MATCH_DEMO} />

          {/* Nav links */}
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button onClick={() => navigate(`/screening/${sessionId}/analysis`)} className="btn btn-ghost btn-sm">
              <ExternalLink size={13} /> Document Analysis
            </button>
            <button onClick={() => navigate(`/screening/${sessionId}/face`)} className="btn btn-ghost btn-sm">
              <ExternalLink size={13} /> Face Verification
            </button>
            <button onClick={() => navigate('/screening/new')} className="btn btn-secondary btn-sm" style={{ marginLeft: 'auto' }}>
              New Screening
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

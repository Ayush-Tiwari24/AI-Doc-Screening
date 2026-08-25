import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useScreeningStore } from '../store/screeningStore';
import { ScreeningWebSocket } from '../lib/websocket';
import type { SessionStatus } from '../types/api';
import { getStatusLabel } from '../lib/utils';
import {
  CheckCircle, Loader2, AlertCircle, XCircle,
  FileText, Cpu, ShieldCheck, ScanFace, BarChart3, ArrowRight
} from 'lucide-react';

const PIPELINE_STAGES: {
  id: string;
  label: string;
  detail: string;
  icon: React.ReactNode;
  activeStatuses: SessionStatus[];
  completeStatuses: SessionStatus[];
}[] = [
  {
    id: 'upload',
    label: 'Document Received',
    detail: 'Stored securely in MinIO',
    icon: <FileText size={18} />,
    activeStatuses: ['pending'],
    completeStatuses: ['processing', 'awaiting_face', 'scored', 'complete'],
  },
  {
    id: 'ocr',
    label: 'OCR Extraction',
    detail: 'Reading identity fields & MRZ',
    icon: <Cpu size={18} />,
    activeStatuses: ['processing'],
    completeStatuses: ['awaiting_face', 'scored', 'complete'],
  },
  {
    id: 'validate',
    label: 'Validation & Tampering Detection',
    detail: 'ELA · Metadata · CNN · Photo-swap',
    icon: <ShieldCheck size={18} />,
    activeStatuses: ['processing'],
    completeStatuses: ['awaiting_face', 'scored', 'complete'],
  },
  {
    id: 'face',
    label: 'Face Verification',
    detail: 'InsightFace biometric comparison',
    icon: <ScanFace size={18} />,
    activeStatuses: ['awaiting_face'],
    completeStatuses: ['scored', 'complete'],
  },
  {
    id: 'risk',
    label: 'Risk Assessment',
    detail: 'Explainable AI risk scoring',
    icon: <BarChart3 size={18} />,
    activeStatuses: ['scored'],
    completeStatuses: ['complete'],
  },
];

type StageState = 'waiting' | 'active' | 'complete' | 'failed';

function getStageState(stage: typeof PIPELINE_STAGES[0], status: SessionStatus | null, failed: boolean): StageState {
  if (failed) {
    if (stage.activeStatuses.includes(status ?? 'pending' as SessionStatus)) return 'failed';
  }
  if (status && stage.completeStatuses.includes(status)) return 'complete';
  if (status && stage.activeStatuses.includes(status)) return 'active';
  return 'waiting';
}

const STAGE_ICONS: Record<StageState, React.ReactNode> = {
  waiting: null,
  active: <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} />,
  complete: <CheckCircle size={15} />,
  failed: <XCircle size={15} />,
};

const STAGE_COLORS: Record<StageState, string> = {
  waiting: 'var(--border-default)',
  active: 'var(--accent-primary)',
  complete: 'var(--risk-low)',
  failed: 'var(--risk-critical)',
};

export default function Processing() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { setStatus, status: storedStatus } = useScreeningStore();
  const [status, setLocalStatus] = useState<SessionStatus | null>(storedStatus ?? 'pending');
  const [failed, setFailed] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<ScreeningWebSocket | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    const ws = new ScreeningWebSocket({
      sessionId,
      onConnected: () => setWsConnected(true),
      onStatus: (s) => {
        setLocalStatus(s);
        setStatus(s);

        if (s === 'awaiting_face') {
          navigate(`/screening/${sessionId}/face`);
        } else if (s === 'complete') {
          navigate(`/screening/${sessionId}/report`);
        } else if (s === 'failed') {
          setFailed(true);
        }
      },
      onError: () => setWsConnected(false),
      onClose: () => setWsConnected(false),
    });

    ws.connect();
    wsRef.current = ws;

    return () => ws.disconnect();
  }, [sessionId]);

  const isFailed = failed || status === 'failed';
  const isComplete = status === 'complete';

  return (
    <div
      className="page-enter"
      style={{
        maxWidth: 600,
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, letterSpacing: '-0.01em' }}>
          Screening in Progress
        </h1>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.375rem 0 0' }}>
          Session {sessionId?.slice(0, 8).toUpperCase()}
        </p>
      </div>

      {/* WebSocket status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', fontSize: '0.75rem', color: wsConnected ? 'var(--risk-low)' : 'var(--text-muted)' }}>
        <span
          style={{
            width: 7, height: 7, borderRadius: '50%',
            background: wsConnected ? 'var(--risk-low)' : 'var(--text-muted)',
            boxShadow: wsConnected ? '0 0 6px var(--risk-low)' : 'none',
          }}
        />
        {wsConnected ? 'Live pipeline connected' : 'Connecting to pipeline…'}
      </div>

      {/* Pipeline */}
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '2rem' }}>
        {PIPELINE_STAGES.map((stage, i) => {
          const state = getStageState(stage, status, isFailed);
          const color = STAGE_COLORS[state];

          return (
            <div key={stage.id}>
              <div
                className={`pipeline-step${state === 'active' ? ' active' : state === 'complete' ? ' complete' : state === 'failed' ? ' failed' : ''}`}
                style={{ borderColor: color, position: 'relative', overflow: 'hidden' }}
              >
                {/* Scanner beam on active */}
                {state === 'active' && <div className="scanner-beam" />}

                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: 8,
                    background: state === 'waiting' ? 'var(--bg-elevated)' : state === 'active' ? 'var(--accent-subtle)' : state === 'complete' ? 'var(--risk-low-bg)' : 'var(--risk-critical-bg)',
                    border: `1px solid ${color}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: color,
                    flexShrink: 0,
                    transition: 'all 0.4s',
                  }}
                >
                  {stage.icon}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.875rem', fontWeight: 600, color: state === 'waiting' ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                    {stage.label}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {stage.detail}
                  </div>
                </div>

                <div style={{ color, flexShrink: 0 }}>
                  {STAGE_ICONS[state]}
                </div>
              </div>

              {i < PIPELINE_STAGES.length - 1 && (
                <div style={{ display: 'flex', justifyContent: 'center', margin: '0.125rem 0' }}>
                  <div style={{ width: 2, height: 16, background: 'var(--border-default)', borderRadius: 1 }} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Status message */}
      {!isFailed && !isComplete && (
        <div style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>
          <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>
            {getStatusLabel(status)}
          </span>
          <span style={{ color: 'var(--text-muted)', marginLeft: '0.375rem' }}>
            — please wait, do not close this tab
          </span>
        </div>
      )}

      {/* Failed state */}
      {isFailed && (
        <div style={{ textAlign: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', color: 'var(--risk-critical)', marginBottom: '1rem' }}>
            <AlertCircle size={18} />
            <span style={{ fontSize: '0.9375rem', fontWeight: 600 }}>Pipeline Failed</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', marginBottom: '1.25rem' }}>
            The automated screening pipeline encountered an error. You may retry or escalate for manual review.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
            <button
              onClick={() => navigate('/screening/new')}
              className="btn btn-secondary"
            >
              New Screening
            </button>
            <button
              onClick={() => navigate(`/screening/${sessionId}/analysis`)}
              className="btn btn-primary"
            >
              View Partial Results <ArrowRight size={15} />
            </button>
          </div>
        </div>
      )}

      {/* Complete redirect note */}
      {isComplete && (
        <div style={{ textAlign: 'center', color: 'var(--risk-low)' }}>
          <CheckCircle size={20} />
          <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>Complete — redirecting to risk report…</div>
        </div>
      )}

      {/* Manual nav links */}
      {!isFailed && status !== 'pending' && (
        <div style={{ marginTop: '2rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          <button
            onClick={() => navigate(`/screening/${sessionId}/analysis`)}
            className="btn btn-ghost btn-sm"
            style={{ fontSize: '0.75rem' }}
          >
            View Document Analysis
          </button>
          {(status === 'awaiting_face' || status === 'scored' || status === 'complete') && (
            <button
              onClick={() => navigate(`/screening/${sessionId}/face`)}
              className="btn btn-ghost btn-sm"
              style={{ fontSize: '0.75rem' }}
            >
              Face Verification →
            </button>
          )}
        </div>
      )}
    </div>
  );
}

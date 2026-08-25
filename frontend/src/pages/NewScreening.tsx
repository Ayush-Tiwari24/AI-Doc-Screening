import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScreeningStore } from '../store/screeningStore';
import api from '../lib/api';
import type { DocType } from '../types/api';
import { getDocTypeLabel, formatFileSize } from '../lib/utils';
import { showToast } from '../components/shared/Toast';
import {
  FileText, Upload, ChevronRight, CheckCircle,
  AlertCircle, X, Loader2
} from 'lucide-react';

const DOC_TYPES: { value: DocType; label: string; desc: string }[] = [
  { value: 'passport', label: 'Passport', desc: 'International travel document' },
  { value: 'visa', label: 'Visa', desc: 'Entry authorization stamp or sticker' },
  { value: 'national_id', label: 'National ID', desc: 'Government-issued national identity card' },
  { value: 'license', label: 'Driving Licence', desc: 'Motor vehicle driving licence' },
  { value: 'permit', label: 'Permit', desc: 'Work permit, residence permit, etc.' },
];

const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
const MAX_SIZE = 10 * 1024 * 1024;

type Step = 1 | 2 | 3;

function StepIndicator({ current }: { current: Step }) {
  const steps = [
    { n: 1, label: 'Create Session' },
    { n: 2, label: 'Document Type' },
    { n: 3, label: 'Upload File' },
  ];

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: '2rem' }}>
      {steps.map((s, i) => (
        <div key={s.n} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '0.8125rem',
                background: (current as number) > s.n
                  ? 'var(--risk-low)'
                  : current === s.n
                    ? 'var(--accent-primary)'
                    : 'var(--bg-elevated)',
                border: current === s.n
                  ? '2px solid var(--accent-primary)'
                  : (current as number) > s.n
                    ? '2px solid var(--risk-low)'
                    : '2px solid var(--border-default)',
                color: (current as number) >= s.n ? 'white' : 'var(--text-muted)',
                transition: 'all 0.3s',
              }}
            >
              {(current as number) > s.n ? <CheckCircle size={16} /> : s.n}
            </div>
            <div style={{
              fontSize: '0.6875rem',
              marginTop: '0.375rem',
              color: current === s.n ? 'var(--accent-primary)' : 'var(--text-muted)',
              fontWeight: current === s.n ? 600 : 400,
            }}>
              {s.label}
            </div>
          </div>
          {i < steps.length - 1 && (
            <div style={{
              height: 2,
              flex: 1,
              background: (current as number) > s.n + 1
                ? 'var(--risk-low)'
                : (current as number) > s.n
                  ? 'var(--accent-primary)'
                  : 'var(--border-default)',
              margin: '0 0.25rem',
              marginTop: '-1.25rem',
              transition: 'background 0.3s',
            }} />
          )}
        </div>
      ))}
    </div>
  );
}

export default function NewScreening() {
  const navigate = useNavigate();
  const { setSession, setDocType, setDocumentId } = useScreeningStore();

  const [step, setStep] = useState<Step>(1);
  const [travelerRef, setTravelerRef] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedDocType, setSelectedDocType] = useState<DocType | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [creatingSession, setCreatingSession] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step 1: Create session
  async function handleCreateSession(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setCreatingSession(true);
    try {
      const res = await api.post('/sessions', {
        traveler_ref_id: travelerRef.trim() || null,
      });
      const id: string = res.data.id;
      setSessionId(id);
      setSession(id, travelerRef.trim() || null);
      showToast('Screening session created', 'success');
      setStep(2);
    } catch (err) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? 'Failed to create session. Check backend connection.');
      showToast('Session creation failed', 'error');
    } finally {
      setCreatingSession(false);
    }
  }

  // Step 2: Choose doc type
  function handleSelectDocType(type: DocType) {
    setSelectedDocType(type);
    setDocType(type);
    setStep(3);
  }

  // Step 3: File handling
  function handleFileSelect(f: File) {
    setError(null);
    if (!ALLOWED_TYPES.includes(f.type)) {
      setError('Unsupported file type. Please upload JPG, PNG, or PDF.');
      return;
    }
    if (f.size > MAX_SIZE) {
      setError('File too large. Maximum size is 10 MB.');
      return;
    }
    setFile(f);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFileSelect(dropped);
  }

  async function handleUpload() {
    if (!file || !sessionId || !selectedDocType) return;
    setUploading(true);
    setError(null);
    setUploadProgress(0);

    const form = new FormData();
    form.append('file', file);

    try {
      const res = await api.post(
        `/sessions/${sessionId}/documents?doc_type=${selectedDocType}`,
        form,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (ev) => {
            if (ev.total) setUploadProgress(Math.round((ev.loaded / ev.total) * 100));
          },
        }
      );
      setDocumentId(res.data.id);
      showToast('Document uploaded — starting pipeline', 'success');
      navigate(`/screening/${sessionId}/processing`);
    } catch (err) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? 'Upload failed. Please try again.');
      showToast('Document upload failed', 'error');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="page-enter" style={{ maxWidth: 680, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, letterSpacing: '-0.01em' }}>
          New Screening Session
        </h1>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>
          Guided document verification workflow
        </p>
      </div>

      <StepIndicator current={step} />

      <div className="card-glass" style={{ padding: '1.75rem' }}>
        {/* ── Step 1: Create Session ───────────────────── */}
        {step === 1 && (
          <div>
            <div style={{ marginBottom: '1.25rem' }}>
              <h2 style={{ fontSize: '1rem', fontWeight: 600, margin: '0 0 0.25rem' }}>
                Create Screening Session
              </h2>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0 }}>
                Optionally enter a traveler reference ID for tracking.
              </p>
            </div>

            <form onSubmit={handleCreateSession} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.375rem', letterSpacing: '0.02em' }}>
                  TRAVELER REFERENCE ID (OPTIONAL)
                </label>
                <input
                  type="text"
                  className="input-field font-mono"
                  value={travelerRef}
                  onChange={(e) => setTravelerRef(e.target.value)}
                  placeholder="e.g. REF-0042, TKT-2891"
                  style={{ letterSpacing: '0.03em' }}
                />
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.375rem' }}>
                  Used for audit trail. Leave blank to auto-generate.
                </div>
              </div>

              {error && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--risk-critical)', fontSize: '0.8125rem', padding: '0.625rem', background: 'var(--risk-critical-bg)', borderRadius: 8, border: '1px solid rgba(239,68,68,0.25)' }}>
                  <AlertCircle size={14} />
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={creatingSession}
                className="btn btn-primary"
                style={{ alignSelf: 'flex-start' }}
              >
                {creatingSession ? <><Loader2 size={15} className="animate-spin" /> Creating…</> : <>Create Session <ChevronRight size={15} /></>}
              </button>
            </form>
          </div>
        )}

        {/* ── Step 2: Choose Document Type ─────────────── */}
        {step === 2 && (
          <div>
            <div style={{ marginBottom: '1.25rem' }}>
              <h2 style={{ fontSize: '1rem', fontWeight: 600, margin: '0 0 0.25rem' }}>
                Choose Document Type
              </h2>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0 }}>
                Select the type of document being presented.
              </p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {DOC_TYPES.map((dt) => (
                <button
                  key={dt.value}
                  onClick={() => handleSelectDocType(dt.value)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.875rem',
                    padding: '0.875rem 1rem',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 10,
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all var(--transition-fast)',
                    width: '100%',
                  }}
                  className="glass-hover"
                >
                  <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--accent-subtle)', border: '1px solid var(--border-accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <FileText size={17} color="var(--accent-primary)" />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>{dt.label}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{dt.desc}</div>
                  </div>
                  <ChevronRight size={16} style={{ color: 'var(--text-muted)' }} />
                </button>
              ))}
            </div>
            <button
              onClick={() => setStep(1)}
              className="btn btn-ghost btn-sm"
              style={{ marginTop: '1rem' }}
            >
              ← Back
            </button>
          </div>
        )}

        {/* ── Step 3: Upload Document ───────────────────── */}
        {step === 3 && selectedDocType && (
          <div>
            <div style={{ marginBottom: '1.25rem' }}>
              <h2 style={{ fontSize: '1rem', fontWeight: 600, margin: '0 0 0.25rem' }}>
                Upload Document
              </h2>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0 }}>
                Upload the {getDocTypeLabel(selectedDocType)} image or PDF for analysis.
              </p>
            </div>

            {/* Drop zone */}
            {!file ? (
              <div
                className={`drop-zone${dragOver ? ' drag-over' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => document.getElementById('file-input')?.click()}
              >
                <Upload size={28} style={{ color: 'var(--text-muted)', marginBottom: '0.75rem' }} />
                <div style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                  Drag &amp; drop or click to browse
                </div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                  JPG, JPEG, PNG or PDF · Max 10 MB
                </div>
                <input
                  id="file-input"
                  type="file"
                  style={{ display: 'none' }}
                  accept=".jpg,.jpeg,.png,.pdf"
                  onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                />
              </div>
            ) : (
              <div style={{
                padding: '1rem',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-accent)',
                borderRadius: 10,
                display: 'flex',
                alignItems: 'center',
                gap: '0.875rem',
              }}>
                <div style={{ width: 40, height: 40, borderRadius: 8, background: 'var(--accent-subtle)', border: '1px solid var(--border-accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <FileText size={20} color="var(--accent-primary)" />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {file.name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.125rem' }}>
                    {formatFileSize(file.size)} · {file.type.split('/')[1]?.toUpperCase()}
                  </div>
                </div>
                <button
                  onClick={() => setFile(null)}
                  className="btn btn-ghost btn-icon"
                  style={{ color: 'var(--text-muted)', flexShrink: 0 }}
                >
                  <X size={16} />
                </button>
              </div>
            )}

            {/* Upload progress */}
            {uploading && (
              <div style={{ marginTop: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.375rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  <span>Uploading…</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${uploadProgress}%`, background: 'var(--accent-primary)' }}
                  />
                </div>
              </div>
            )}

            {error && (
              <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--risk-critical)', fontSize: '0.8125rem', padding: '0.625rem', background: 'var(--risk-critical-bg)', borderRadius: 8, border: '1px solid rgba(239,68,68,0.25)' }}>
                <AlertCircle size={14} /> {error}
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
              <button
                onClick={() => { setStep(2); setFile(null); setError(null); }}
                className="btn btn-secondary"
              >
                ← Back
              </button>
              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="btn btn-primary"
                style={{ flex: 1 }}
              >
                {uploading
                  ? <><Loader2 size={15} /> Uploading…</>
                  : <><Upload size={15} /> Upload &amp; Start Analysis</>}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

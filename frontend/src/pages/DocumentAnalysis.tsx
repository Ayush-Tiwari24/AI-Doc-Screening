import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useScreeningStore } from '../store/screeningStore';
import api from '../lib/api';
import type { DocumentWithUrl, ExtractedDataOut, ValidationResultOut, TamperingResultOut } from '../types/api';
import { formatDate, getDocTypeLabel, getSeverityDisplay, getTechniqueLabel, getSuspicionLabel, getConfidenceLabel } from '../lib/utils';
import { CheckCircle, XCircle, AlertTriangle, Info, Loader2, ZoomIn, RotateCw, Maximize2 } from 'lucide-react';
import DigiLockerVerificationCard from '../components/digilocker/DigiLockerVerificationCard';
import { DIGILOCKER_MATCH_DEMO } from '../lib/demoData';

function OCRField({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.125rem', padding: '0.5rem 0', borderBottom: '1px solid var(--border-subtle)' }}>
      <div style={{ fontSize: '0.6875rem', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>{label}</div>
      <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', fontFamily: value?.length > 30 ? 'var(--font-mono)' : undefined }}>
        {value || '—'}
      </div>
    </div>
  );
}

function ValidationRow({ result }: { result: ValidationResultOut }) {
  const disp = getSeverityDisplay(result.severity, result.passed);
  const StatusIcon = result.passed
    ? <CheckCircle size={14} />
    : result.severity === 'critical'
      ? <XCircle size={14} />
      : result.severity === 'warning'
        ? <AlertTriangle size={14} />
        : <Info size={14} />;

  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', padding: '0.625rem 0', borderBottom: '1px solid var(--border-subtle)' }}>
      <div style={{ color: `var(--${result.passed ? 'risk-low' : result.severity === 'critical' ? 'risk-critical' : result.severity === 'warning' ? 'risk-medium' : 'text-muted'})`, marginTop: '0.125rem', flexShrink: 0 }}>
        {StatusIcon}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.125rem' }}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            {result.rule_name.replace(/_/g, ' ')}
          </span>
          <span className={`badge ${result.passed ? 'badge-success' : result.severity === 'critical' ? 'badge-critical' : result.severity === 'warning' ? 'badge-warning' : 'badge-info'}`} style={{ fontSize: '0.5625rem' }}>
            {disp.text}
          </span>
        </div>
        {result.details && (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{result.details}</div>
        )}
      </div>
    </div>
  );
}

function TamperingCard({ result }: { result: TamperingResultOut }) {
  const { label, color } = getSuspicionLabel(result.suspicious_score);
  return (
    <div style={{ padding: '0.875rem', background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
        <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          {getTechniqueLabel(result.technique)}
        </div>
        <span style={{ fontSize: '0.6875rem', fontWeight: 600, color, background: `${color}18`, padding: '0.125rem 0.5rem', borderRadius: 20, border: `1px solid ${color}33`, flexShrink: 0 }}>
          {label}
        </span>
      </div>
      {result.suspicious_score !== null && (
        <div style={{ marginBottom: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
            <span>Suspicion Score</span>
            <span style={{ color }}>{Math.round((result.suspicious_score ?? 0) * 100)}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${(result.suspicious_score ?? 0) * 100}%`, background: color }} />
          </div>
        </div>
      )}
      {result.details && Object.entries(result.details).slice(0, 2).map(([k, v]) => (
        <div key={k} style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
          {k}: {String(v)}
        </div>
      ))}
      {result.heatmap_path && (
        <div style={{ marginTop: '0.5rem', fontSize: '0.6875rem', color: 'var(--accent-primary)' }}>
          Heatmap available
        </div>
      )}
    </div>
  );
}

export default function DocumentAnalysis() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const store = useScreeningStore();

  const [doc, setDoc] = useState<DocumentWithUrl | null>(null);
  const [extractedData, setExtractedData] = useState<ExtractedDataOut | null>(store.extractedData);
  const [validationResults, setValidationResults] = useState<ValidationResultOut[]>(store.validationResults);
  const [tamperingResults, setTamperingResults] = useState<TamperingResultOut[]>(store.tamperingResults);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imageRotation, setImageRotation] = useState(0);

  useEffect(() => {
    if (!sessionId) return;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        // Load documents
        const docsRes = await api.get(`/sessions/${sessionId}/documents`);
        const documents: DocumentWithUrl[] = docsRes.data;
        if (documents.length === 0) { setError('No documents found for this session.'); return; }
        const firstDoc = documents[0];
        setDoc(firstDoc);

        // Load extracted data
        try {
          const exRes = await api.post(`/documents/${firstDoc.id}/extract`);
          setExtractedData(exRes.data);
          store.setExtractedData(exRes.data);
        } catch { /* might already be extracted */ }

        // Load validation
        try {
          const valRes = await api.post(`/documents/${firstDoc.id}/validate`);
          setValidationResults(valRes.data);
          store.setValidationResults(valRes.data);
        } catch { /* might already be done */ }

        // Load tampering
        try {
          const tampRes = await api.post(`/documents/${firstDoc.id}/detect-tampering/basic`);
          setTamperingResults(tampRes.data);
          store.setTamperingResults(tampRes.data);
        } catch { /* might already be done */ }

      } catch (e) {
        setError('Failed to load document analysis. Please try again.');
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 300, gap: '0.75rem', color: 'var(--text-secondary)' }}>
        <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
        Loading analysis results…
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: 500, margin: '4rem auto', textAlign: 'center' }}>
        <div style={{ color: 'var(--risk-critical)', marginBottom: '0.75rem' }}><AlertTriangle size={24} /></div>
        <div style={{ color: 'var(--text-primary)', marginBottom: '0.5rem', fontWeight: 600 }}>{error}</div>
        <button onClick={() => navigate(-1)} className="btn btn-secondary btn-sm">← Back</button>
      </div>
    );
  }

  const docType = doc?.doc_type ?? 'passport';
  const conf = getConfidenceLabel(extractedData?.ocr_confidence ?? null);
  const passed = validationResults.filter((v) => v.passed).length;
  const failed = validationResults.filter((v) => !v.passed).length;
  const maxSuspicion = tamperingResults.reduce((a, t) => Math.max(a, t.suspicious_score ?? 0), 0);
  const { label: tampLabel, color: tampColor } = getSuspicionLabel(maxSuspicion > 0 ? maxSuspicion : null);

  return (
    <div className="page-enter" style={{ maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>Document Analysis</h1>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>
            {getDocTypeLabel(docType)} · Session {sessionId?.slice(0, 8).toUpperCase()}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button onClick={() => navigate(`/screening/${sessionId}/face`)} className="btn btn-secondary btn-sm">
            Face Verification →
          </button>
          <button onClick={() => navigate(`/screening/${sessionId}/report`)} className="btn btn-primary btn-sm">
            Risk Report →
          </button>
        </div>
      </div>

      {/* Three-column layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', alignItems: 'start' }}>
        {/* ── LEFT: Document Preview ─────────────────────── */}
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, overflow: 'hidden' }}>
          <div style={{ padding: '0.875rem 1rem', borderBottom: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Document Preview</span>
            <div style={{ display: 'flex', gap: '0.25rem' }}>
              <button className="btn btn-ghost btn-icon" onClick={() => setImageRotation((r) => r + 90)} title="Rotate"><RotateCw size={14} /></button>
              <button className="btn btn-ghost btn-icon" title="Zoom"><ZoomIn size={14} /></button>
              {doc?.view_url && <a href={doc.view_url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-icon" title="Fullscreen"><Maximize2 size={14} /></a>}
            </div>
          </div>
          <div style={{ padding: '1rem' }}>
            {doc?.view_url ? (
              <div className="scanner-container" style={{ borderRadius: 8, overflow: 'hidden', background: 'var(--bg-primary)' }}>
                <img
                  src={doc.view_url}
                  alt="Document"
                  style={{ width: '100%', display: 'block', transform: `rotate(${imageRotation}deg)`, transition: 'transform 0.3s' }}
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
              </div>
            ) : (
              <div style={{ height: 200, background: 'var(--bg-primary)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                Preview not available
              </div>
            )}
            {doc && (
              <div style={{ marginTop: '0.75rem', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                <div>Type: {getDocTypeLabel(doc.doc_type)}</div>
                <div style={{ marginTop: '0.125rem' }}>Uploaded: {formatDate(doc.uploaded_at)}</div>
              </div>
            )}
          </div>
        </div>

        {/* ── CENTER: Extracted Identity ──────────────────── */}
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, overflow: 'hidden' }}>
          <div style={{ padding: '0.875rem 1rem', borderBottom: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Extracted Identity</span>
            {extractedData && (
              <span style={{ marginLeft: 'auto', fontSize: '0.6875rem', color: conf.color, fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                OCR {conf.label}
              </span>
            )}
          </div>
          <div style={{ padding: '1rem' }}>
            {extractedData ? (
              <>
                <OCRField label="Full Name" value={extractedData.full_name ?? ''} />
                <OCRField label="Document Number" value={extractedData.doc_number ?? ''} />
                <OCRField label="Nationality" value={extractedData.nationality ?? ''} />
                <OCRField label="Date of Birth" value={extractedData.dob ? formatDate(extractedData.dob) : ''} />
                <OCRField label="Date of Expiry" value={extractedData.doe ? formatDate(extractedData.doe) : ''} />
                <OCRField label="Gender" value={extractedData.gender ?? ''} />
                {extractedData.mrz_raw && (
                  <div style={{ marginTop: '0.75rem', padding: '0.5rem', background: 'var(--bg-primary)', borderRadius: 6, fontFamily: 'var(--font-mono)', fontSize: '0.625rem', color: 'var(--text-secondary)', wordBreak: 'break-all', letterSpacing: '0.06em' }}>
                    MRZ: {extractedData.mrz_raw}
                  </div>
                )}
                {extractedData.extra_fields && Object.entries(extractedData.extra_fields).map(([k, v]) => (
                  <OCRField key={k} label={k.replace(/_/g, ' ')} value={String(v)} />
                ))}
              </>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', textAlign: 'center', padding: '2rem 0' }}>
                OCR data not yet available
              </div>
            )}
          </div>
        </div>

        {/* ── RIGHT: Validation + Tampering ──────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Validation */}
          <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, overflow: 'hidden' }}>
            <div style={{ padding: '0.875rem 1rem', borderBottom: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Validation</span>
              <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.375rem' }}>
                {passed > 0 && <span className="badge badge-success" style={{ fontSize: '0.5625rem' }}>{passed} PASS</span>}
                {failed > 0 && <span className="badge badge-critical" style={{ fontSize: '0.5625rem' }}>{failed} FAIL</span>}
              </div>
            </div>
            <div style={{ padding: '0.625rem 1rem' }}>
              {validationResults.length > 0 ? (
                validationResults.map((v) => <ValidationRow key={v.id} result={v} />)
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', padding: '1rem 0', textAlign: 'center' }}>
                  Validation pending
                </div>
              )}
            </div>
          </div>

          {/* Tampering */}
          <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, overflow: 'hidden' }}>
            <div style={{ padding: '0.875rem 1rem', borderBottom: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Forensic Analysis</span>
              {tamperingResults.length > 0 && (
                <span style={{ marginLeft: 'auto', fontSize: '0.6875rem', fontWeight: 600, color: tampColor }}>
                  {tampLabel}
                </span>
              )}
            </div>
            <div style={{ padding: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {tamperingResults.length > 0 ? (
                tamperingResults.map((t) => <TamperingCard key={t.id} result={t} />)
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', padding: '1rem 0', textAlign: 'center' }}>
                  Tampering analysis pending
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* DigiLocker Demo */}
      <div style={{ marginTop: '1.25rem' }}>
        <DigiLockerVerificationCard record={DIGILOCKER_MATCH_DEMO} />
      </div>
    </div>
  );
}

import { useState, useRef, useCallback, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useScreeningStore } from '../store/screeningStore';
import api from '../lib/api';
import type { FaceVerificationOut } from '../types/api';
import { showToast } from '../components/shared/Toast';
import {
  Camera, Upload, RotateCcw, CheckCircle, XCircle,
  Loader2, AlertTriangle, User, ScanFace, Shield
} from 'lucide-react';

function SimilarityRing({ score, match }: { score: number; match: boolean | null }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const color = match === false ? 'var(--risk-critical)' : score >= 70 ? 'var(--risk-low)' : score >= 50 ? 'var(--risk-medium)' : 'var(--risk-critical)';

  return (
    <div style={{ position: 'relative', width: 130, height: 130, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width="130" height="130" style={{ transform: 'rotate(-90deg)', position: 'absolute' }}>
        <circle cx="65" cy="65" r={radius} fill="none" stroke="var(--border-default)" strokeWidth="8" />
        <circle
          cx="65" cy="65" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="similarity-ring"
          style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.25,0.46,0.45,0.94), stroke 0.5s' }}
        />
      </svg>
      <div style={{ textAlign: 'center', position: 'relative', zIndex: 1 }}>
        <div style={{ fontSize: '1.5rem', fontWeight: 800, color, letterSpacing: '-0.03em', lineHeight: 1 }}>
          {Math.round(score)}%
        </div>
        <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: '0.125rem' }}>
          Similarity
        </div>
      </div>
    </div>
  );
}

export default function FaceVerification() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { setFaceVerification } = useScreeningStore();

  const [mode, setMode] = useState<'idle' | 'webcam' | 'upload'>('idle');
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [result, setResult] = useState<FaceVerificationOut | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startCamera = useCallback(async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setMode('webcam');
    } catch {
      setCameraError('Camera access denied or unavailable. Please use image upload instead.');
    }
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  useEffect(() => () => stopCamera(), [stopCamera]);

  function captureFrame() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')?.drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob) return;
      setCapturedBlob(blob);
      setCapturedImage(canvas.toDataURL('image/jpeg'));
      stopCamera();
    }, 'image/jpeg', 0.92);
  }

  function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setUploadedFile(f);
    const reader = new FileReader();
    reader.onload = (ev) => setCapturedImage(ev.target?.result as string);
    reader.readAsDataURL(f);
    setCapturedBlob(f);
    setMode('upload');
  }

  function retake() {
    setCapturedImage(null);
    setCapturedBlob(null);
    setUploadedFile(null);
    setResult(null);
    setMode('idle');
  }

  async function handleVerify() {
    if (!capturedBlob || !sessionId) return;
    setVerifying(true);

    const form = new FormData();
    form.append(
      'live_image',
      capturedBlob instanceof File ? capturedBlob : new File([capturedBlob], 'live_capture.jpg', { type: 'image/jpeg' })
    );

    try {
      const res = await api.post<FaceVerificationOut>(
        `/sessions/${sessionId}/verify-face`,
        form,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setResult(res.data);
      setFaceVerification(res.data);
      showToast('Face verification complete', 'success');
    } catch (err) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast(msg ?? 'Face verification failed', 'error');
    } finally {
      setVerifying(false);
    }
  }

  const simScore = result?.similarity_score !== null && result?.similarity_score !== undefined
    ? result.similarity_score * 100
    : 0;

  return (
    <div className="page-enter" style={{ maxWidth: 800, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>Face Verification</h1>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>
          Biometric comparison · Session {sessionId?.slice(0, 8).toUpperCase()}
        </p>
      </div>

      {/* Result view */}
      {result ? (
        <div className="card-glass" style={{ padding: '2rem', textAlign: 'center' }}>
          <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'center' }}>
            <SimilarityRing score={simScore} match={result.match} />
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
            <span className={`badge ${result.match ? 'badge-success' : 'badge-critical'}`}>
              {result.match ? <CheckCircle size={12} /> : <XCircle size={12} />}
              {result.match ? 'Match' : 'Mismatch'}
            </span>
            {result.liveness_passed !== null && (
              <span className={`badge ${result.liveness_passed ? 'badge-success' : 'badge-warning'}`}>
                {result.liveness_passed ? 'Liveness Passed' : 'Liveness Requires Review'}
              </span>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', maxWidth: 360, margin: '0 auto 1.5rem' }}>
            <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 10, padding: '0.875rem' }}>
              <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginBottom: '0.25rem', fontWeight: 600, letterSpacing: '0.04em' }}>SIMILARITY</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: result.match ? 'var(--risk-low)' : 'var(--risk-critical)' }}>
                {result.similarity_score !== null ? `${Math.round((result.similarity_score ?? 0) * 100)}%` : '—'}
              </div>
            </div>
            {result.liveness_score !== null && (
              <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 10, padding: '0.875rem' }}>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginBottom: '0.25rem', fontWeight: 600, letterSpacing: '0.04em' }}>LIVENESS</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: result.liveness_passed ? 'var(--risk-low)' : 'var(--risk-medium)' }}>
                  {result.liveness_score !== null ? `${Math.round((result.liveness_score ?? 0) * 100)}%` : '—'}
                </div>
              </div>
            )}
          </div>

          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
            <Shield size={12} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '0.25rem' }} />
            Powered by InsightFace · Liveness accuracy may vary
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button onClick={retake} className="btn btn-secondary">
              <RotateCcw size={15} /> Retake
            </button>
            <button
              onClick={() => navigate(`/screening/${sessionId}/report`)}
              className="btn btn-primary"
            >
              View Risk Report →
            </button>
          </div>
        </div>
      ) : (
        <div className="card-glass" style={{ padding: '1.75rem' }}>
          {/* Capture mode selection */}
          {mode === 'idle' && !capturedImage && (
            <div>
              <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                <div style={{ width: 60, height: 60, borderRadius: '50%', background: 'var(--accent-subtle)', border: '1px solid var(--border-accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 0.875rem' }}>
                  <ScanFace size={28} color="var(--accent-primary)" />
                </div>
                <h2 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: '0 0 0.375rem' }}>Capture Live Image</h2>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0 }}>
                  Use webcam or upload a recent photograph for biometric comparison.
                </p>
              </div>

              {cameraError && (
                <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--risk-medium)', fontSize: '0.8125rem', padding: '0.625rem', background: 'var(--risk-medium-bg)', borderRadius: 8 }}>
                  <AlertTriangle size={14} /> {cameraError}
                </div>
              )}

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                <button onClick={startCamera} className="btn btn-primary btn-lg">
                  <Camera size={18} /> Use Webcam
                </button>
                <label className="btn btn-secondary btn-lg" style={{ cursor: 'pointer' }}>
                  <Upload size={18} /> Upload Image
                  <input type="file" accept=".jpg,.jpeg,.png" onChange={handleFileUpload} style={{ display: 'none' }} />
                </label>
              </div>
            </div>
          )}

          {/* Webcam view */}
          {mode === 'webcam' && !capturedImage && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <div style={{ position: 'relative', borderRadius: 12, overflow: 'hidden', background: 'var(--bg-primary)', border: '1px solid var(--border-default)' }}>
                <video ref={videoRef} autoPlay muted playsInline style={{ display: 'block', maxWidth: '100%', maxHeight: 360 }} />
                {/* Face guide overlay */}
                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
                  <div style={{ width: 180, height: 220, border: '2px dashed rgba(59,130,246,0.6)', borderRadius: '50%' }} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button onClick={retake} className="btn btn-ghost">Cancel</button>
                <button onClick={captureFrame} className="btn btn-primary btn-lg">
                  <Camera size={16} /> Capture
                </button>
              </div>
              <canvas ref={canvasRef} style={{ display: 'none' }} />
            </div>
          )}

          {/* Preview captured image */}
          {capturedImage && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem' }}>
              <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Document Photo</div>
                  <div style={{ width: 120, height: 150, background: 'var(--bg-primary)', border: '1px solid var(--border-default)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                    <User size={32} />
                  </div>
                  <div style={{ fontSize: '0.625rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>From document</div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{ fontSize: '1.25rem', color: 'var(--text-muted)' }}>↔</div>
                  <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'var(--accent-subtle)', border: '1px solid var(--border-accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <ScanFace size={20} color="var(--accent-primary)" />
                  </div>
                </div>

                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Live Capture</div>
                  <img
                    src={capturedImage}
                    alt="Live capture"
                    style={{ width: 120, height: 150, objectFit: 'cover', borderRadius: 8, border: '2px solid var(--accent-primary)', display: 'block' }}
                  />
                  <div style={{ fontSize: '0.625rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Just captured</div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button onClick={retake} className="btn btn-secondary">
                  <RotateCcw size={15} /> Retake
                </button>
                <button onClick={handleVerify} disabled={verifying} className="btn btn-primary btn-lg">
                  {verifying
                    ? <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Verifying…</>
                    : <><CheckCircle size={16} /> Verify Identity</>}
                </button>
              </div>

              {(uploadedFile != null) && (
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                  File: {uploadedFile.name}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Nav links */}
      <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
        <button onClick={() => navigate(`/screening/${sessionId}/analysis`)} className="btn btn-ghost btn-sm" style={{ fontSize: '0.75rem' }}>
          ← Document Analysis
        </button>
        <button onClick={() => navigate(`/screening/${sessionId}/report`)} className="btn btn-ghost btn-sm" style={{ fontSize: '0.75rem' }}>
          Skip to Risk Report →
        </button>
      </div>
    </div>
  );
}

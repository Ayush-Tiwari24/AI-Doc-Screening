import type { RiskLevel, DocType, SessionStatus } from '../types/api';

// ─── Risk Level Helpers ────────────────────────────────────────

export function getRiskColor(level: RiskLevel | string | null): string {
  switch (level) {
    case 'low': return 'var(--risk-low)';
    case 'medium': return 'var(--risk-medium)';
    case 'high': return 'var(--risk-high)';
    case 'critical': return 'var(--risk-critical)';
    default: return 'var(--text-muted)';
  }
}

export function getRiskBadgeClass(level: RiskLevel | string | null): string {
  switch (level) {
    case 'low': return 'badge badge-low';
    case 'medium': return 'badge badge-medium';
    case 'high': return 'badge badge-high';
    case 'critical': return 'badge badge-critical';
    default: return 'badge badge-info';
  }
}

export function getRiskLabel(level: RiskLevel | string | null): string {
  if (!level) return 'Unknown';
  return level.charAt(0).toUpperCase() + level.slice(1);
}

// ─── DocType Display Labels ────────────────────────────────────

const DOC_TYPE_LABELS: Record<DocType, string> = {
  passport: 'Passport',
  visa: 'Visa',
  national_id: 'National ID',
  license: 'Driving Licence',
  permit: 'Permit',
};

export function getDocTypeLabel(type: DocType | string): string {
  return DOC_TYPE_LABELS[type as DocType] ?? type;
}

// ─── Session Status Display ─────────────────────────────────────

export function getStatusLabel(status: SessionStatus | string | null): string {
  switch (status) {
    case 'pending': return 'Pending';
    case 'processing': return 'Processing';
    case 'awaiting_face': return 'Awaiting Face Verification';
    case 'scored': return 'Scoring Risk';
    case 'complete': return 'Complete';
    case 'failed': return 'Failed';
    default: return status ?? 'Unknown';
  }
}

// ─── Date Formatting ──────────────────────────────────────────

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ─── Tampering Technique Labels ───────────────────────────────

export function getTechniqueLabel(technique: string): string {
  switch (technique) {
    case 'ela': return 'Error Level Analysis (ELA)';
    case 'metadata': return 'Metadata Forensics';
    case 'cnn_classifier': return 'CNN Classifier';
    case 'photo_swap': return 'Photo Swap Detection';
    default: return technique;
  }
}

export function getSuspicionLabel(score: number | null): { label: string; color: string } {
  if (score === null) return { label: 'Not Assessed', color: 'var(--text-muted)' };
  if (score < 0.3) return { label: 'Low Suspicion', color: 'var(--risk-low)' };
  if (score < 0.6) return { label: 'Requires Review', color: 'var(--risk-medium)' };
  return { label: 'High Suspicion', color: 'var(--risk-critical)' };
}

// ─── File size formatting ──────────────────────────────────────

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ─── Validation Severity ──────────────────────────────────────

export function getSeverityDisplay(severity: string, passed: boolean): { icon: string; className: string; text: string } {
  if (passed) return { icon: '✓', className: 'validation-pass', text: 'PASS' };
  switch (severity) {
    case 'critical': return { icon: '✕', className: 'validation-fail', text: 'FAIL' };
    case 'warning': return { icon: '⚠', className: 'validation-warn', text: 'WARNING' };
    default: return { icon: 'ℹ', className: '', text: 'INFO' };
  }
}

// ─── OCR Confidence ───────────────────────────────────────────

export function getConfidenceLabel(conf: number | null): { label: string; color: string } {
  if (conf === null) return { label: '—', color: 'var(--text-muted)' };
  const pct = Math.round(conf * 100);
  if (pct >= 80) return { label: `${pct}%`, color: 'var(--risk-low)' };
  if (pct >= 60) return { label: `${pct}%`, color: 'var(--risk-medium)' };
  return { label: `${pct}%`, color: 'var(--risk-critical)' };
}

// ─── Short UUID ────────────────────────────────────────────────
export function shortId(id: string): string {
  return id.slice(0, 8).toUpperCase();
}

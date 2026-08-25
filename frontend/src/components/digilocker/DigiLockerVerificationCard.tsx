import type { DigiLockerRecord } from '../../types/api';
import { CheckCircle, XCircle, AlertCircle, Info, ExternalLink } from 'lucide-react';

interface Props {
  record: DigiLockerRecord;
  className?: string;
}

const STATUS_CONFIG = {
  matched: { icon: <CheckCircle size={15} />, color: 'var(--risk-low)', label: 'Demo Match', bgClass: 'badge-success' },
  mismatched: { icon: <XCircle size={15} />, color: 'var(--risk-critical)', label: 'Demo Mismatch', bgClass: 'badge-critical' },
  unavailable: { icon: <AlertCircle size={15} />, color: 'var(--text-muted)', label: 'Unavailable', bgClass: 'badge-info' },
};

export default function DigiLockerVerificationCard({ record }: Props) {
  const config = STATUS_CONFIG[record.status];

  return (
    <div
      style={{
        background: 'var(--bg-elevated)',
        border: '1px dashed rgba(139,92,246,0.3)',
        borderRadius: 12,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '0.875rem 1.125rem',
          background: 'var(--violet-subtle)',
          borderBottom: '1px dashed rgba(139,92,246,0.2)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          flexWrap: 'wrap',
        }}
      >
        {/* Source logo placeholder */}
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: 'rgba(139,92,246,0.15)',
            border: '1px solid rgba(139,92,246,0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.5625rem',
            fontWeight: 700,
            color: '#8b5cf6',
            flexShrink: 0,
          }}
        >
          DL
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              DigiLocker Verification
            </span>
            <span className="badge badge-demo" style={{ fontSize: '0.5625rem' }}>DEMO SOURCE</span>
          </div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.125rem' }}>
            {record.source} · Sandbox Mode
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: config.color }}>
          {config.icon}
          <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>{config.label}</span>
        </div>
      </div>

      {/* Body */}
      <div style={{ padding: '1rem 1.125rem' }}>
        {/* Disclaimer */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.5rem',
            padding: '0.5rem 0.75rem',
            marginBottom: '1rem',
            background: 'rgba(139,92,246,0.06)',
            borderRadius: 8,
            fontSize: '0.6875rem',
            color: 'var(--text-muted)',
            lineHeight: 1.5,
          }}
        >
          <Info size={13} style={{ flexShrink: 0, color: '#8b5cf6', marginTop: '0.125rem' }} />
          <span>
            This prototype does not access live DigiLocker or government records.
            This component demonstrates how authorized issuer verification could be integrated in production.
            {' '}<strong style={{ color: 'var(--text-secondary)' }}>Not included in backend risk score.</strong>
          </span>
        </div>

        {record.status === 'unavailable' ? (
          <div style={{ textAlign: 'center', padding: '1.5rem 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            <AlertCircle size={20} style={{ marginBottom: '0.5rem', display: 'block', margin: '0 auto 0.5rem' }} />
            Authoritative source unavailable in demo environment
          </div>
        ) : (
          <>
            {/* Comparison table */}
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ padding: '0.375rem 0.625rem', textAlign: 'left', fontSize: '0.6rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)', borderBottom: '1px solid var(--border-default)', width: '25%' }}>Field</th>
                    <th style={{ padding: '0.375rem 0.625rem', textAlign: 'left', fontSize: '0.6rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)', borderBottom: '1px solid var(--border-default)' }}>OCR Extracted</th>
                    <th style={{ padding: '0.375rem 0.625rem', textAlign: 'left', fontSize: '0.6rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)', borderBottom: '1px solid var(--border-default)' }}>Sandbox Reference</th>
                    <th style={{ padding: '0.375rem 0.625rem', textAlign: 'center', fontSize: '0.6rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)', borderBottom: '1px solid var(--border-default)', width: 80 }}>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {record.fields.map((field) => (
                    <tr key={field.label} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '0.5rem 0.625rem', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                        {field.label}
                      </td>
                      <td style={{ padding: '0.5rem 0.625rem', fontSize: '0.8125rem', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                        {field.extracted}
                      </td>
                      <td style={{ padding: '0.5rem 0.625rem', fontSize: '0.8125rem', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                        {field.reference}
                      </td>
                      <td style={{ padding: '0.5rem 0.625rem', textAlign: 'center' }}>
                        {field.match ? (
                          <CheckCircle size={15} style={{ color: 'var(--risk-low)' }} />
                        ) : (
                          <XCircle size={15} style={{ color: 'var(--risk-critical)' }} />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Summary */}
            <div style={{ marginTop: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', gap: '0.375rem' }}>
                {record.fields.filter((f) => f.match).length > 0 && (
                  <span className="badge badge-success" style={{ fontSize: '0.5625rem' }}>
                    {record.fields.filter((f) => f.match).length} Matched
                  </span>
                )}
                {record.fields.filter((f) => !f.match).length > 0 && (
                  <span className="badge badge-critical" style={{ fontSize: '0.5625rem' }}>
                    {record.fields.filter((f) => !f.match).length} Mismatched
                  </span>
                )}
              </div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                Demo authoritative-source check — not included in backend risk score
                <ExternalLink size={11} />
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

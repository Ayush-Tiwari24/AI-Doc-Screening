import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DEMO_SCREENING_HISTORY } from '../lib/demoData';
import { getDocTypeLabel, formatDateTime, getRiskBadgeClass, getRiskLabel } from '../lib/utils';
import type { RiskLevel, DocType } from '../types/api';
import RiskBadge from '../components/shared/RiskBadge';
import { Search, Filter, Eye } from 'lucide-react';

const DOC_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: '', label: 'All Document Types' },
  { value: 'passport', label: 'Passport' },
  { value: 'visa', label: 'Visa' },
  { value: 'national_id', label: 'National ID' },
  { value: 'license', label: 'Driving Licence' },
  { value: 'permit', label: 'Permit' },
];

const RISK_OPTIONS: { value: string; label: string }[] = [
  { value: '', label: 'All Risk Levels' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
];

export default function History() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [docTypeFilter, setDocTypeFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');

  const filtered = DEMO_SCREENING_HISTORY.filter((row) => {
    if (search && !row.travelerRef.toLowerCase().includes(search.toLowerCase()) && !row.id.includes(search.toLowerCase())) return false;
    if (docTypeFilter && row.docType !== docTypeFilter) return false;
    if (riskFilter && row.riskLevel !== riskFilter) return false;
    return true;
  });

  return (
    <div className="page-enter" style={{ maxWidth: 1100, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>Screening History</h1>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>
            Session records and audit trail
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <span className="badge badge-demo" style={{ fontSize: '0.6rem' }}>Demo Data</span>
          <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>— No session history API available</span>
        </div>
      </div>

      {/* Filters */}
      <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, padding: '1rem', marginBottom: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <Filter size={15} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />

        <div style={{ position: 'relative', flex: '1 1 200px' }}>
          <Search size={14} style={{ position: 'absolute', left: '0.625rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            className="input-field"
            type="text"
            placeholder="Search by reference or ID…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: '2rem' }}
          />
        </div>

        <select
          className="input-field"
          value={docTypeFilter}
          onChange={(e) => setDocTypeFilter(e.target.value)}
          style={{ flex: '0 1 180px' }}
        >
          {DOC_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>

        <select
          className="input-field"
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          style={{ flex: '0 1 160px' }}
        >
          {RISK_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>

        {(search || docTypeFilter || riskFilter) && (
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => { setSearch(''); setDocTypeFilter(''); setRiskFilter(''); }}
          >
            Clear
          </button>
        )}
      </div>

      {/* Table */}
      <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Screening ID</th>
                <th>Traveler Ref</th>
                <th>Document Type</th>
                <th>Date &amp; Time</th>
                <th>Risk</th>
                <th>Status</th>
                <th>Officer</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '3rem 1rem' }}>
                    No records match your filters
                  </td>
                </tr>
              ) : (
                filtered.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {row.id.slice(0, 8).toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {row.travelerRef}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      {getDocTypeLabel(row.docType as DocType)}
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                      {formatDateTime(row.date)}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <RiskBadge level={row.riskLevel as RiskLevel} />
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
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>
                      {row.officer}
                    </td>
                    <td>
                      <button
                        className="btn btn-ghost btn-sm"
                        style={{ color: 'var(--accent-primary)' }}
                        onClick={() => navigate(`/screening/${row.id}/report`)}
                        title="View screening"
                      >
                        <Eye size={14} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div style={{ padding: '0.625rem 1rem', borderTop: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {filtered.length} of {DEMO_SCREENING_HISTORY.length} records
          </span>
          <span className="badge badge-demo" style={{ fontSize: '0.5625rem' }}>Synthetic identities — Demo only</span>
        </div>
      </div>
    </div>
  );
}

// suppress unused import
void getRiskBadgeClass; void getRiskLabel;

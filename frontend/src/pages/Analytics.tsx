import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
  DEMO_RISK_DISTRIBUTION,
  DEMO_SCREENINGS_OVER_TIME,
  DEMO_DOC_TYPE_DISTRIBUTION,
  DEMO_TAMPERING_BREAKDOWN
} from '../lib/demoData';
import { BarChart3 } from 'lucide-react';

function ChartCard({ title, children, className }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 12, overflow: 'hidden' }} className={className}>
      <div style={{ padding: '0.875rem 1.125rem', borderBottom: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>{title}</span>
        <span className="badge badge-demo" style={{ marginLeft: 'auto', fontSize: '0.5625rem' }}>Demo Analytics</span>
      </div>
      <div style={{ padding: '1rem' }}>{children}</div>
    </div>
  );
}

const CUSTOM_TOOLTIP_STYLE = {
  background: 'var(--bg-elevated)',
  border: '1px solid var(--border-default)',
  borderRadius: 8,
  padding: '0.5rem 0.875rem',
  fontSize: '0.8125rem',
  color: 'var(--text-primary)',
  boxShadow: 'var(--shadow-md)',
};

export default function Analytics() {
  return (
    <div className="page-enter" style={{ maxWidth: 1100, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>Analytics</h1>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>
            Operational intelligence and screening metrics
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <BarChart3 size={14} style={{ color: 'var(--text-muted)' }} />
          <span className="badge badge-demo">Demo Analytics</span>
          <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>— No analytics API endpoint available</span>
        </div>
      </div>

      {/* Summary row */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        {[
          { label: 'Total Screenings', value: '177', accent: 'var(--accent-primary)' },
          { label: 'Cleared', value: '143', accent: 'var(--risk-low)' },
          { label: 'Flagged', value: '25', accent: 'var(--risk-high)' },
          { label: 'Critical Escalations', value: '9', accent: 'var(--risk-critical)' },
          { label: 'Avg. Time', value: '4.2m', accent: 'var(--risk-medium)' },
        ].map((m) => (
          <div key={m.label} style={{ flex: '1 1 130px', background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 10, padding: '0.875rem 1rem' }}>
            <div style={{ fontSize: '1.375rem', fontWeight: 700, color: m.accent, letterSpacing: '-0.02em' }}>{m.value}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500, marginTop: '0.125rem' }}>{m.label}</div>
          </div>
        ))}
      </div>

      {/* Charts grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
        {/* Screenings over time */}
        <ChartCard title="Screenings Over Time">
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={DEMO_SCREENINGS_OVER_TIME} margin={{ top: 5, right: 5, bottom: 0, left: -20 }}>
              <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={CUSTOM_TOOLTIP_STYLE} cursor={{ stroke: 'var(--border-default)' }} />
              <Area type="monotone" dataKey="count" stroke="var(--accent-primary)" strokeWidth={2} fill="url(#areaGrad)" name="Screenings" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Risk distribution */}
        <ChartCard title="Risk Distribution">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <ResponsiveContainer width={160} height={160}>
              <PieChart>
                <Pie
                  data={DEMO_RISK_DISTRIBUTION}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {DEMO_RISK_DISTRIBUTION.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={CUSTOM_TOOLTIP_STYLE} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {DEMO_RISK_DISTRIBUTION.map((d) => (
                <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: d.color, flexShrink: 0 }} />
                  <span style={{ flex: 1, fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{d.name}</span>
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>{d.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </ChartCard>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {/* Document type distribution */}
        <ChartCard title="Document Type Distribution">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={DEMO_DOC_TYPE_DISTRIBUTION} margin={{ top: 5, right: 5, bottom: 0, left: -20 }} barSize={18}>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={CUSTOM_TOOLTIP_STYLE} cursor={{ fill: 'var(--bg-glass)' }} />
              <Bar dataKey="value" fill="var(--accent-primary)" radius={[4, 4, 0, 0]} name="Count" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Tampering breakdown */}
        <ChartCard title="Tampering Technique Breakdown">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={DEMO_TAMPERING_BREAKDOWN} layout="vertical" margin={{ top: 5, right: 15, bottom: 0, left: 10 }} barSize={12}>
              <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
              <YAxis dataKey="technique" type="category" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} width={65} />
              <Tooltip contentStyle={CUSTOM_TOOLTIP_STYLE} cursor={{ fill: 'var(--bg-glass)' }} />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '0.75rem' }} />
              <Bar dataKey="clean" name="Clean" fill="var(--risk-low)" stackId="a" radius={[0, 4, 4, 0]} />
              <Bar dataKey="flagged" name="Flagged" fill="var(--risk-critical)" stackId="a" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

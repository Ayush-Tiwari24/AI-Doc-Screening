import type { RiskLevel } from '../../types/api';
import { getRiskLabel } from '../../lib/utils';

interface RiskBadgeProps {
  level: RiskLevel | string | null;
  size?: 'sm' | 'md' | 'lg';
}

const DOT_COLORS: Record<string, string> = {
  low: 'var(--risk-low)',
  medium: 'var(--risk-medium)',
  high: 'var(--risk-high)',
  critical: 'var(--risk-critical)',
};

const BADGE_CLASSES: Record<string, string> = {
  low: 'badge badge-low',
  medium: 'badge badge-medium',
  high: 'badge badge-high',
  critical: 'badge badge-critical',
};

export default function RiskBadge({ level, size = 'md' }: RiskBadgeProps) {
  const key = level?.toLowerCase() ?? '';
  const cls = BADGE_CLASSES[key] ?? 'badge badge-info';
  const dot = DOT_COLORS[key] ?? 'var(--text-muted)';

  const fontSize = size === 'sm' ? '0.625rem' : size === 'lg' ? '0.8125rem' : undefined;

  return (
    <span className={cls} style={fontSize ? { fontSize } : undefined}>
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: dot,
          display: 'inline-block',
          flexShrink: 0,
        }}
      />
      {getRiskLabel(level)}
    </span>
  );
}

import { useEffect, useState, useCallback } from 'react';
import { CheckCircle, AlertCircle, Info, X, AlertTriangle } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

// Singleton event bus
type ToastHandler = (t: Toast) => void;
let _handler: ToastHandler | null = null;

export function showToast(message: string, type: ToastType = 'info', duration = 4000) {
  _handler?.({ id: Math.random().toString(36).slice(2), type, message, duration });
}

const ICONS: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle size={16} style={{ color: 'var(--risk-low)' }} />,
  error: <AlertCircle size={16} style={{ color: 'var(--risk-critical)' }} />,
  warning: <AlertTriangle size={16} style={{ color: 'var(--risk-medium)' }} />,
  info: <Info size={16} style={{ color: 'var(--accent-primary)' }} />,
};

const BORDER_COLORS: Record<ToastType, string> = {
  success: 'rgba(16,185,129,0.3)',
  error: 'rgba(239,68,68,0.3)',
  warning: 'rgba(245,158,11,0.3)',
  info: 'rgba(59,130,246,0.3)',
};

export default function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const add = useCallback((t: Toast) => {
    setToasts((prev) => [...prev, t]);
    if (t.duration) {
      setTimeout(() => remove(t.id), t.duration);
    }
  }, []);

  function remove(id: string) {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }

  useEffect(() => {
    _handler = add;
    return () => { _handler = null; };
  }, [add]);

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="toast"
          style={{ borderColor: BORDER_COLORS[t.type] }}
        >
          {ICONS[t.type]}
          <span style={{ flex: 1, color: 'var(--text-primary)', fontSize: '0.8125rem' }}>
            {t.message}
          </span>
          <button
            onClick={() => remove(t.id)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              padding: '2px',
            }}
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}

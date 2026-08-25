import { type ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="w-56 border-r border-border bg-surface p-4">
        <h2 className="mb-6 text-sm font-semibold uppercase tracking-wide text-text-secondary">
          Doc Screening
        </h2>
        <nav className="space-y-1">
          <Link
            to="/"
            className="block rounded px-3 py-2 text-sm text-text-primary hover:bg-surface-hover"
          >
            New Screening
          </Link>
          <Link
            to="/history"
            className="block rounded px-3 py-2 text-sm text-text-primary hover:bg-surface-hover"
          >
            History
          </Link>
          {user?.role === 'admin' && (
            <Link
              to="/admin"
              className="block rounded px-3 py-2 text-sm text-text-primary hover:bg-surface-hover"
            >
              Admin
            </Link>
          )}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border bg-surface px-6 py-3">
          <div className="text-sm text-text-secondary">
            {user?.name} · {user?.badge_id}
          </div>
          <button
            onClick={handleLogout}
            className="rounded px-3 py-1.5 text-sm text-text-secondary hover:bg-surface-hover hover:text-text-primary"
          >
            Logout
          </button>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}

import { type ReactNode, useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useThemeStore } from '../store/themeStore';
import {
  LayoutDashboard,
  PlusCircle,
  Clock,
  BarChart3,
  Brain,
  Activity,
  ShieldAlert,
  Users,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Moon,
  Sun,
  Bell,
  Shield,
} from 'lucide-react';

interface NavItem {
  to: string;
  icon: ReactNode;
  label: string;
  adminOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', icon: <LayoutDashboard size={16} />, label: 'Dashboard' },
  { to: '/screening/new', icon: <PlusCircle size={16} />, label: 'New Screening' },
  { to: '/history', icon: <Clock size={16} />, label: 'Screening History' },
  { to: '/analytics', icon: <BarChart3 size={16} />, label: 'Analytics' },
  { to: '/system-intelligence', icon: <Brain size={16} />, label: 'System Intelligence' },
  { to: '/system', icon: <Activity size={16} />, label: 'System Status' },
];

const ADMIN_ITEMS: NavItem[] = [
  { to: '/admin/audit', icon: <ShieldAlert size={16} />, label: 'Audit Logs', adminOnly: true },
  { to: '/admin', icon: <Users size={16} />, label: 'Officer Management', adminOnly: true },
];

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/screening/new': 'New Screening',
  '/history': 'Screening History',
  '/analytics': 'Analytics',
  '/system-intelligence': 'System Intelligence',
  '/system': 'System Status',
  '/admin': 'Administration',
  '/admin/audit': 'Audit Logs',
};

function getPageTitle(pathname: string): string {
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];
  if (pathname.includes('/processing')) return 'Processing';
  if (pathname.includes('/analysis')) return 'Document Analysis';
  if (pathname.includes('/face')) return 'Face Verification';
  if (pathname.includes('/report')) return 'Risk Report';
  return 'SentinelID';
}

interface SidebarLinkProps {
  to: string;
  icon: ReactNode;
  label: string;
  collapsed: boolean;
}

function SidebarNavLink({ to, icon, label, collapsed }: SidebarLinkProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `sidebar-link${isActive ? ' active' : ''}`
      }
      title={collapsed ? label : undefined}
      style={{ justifyContent: collapsed ? 'center' : undefined }}
    >
      <span className="link-icon">{icon}</span>
      {!collapsed && <span style={{ transition: 'opacity 0.2s', whiteSpace: 'nowrap' }}>{label}</span>}
    </NavLink>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuthStore();
  const { theme, toggle: toggleTheme } = useThemeStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  function handleLogout() {
    logout();
    navigate('/login');
  }

  const pageTitle = getPageTitle(location.pathname);
  const isAdmin = user?.role === 'admin';

  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        background: 'var(--bg-primary)',
        color: 'var(--text-primary)',
      }}
    >
      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside
        className="sidebar"
        style={{ width: collapsed ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)' }}
      >
        {/* Logo */}
        <div
          style={{
            padding: collapsed ? '1rem 0.75rem' : '1.25rem 1rem',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.625rem',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 7,
              background: 'linear-gradient(135deg, var(--accent-primary), #6366f1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Shield size={15} color="white" />
          </div>
          {!collapsed && (
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontWeight: 700, fontSize: '0.875rem', letterSpacing: '-0.01em', color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
                SentinelID
              </div>
              <div style={{ fontSize: '0.625rem', color: 'var(--text-muted)', letterSpacing: '0.04em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
                SSB · MHA
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: '0.75rem 0.625rem', overflowY: 'auto', overflowX: 'hidden' }}>
          {!collapsed && (
            <div style={{ fontSize: '0.6rem', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', padding: '0.25rem 0.5rem 0.5rem', marginBottom: '0.25rem' }}>
              Operations
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.125rem' }}>
            {NAV_ITEMS.map((item) => (
              <SidebarNavLink key={item.to} {...item} collapsed={collapsed} />
            ))}
          </div>

          {isAdmin && (
            <>
              <div style={{ height: '1px', background: 'var(--border-default)', margin: '0.75rem 0.5rem' }} />
              {!collapsed && (
                <div style={{ fontSize: '0.6rem', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', padding: '0.25rem 0.5rem 0.5rem' }}>
                  Admin
                </div>
              )}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.125rem' }}>
                {ADMIN_ITEMS.map((item) => (
                  <SidebarNavLink key={item.to} {...item} collapsed={collapsed} />
                ))}
              </div>
            </>
          )}
        </nav>

        {/* Officer Info + Logout */}
        <div
          style={{
            padding: collapsed ? '0.75rem' : '0.875rem 1rem',
            borderTop: '1px solid var(--border-default)',
          }}
        >
          {!collapsed && user && (
            <div style={{ marginBottom: '0.625rem' }}>
              <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.name}
              </div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '0.125rem' }}>
                {user.badge_id}
              </div>
              <div style={{ marginTop: '0.25rem' }}>
                <span className="badge badge-info" style={{ fontSize: '0.6rem', padding: '0.125rem 0.375rem' }}>
                  {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                </span>
              </div>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="btn-ghost btn btn-sm"
            style={{
              width: '100%',
              justifyContent: collapsed ? 'center' : 'flex-start',
              color: 'var(--text-muted)',
              gap: '0.5rem',
              padding: '0.375rem 0.5rem',
            }}
            title="Sign out"
          >
            <LogOut size={14} />
            {!collapsed && <span>Sign Out</span>}
          </button>
        </div>

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{
            position: 'absolute',
            top: '4.25rem',
            right: -12,
            width: 24,
            height: 24,
            borderRadius: '50%',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-default)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-muted)',
            zIndex: 50,
            transition: 'all var(--transition-fast)',
          }}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
        </button>
      </aside>

      {/* ── Main Area ─────────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
        {/* Topbar */}
        <header className="topbar">
          <div style={{ flex: 1 }}>
            <h1 style={{
              fontSize: '0.9375rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
              margin: 0,
              letterSpacing: '-0.01em',
            }}>
              {pageTitle}
            </h1>
          </div>

          {/* System operational indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            <span className="status-dot status-dot-operational" />
            <span>System Operational</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className="btn-ghost btn btn-icon"
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              style={{ color: 'var(--text-muted)' }}
            >
              {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            </button>

            {/* Notification icon */}
            <button className="btn-ghost btn btn-icon" style={{ color: 'var(--text-muted)' }} title="Notifications">
              <Bell size={16} />
            </button>

            {/* Profile area */}
            {user && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.25rem 0.625rem',
                  borderRadius: 8,
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-default)',
                }}
              >
                <div
                  style={{
                    width: 24,
                    height: 24,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, var(--accent-primary), #6366f1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.6875rem',
                    fontWeight: 700,
                    color: 'white',
                    flexShrink: 0,
                  }}
                >
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div style={{ lineHeight: 1.2 }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {user.name.split(' ')[0]}
                  </div>
                  <div style={{ fontSize: '0.625rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {user.badge_id}
                  </div>
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Page Content */}
        <main
          style={{
            flex: 1,
            padding: '1.5rem',
            overflowY: 'auto',
          }}
          className="page-enter"
        >
          {children}
        </main>
      </div>
    </div>
  );
}

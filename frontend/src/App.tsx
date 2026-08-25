import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import NewScreening from './pages/NewScreening';
import Processing from './pages/Processing';
import DocumentAnalysis from './pages/DocumentAnalysis';
import FaceVerification from './pages/FaceVerification';
import RiskReport from './pages/RiskReport';
import History from './pages/History';
import Analytics from './pages/Analytics';
import SystemIntelligence from './pages/SystemIntelligence';
import SystemStatus from './pages/SystemStatus';
import Admin from './pages/Admin';
import ProtectedRoute from './components/ProtectedRoute';
import AppShell from './components/AppShell';
import ToastContainer from './components/shared/Toast';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<Login />} />

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* Protected routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <AppShell><Dashboard /></AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/screening/new"
          element={
            <ProtectedRoute>
              <AppShell><NewScreening /></AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/screening/:sessionId/processing"
          element={
            <ProtectedRoute>
              <AppShell><Processing /></AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/screening/:sessionId/analysis"
          element={
            <ProtectedRoute>
              <AppShell><DocumentAnalysis /></AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/screening/:sessionId/face"
          element={
            <ProtectedRoute>
              <AppShell><FaceVerification /></AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/screening/:sessionId/report"
          element={
            <ProtectedRoute>
              <AppShell><RiskReport /></AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <AppShell><History /></AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <AppShell><Analytics /></AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/system-intelligence"
          element={
            <ProtectedRoute>
              <AppShell><SystemIntelligence /></AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/system"
          element={
            <ProtectedRoute>
              <AppShell><SystemStatus /></AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AppShell><Admin /></AppShell>
            </ProtectedRoute>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>

      {/* Global toast notifications */}
      <ToastContainer />
    </BrowserRouter>
  );
}

export default App;

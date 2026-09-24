import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useSearchParams } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { BotProvider } from './context/BotContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Landing from './pages/Landing';
import Onboarding from './pages/Onboarding';
import Training from './pages/Training';
import WorkflowBuilder from './pages/WorkflowBuilder';
import WorkflowsList from './pages/WorkflowsList';
import BotTester from './pages/BotTester';
import PublicBot from './pages/PublicBot';
import CreatorLayout from './components/creator/CreatorLayout';
import CreatorOverview from './pages/creator/CreatorOverview';
import CreatorConfig from './pages/creator/CreatorConfig';
import CreatorKnowledge from './pages/creator/CreatorKnowledge';
import CreatorPublication from './pages/creator/CreatorPublication';
import CreatorChannels from './pages/creator/CreatorChannels';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-navy flex items-center justify-center">
        <div className="text-white/50">Cargando...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-navy flex items-center justify-center">
        <div className="text-white/50">Cargando...</div>
      </div>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

/**
 * LegacyRedirectTraining — Redirige /training?bot_id=X a /bots/X/training.
 * Si no hay bot_id, redirige a /dashboard.
 */
function LegacyRedirectTraining() {
  const [searchParams] = useSearchParams();
  const botId = searchParams.get('bot_id');
  if (botId) {
    return <Navigate to={`/bots/${botId}/training`} replace />;
  }
  return <Navigate to="/dashboard" replace />;
}

function AppContent() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <PublicRoute>
            <Landing />
          </PublicRoute>
        }
      />
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        }
      />
      {/* Bot Tester → /bots/:botId/tester */}
      <Route
        path="/bots/:botId/tester"
        element={
          <ProtectedRoute>
            <BotTester />
          </ProtectedRoute>
        }
      />

      {/* ============================================================ */}
      {/* CREATOR WORKSPACE (14.12.5) - nuevas rutas bajo /bots/:botId */}
      {/* ============================================================ */}

      <Route
        path="/bots/:botId"
        element={
          <ProtectedRoute>
            <CreatorLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<CreatorOverview />} />
        <Route path="config" element={<CreatorConfig />} />
        <Route path="knowledge" element={<CreatorKnowledge />} />
        <Route path="publication" element={<CreatorPublication />} />
        <Route path="channels" element={<CreatorChannels />} />
      </Route>

      {/* Sub-rutas que reutilizan páginas existentes con CreatorLayout */}
      <Route
        path="/bots/:botId/workflows"
        element={
          <ProtectedRoute>
            <CreatorLayout>
              <WorkflowsList />
            </CreatorLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/bots/:botId/workflows/new"
        element={
          <ProtectedRoute>
            <CreatorLayout>
              <WorkflowBuilder />
            </CreatorLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/bots/:botId/workflows/:workflowId"
        element={
          <ProtectedRoute>
            <CreatorLayout>
              <WorkflowBuilder />
            </CreatorLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/bots/:botId/training"
        element={
          <ProtectedRoute>
            <CreatorLayout>
              <Training />
            </CreatorLayout>
          </ProtectedRoute>
        }
      />

      {/* ============================================================ */}
      {/* LEGACY REDIRECTS (14.12.5) - mantienen URLs antiguas vivas     */}
      {/* Revisión de eliminación: fase 14.14                            */}
      {/* ============================================================ */}

      <Route
        path="/training"
        element={<LegacyRedirectTraining />}
      />

      <Route
        path="/workflows/:botId"
        element={<Navigate to="/bots/:botId/workflows" replace />}
      />

      <Route
        path="/workflows/:botId/new"
        element={<Navigate to="/bots/:botId/workflows/new" replace />}
      />

      <Route
        path="/workflows/:botId/:workflowId"
        element={<Navigate to="/bots/:botId/workflows/:workflowId" replace />}
      />

      {/* Bot Público → /b/:identifier (sin auth) */}
      <Route path="/b/:identifier" element={<PublicBot />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <BotProvider>
          <AppContent />
        </BotProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { BotProvider } from './context/BotContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Landing from './pages/Landing';
import Onboarding from './pages/Onboarding';
import Training from './pages/Training';
import WorkflowBuilder from './pages/WorkflowBuilder';
import WorkflowsList from './pages/WorkflowsList';

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
      <Route
        path="/training"
        element={
          <ProtectedRoute>
            <Training />
          </ProtectedRoute>
        }
      />

      {/* Workflows: lista → /workflows/:botId */}
      <Route
        path="/workflows/:botId"
        element={
          <ProtectedRoute>
            <WorkflowsList />
          </ProtectedRoute>
        }
      />

      {/* Workflows: nuevo → /workflows/:botId/new */}
      <Route
        path="/workflows/:botId/new"
        element={
          <ProtectedRoute>
            <WorkflowBuilder />
          </ProtectedRoute>
        }
      />

      {/* Workflows: editar existente → /workflows/:botId/:workflowId */}
      <Route
        path="/workflows/:botId/:workflowId"
        element={
          <ProtectedRoute>
            <WorkflowBuilder />
          </ProtectedRoute>
        }
      />

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

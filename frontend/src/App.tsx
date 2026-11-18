import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppLayout } from './components/Layout/AppLayout';
import { AuthPage } from './pages/AuthPage';
import { OverviewPage } from './pages/OverviewPage';
import { AgentsPage } from './pages/AgentsPage';
import { DatasetsPage } from './pages/DatasetsPage';
import { EvaluationsListPage } from './pages/EvaluationsListPage';
import { NewEvaluationPage } from './pages/NewEvaluationPage';
import { EvaluationDetailPage } from './pages/EvaluationDetailPage';
import { ModelComparisonPage } from './pages/ModelComparisonPage';
import { RegressionTestingPage } from './pages/RegressionTestingPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex flex-col items-center justify-center space-y-3">
        <div className="w-9 h-9 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></div>
        <span className="text-xs text-gray-400 font-mono tracking-wider">Loading AgentBench...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public route */}
            <Route path="/auth" element={<AuthPage />} />

            {/* Protected SaaS App routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<OverviewPage />} />
              <Route path="agents" element={<AgentsPage />} />
              <Route path="datasets" element={<DatasetsPage />} />
              <Route path="evaluations" element={<EvaluationsListPage />} />
              <Route path="evaluations/new" element={<NewEvaluationPage />} />
              <Route path="evaluations/:id" element={<EvaluationDetailPage />} />
              <Route path="compare" element={<ModelComparisonPage />} />
              <Route path="regression" element={<RegressionTestingPage />} />
              <Route path="analytics" element={<AnalyticsPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;

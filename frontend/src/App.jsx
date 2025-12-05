import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Signup from './pages/Signup';
import AdminDashboard from './pages/AdminDashboard';
import UserDashboard from './pages/UserDashboard';
import Movies from './pages/Movies';
import MovieDetail from './pages/MovieDetail';
import RequestPasswordReset from './pages/RequestPasswordReset';
import ResetPassword from './pages/ResetPassword';
import './App.css';

const RedirectToDashboard = () => {
  const { user, loading, isAdmin } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Navigate to={isAdmin() ? '/admin' : '/dashboard'} replace />;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public auth routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/forgot-password" element={<RequestPasswordReset />} />
          <Route path="/reset-password" element={<ResetPassword />} />

          {/* Protected app routes */}
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route
              path="/admin"
              element={
                <ProtectedRoute requireAdmin={true}>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />

            <Route path="/dashboard" element={<UserDashboard />} />
            <Route path="/movies" element={<Movies />} />
            <Route path="/movies/:movieId" element={<MovieDetail />} />
          </Route>

          {/* Root + fallback */}
          <Route path="/" element={<RedirectToDashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;

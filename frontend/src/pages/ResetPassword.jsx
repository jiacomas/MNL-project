import React, { useState } from 'react';
import axios from 'axios';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock } from 'lucide-react';
import { motion } from 'framer-motion';

const ResetPassword = () => {
  const { API_URL } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const initialToken = (location.state && location.state.token) || '';

  const [token, setToken] = useState(initialToken);
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await axios.post(`${API_URL}/auth/reset-password`, {
        token,
        new_password: password,
      });

      setSuccess('Password reset successfully. You can now log in.');
      setPassword('');
      setConfirm('');
    } catch (err) {
      console.error(err);
      setError(
        err?.response?.data?.detail ||
          'Could not reset password. Please check your token and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <motion.div
        className="login-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="login-header">
          <div className="logo-container">
            <Lock className="logo-icon" />
          </div>
          <h1>Set a new password</h1>
          <p>Paste the token from the reset link and choose a new password.</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="token">Reset token</label>
            <input
              id="token"
              type="text"
              className="auth-input"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">New password</label>
            <input
              id="password"
              type="password"
              className="auth-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirm">Confirm new password</label>
            <input
              id="confirm"
              type="password"
              className="auth-input"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              minLength={8}
              disabled={loading}
            />
          </div>

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <motion.button
            className="login-button"
            type="submit"
            disabled={loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {loading ? 'Resetting…' : 'Reset password'}
          </motion.button>
        </form>

        <div className="login-footer">
          <p>
            Back to <Link to="/login">Login</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default ResetPassword;

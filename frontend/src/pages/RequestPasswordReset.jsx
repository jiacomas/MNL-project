import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock } from 'lucide-react';
import { motion } from 'framer-motion';

const RequestPasswordReset = () => {
  const { API_URL } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [resetLink, setResetLink] = useState('');
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    setResetLink('');
    setToken('');

    try {
      const res = await axios.post(`${API_URL}/auth/request-reset`, {
        email,
      });

      const link = res.data?.reset_link || '';
      setResetLink(link);

      // pull the token id out of ".../reset-password/<token>"
      const parts = link.split('/');
      const lastPart = parts[parts.length - 1];
      if (lastPart && lastPart !== 'reset-password') {
        setToken(lastPart);
      }

      setSuccess('Reset link generated. Copy the token or link below.');
    } catch (err) {
      console.error(err);
      setError(
        err?.response?.data?.detail ||
          'Could not create reset link. Please check your email and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const goToConfirm = () => {
    if (token) {
      navigate('/reset-password', { state: { token } });
    } else {
      navigate('/reset-password');
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
          <h1>Forgot your password?</h1>
          <p>Enter your registered email and we’ll generate a reset link.</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              className="auth-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
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
            {loading ? 'Generating…' : 'Generate reset link'}
          </motion.button>
        </form>

        {resetLink && (
          <div className="reset-result">
            <p>
              <strong>Reset link (shown instead of sending email):</strong>
            </p>
            <code className="reset-code">{resetLink}</code>

            {token && (
              <>
                <p style={{ marginTop: '0.75rem' }}>
                  <strong>Token ID:</strong>
                </p>
                <code className="reset-code">{token}</code>

                <motion.button
                  type="button"
                  className="login-button"
                  style={{ marginTop: '0.75rem' }}
                  onClick={goToConfirm}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  Continue to set new password
                </motion.button>
              </>
            )}
          </div>
        )}

        <div className="login-footer">
          <p>
            Remembered your password? <Link to="/login">Back to login</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default RequestPasswordReset;

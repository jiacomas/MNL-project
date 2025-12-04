import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UserPlus, Mail, Lock } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';

const Signup = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { API_URL } = useAuth();
  const navigate = useNavigate();

  const validateLocal = () => {
    if (!username || !email || !password) return 'All fields are required';
    if (password !== confirm) return 'Passwords do not match';
    if (password.length < 6) return 'Password must be at least 6 characters';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const localErr = validateLocal();
    if (localErr) return setError(localErr);

    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/users/signup`, {
        username,
        email,
        password,
      });
      // On success, redirect to login
      navigate('/login');
    } catch (err) {
      console.error('Signup failed', err);
      const msg = err?.response?.data?.detail || 'Signup failed';
      setError(msg);
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
            <UserPlus className="logo-icon" />
          </div>
          <h1>Create Account</h1>
          <p>Sign up to get started</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">
              <UserPlus size={18} />
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Choose a username"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">
              <Mail size={18} />
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">
              <Lock size={18} />
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter a password"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirm">
              <Lock size={18} />
              Confirm Password
            </label>
            <input
              id="confirm"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Repeat password"
              required
              disabled={loading}
            />
          </div>

          {error && (
            <motion.div
              className="error-message"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
            >
              {error}
            </motion.div>
          )}

          <motion.button
            type="submit"
            className="login-button"
            disabled={loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {loading ? 'Creating...' : 'Sign Up'}
          </motion.button>
        </form>

        <div className="login-footer">
          <p>
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Signup;

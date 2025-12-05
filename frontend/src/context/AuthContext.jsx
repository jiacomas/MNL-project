import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    // Helpful debug: print detected API URL
    // (useful if VITE_API_URL is misconfigured)
    // eslint-disable-next-line no-console
    console.debug('Auth API_URL =', API_URL);
    if (token) {
      fetchCurrentUser(token);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchCurrentUser = async (token) => {
    try {
      const response = await axios.get(`${API_URL}/users/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      localStorage.removeItem('token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const url = `${API_URL}/users/token`;
      const response = await axios.post(url, formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      const { access_token } = response.data;
      localStorage.setItem('token', access_token);

      await fetchCurrentUser(access_token);
      return true;
    } catch (error) {
      // Provide more helpful debug info in console for 404s / network issues
      // eslint-disable-next-line no-console
      console.error('Login failed:', error);
      // eslint-disable-next-line no-console
      console.debug('Login request url:', `${API_URL}/users/token`);
      // eslint-disable-next-line no-console
      console.debug(
        'Axios error response:',
        error?.response?.data,
        error?.response?.status
      );
      return false;
    }
  };

  const logout = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        await axios.post(
          `${API_URL}/users/logout`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    localStorage.removeItem('token');
    setUser(null);
  };

  // Support different user payload shapes returned by backend
  // Some endpoints return `role`, others `user_type` (or `userType`). Treat any of
  // these as authoritative for admin detection.
  const isAdmin = () =>
    user?.role === 'admin' ||
    user?.user_type === 'admin' ||
    user?.userType === 'admin';

  return (
    <AuthContext.Provider
      value={{ user, login, logout, loading, isAdmin, API_URL }}
    >
      {children}
    </AuthContext.Provider>
  );
};

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
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    console.debug('Auth API_URL =', API_URL);
    if (storedToken) {
      setToken(storedToken);
      fetchCurrentUser(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchCurrentUser = async (tokenFromArg) => {
    try {
      const response = await axios.get(`${API_URL}/users/me`, {
        headers: { Authorization: `Bearer ${tokenFromArg}` },
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      localStorage.removeItem('token');
      setToken(null);
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
      setToken(access_token);

      await fetchCurrentUser(access_token);
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      console.debug('Login request url:', `${API_URL}/users/token`);
      console.debug(
        'Axios error response:',
        error?.response?.data,
        error?.response?.status
      );
      return false;
    }
  };

  const logout = async () => {
    const currentToken = localStorage.getItem('token');
    if (currentToken) {
      try {
        await axios.post(
          `${API_URL}/users/logout`,
          {},
          {
            headers: { Authorization: `Bearer ${currentToken}` },
          }
        );
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    localStorage.removeItem('token');
    setUser(null);
    setToken(null);
  };

  const isAdmin = () => user?.role === 'admin';

  return (
    <AuthContext.Provider
      value={{ user, token, login, logout, loading, isAdmin, API_URL }}
    >
      {children}
    </AuthContext.Provider>
  );
};

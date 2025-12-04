import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Users, Shield, Activity, UserX, Film } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';
import MovieManagement from '../components/MovieManagement';

const AdminDashboard = () => {
  const { user, API_URL } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('users');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUsers(response.data.users || []);
    } catch (err) {
      setError('Failed to load users');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const stats = {
    total: users.length,
    admins: users.filter((u) => u.user_type === 'admin').length,
    customers: users.filter((u) => u.user_type === 'customer').length,
    locked: users.filter((u) => u.is_locked).length,
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div>
          <h1>Admin Dashboard</h1>
          <p>Welcome back, {user?.username}</p>
        </div>
        <div className="user-badge admin-badge">
          <Shield size={16} />
          Admin
        </div>
      </div>

      <div className="stats-grid">
        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="stat-icon users">
            <Users size={24} />
          </div>
          <div className="stat-content">
            <h3>Total Users</h3>
            <p className="stat-number">{stats.total}</p>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="stat-icon admins">
            <Shield size={24} />
          </div>
          <div className="stat-content">
            <h3>Admins</h3>
            <p className="stat-number">{stats.admins}</p>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="stat-icon customers">
            <Activity size={24} />
          </div>
          <div className="stat-content">
            <h3>Customers</h3>
            <p className="stat-number">{stats.customers}</p>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="stat-icon locked">
            <UserX size={24} />
          </div>
          <div className="stat-content">
            <h3>Locked Accounts</h3>
            <p className="stat-number">{stats.locked}</p>
          </div>
        </motion.div>
      </div>

      <div className="tabs-container">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            <Users size={18} />
            User Management
          </button>
          <button
            className={`tab ${activeTab === 'movies' ? 'active' : ''}`}
            onClick={() => setActiveTab('movies')}
          >
            <Film size={18} />
            Movie Management
          </button>
        </div>
      </div>

      {activeTab === 'users' ? (
        <div className="users-section">
          <h2>User Management</h2>

          {loading ? (
            <div className="loading">Loading users...</div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : (
            <div className="users-table-container">
              <table className="users-table">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>User ID</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u, index) => (
                    <motion.tr
                      key={u.user_id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <td className="username-cell">
                        <div className="user-avatar">
                          {u.username.charAt(0).toUpperCase()}
                        </div>
                        {u.username}
                      </td>
                      <td>{u.email}</td>
                      <td>
                        <span className={`type-badge ${u.user_type}`}>
                          {u.user_type}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`status-badge ${u.is_locked ? 'locked' : 'active'}`}
                        >
                          {u.is_locked ? 'Locked' : 'Active'}
                        </span>
                      </td>
                      <td className="user-id">
                        {u.user_id.substring(0, 8)}...
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <MovieManagement />
      )}
    </div>
  );
};

export default AdminDashboard;

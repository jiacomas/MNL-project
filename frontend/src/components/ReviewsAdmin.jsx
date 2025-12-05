import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Search, Download, Filter, Star, Calendar, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ReviewsAdmin = () => {
  const { API_URL } = useAuth();
  const [q, setQ] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [order, setOrder] = useState('desc');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [rows, setRows] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e) => {
    e && e.preventDefault();
    if (!q || q.trim().length === 0) return;
    setError('');
    setLoading(true);
    setHasSearched(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/admin/analytics/reviews/search`, {
        params: { q: q.trim(), sort: sortBy, order },
        headers: { Authorization: `Bearer ${token}` },
      });
      setRows(res.data || []);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to search reviews');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!q || q.trim().length === 0)
      return alert('Please enter a search query');
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/admin/analytics/reviews/export`, {
        params: { q: q.trim(), sort: sortBy, order },
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      });

      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'reviews_export.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to export CSV');
    }
  };

  return (
    <div className="reviews-admin-container">
      <motion.div
        className="reviews-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h2>Reviews Search</h2>
        <p>Search and manage user reviews across all movies</p>
      </motion.div>

      <motion.div
        className="search-panel"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <form onSubmit={handleSearch}>
          <div className="search-bar-wrapper">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              placeholder="Search by movie title..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
              className="search-input-field"
            />
          </div>

          <div className="filters-row">
            <div className="filter-group">
              <label>
                <Filter size={14} /> Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="filter-select"
              >
                <option value="date">Date</option>
                <option value="rating">Rating</option>
              </select>
            </div>

            <div className="filter-group">
              <label>
                <Filter size={14} /> Order
              </label>
              <select
                value={order}
                onChange={(e) => setOrder(e.target.value)}
                className="filter-select"
              >
                <option value="desc">Newest / Highest</option>
                <option value="asc">Oldest / Lowest</option>
              </select>
            </div>

            <div className="action-buttons">
              <button className="btn-search" type="submit" disabled={loading}>
                {loading ? 'Searching...' : 'Search Reviews'}
              </button>

              <button
                type="button"
                className="btn-export"
                onClick={handleExport}
                disabled={!hasSearched || rows.length === 0}
              >
                <Download size={16} /> Export CSV
              </button>
            </div>
          </div>
        </form>
      </motion.div>

      {error && (
        <motion.div
          className="error-banner"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {error}
        </motion.div>
      )}

      <div className="results-area">
        <AnimatePresence>
          {loading ? (
            <motion.div
              className="loading-state"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className="spinner"></div>
              <p>Searching database...</p>
            </motion.div>
          ) : rows.length > 0 ? (
            <motion.div
              className="table-wrapper"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <table className="modern-table">
                <thead>
                  <tr>
                    <th>Movie</th>
                    <th>Rating</th>
                    <th>User</th>
                    <th>Date</th>
                    <th>Review ID</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <motion.tr
                      key={r.id || `${r.movie_title}-${i}`}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <td className="movie-cell">
                        <span className="movie-title">{r.movie_title}</span>
                      </td>
                      <td>
                        <div className="rating-badge">
                          <Star size={12} fill="currentColor" />
                          {r.rating ?? 'N/A'}
                        </div>
                      </td>
                      <td>
                        <div className="user-info">
                          <User size={14} />
                          <span className="mono-text">
                            {r.user_id
                              ? r.user_id.substring(0, 8) + '...'
                              : 'Unknown'}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div className="date-info">
                          <Calendar size={14} />
                          {r.created_at
                            ? new Date(r.created_at).toLocaleDateString()
                            : '-'}
                        </div>
                      </td>
                      <td className="id-cell">
                        <span className="mono-text">
                          {r.id ? r.id.substring(0, 8) + '...' : '-'}
                        </span>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </motion.div>
          ) : hasSearched ? (
            <motion.div
              className="empty-state"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <p>No reviews found matching your criteria.</p>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ReviewsAdmin;

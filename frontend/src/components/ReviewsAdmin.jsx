import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Search, Download } from 'lucide-react';

const ReviewsAdmin = () => {
  const { API_URL } = useAuth();
  const [q, setQ] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [order, setOrder] = useState('desc');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [rows, setRows] = useState([]);

  const handleSearch = async (e) => {
    e && e.preventDefault();
    if (!q || q.trim().length === 0) return;
    setError('');
    setLoading(true);
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
    <div className="reviews-admin">
      <div className="reviews-header">
        <h2>Reviews Search</h2>
      </div>

      <form className="reviews-search" onSubmit={handleSearch}>
        <div className="search-row">
          <div className="search-input">
            <Search />
            <input
              type="text"
              placeholder="Search reviews by movie title..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>

          <div className="search-controls">
            <label>
              Sort
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="date">Date</option>
                <option value="rating">Rating</option>
              </select>
            </label>

            <label>
              Order
              <select value={order} onChange={(e) => setOrder(e.target.value)}>
                <option value="desc">Desc</option>
                <option value="asc">Asc</option>
              </select>
            </label>

            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? 'Searching...' : 'Search'}
            </button>

            <button
              type="button"
              className="btn-secondary"
              onClick={handleExport}
            >
              <Download /> Export CSV
            </button>
          </div>
        </div>
      </form>

      {error && <div className="error-message">{error}</div>}

      <div className="reviews-results">
        <table className="reviews-table">
          <thead>
            <tr>
              <th>Review ID</th>
              <th>Movie Title</th>
              <th>Rating</th>
              <th>Review Date</th>
              <th>User ID</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.id || `${r.movie_title}-${i}`}>
                <td className="mono">{r.id}</td>
                <td>{r.movie_title}</td>
                <td>{r.rating ?? 'N/A'}</td>
                <td>{r.created_at ? String(r.created_at).slice(0, 19) : ''}</td>
                <td className="mono">{r.user_id ?? ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ReviewsAdmin;

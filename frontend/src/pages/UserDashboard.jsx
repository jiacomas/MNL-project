import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { BookMarked, Star, Clock, Download, Film } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Recommendations from '../components/Recommendations';

const UserDashboard = () => {
  const { user, API_URL } = useAuth();
  const navigate = useNavigate();
  const [bookmarks, setBookmarks] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      // Fetch bookmarks (API) and user export (contains reviews & history)
      const [bookmarksRes, exportRes] = await Promise.all([
        axios
          .get(`${API_URL}/api/bookmarks`, { headers })
          .catch(() => ({ data: [] })),
        axios
          .get(`${API_URL}/users/me/export`, { headers })
          .catch(() => ({ data: { data: {} } })),
      ]);

      // Bookmarks endpoint returns an array of BookmarkOut
      setBookmarks(bookmarksRes.data || []);

      // Export payload has shape { meta, data: { reviews, bookmarks, history, ... } }
      const exported = exportRes.data?.data || {};
      setReviews(exported.reviews || []);
      setHistory(exported.history || []);
    } catch (err) {
      console.error('Failed to fetch user data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/export/user-data`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `user-data-${Date.now()}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to export data:', err);
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div>
          <h1>My Dashboard</h1>
          <p>Welcome back, {user?.username}</p>
        </div>
        <div className="header-actions">
          <motion.button
            className="export-button"
            onClick={handleExportData}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Download size={16} />
            Export Data
          </motion.button>
        </div>
      </div>

      <div className="stats-grid">
        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="stat-icon bookmarks">
            <BookMarked size={24} />
          </div>
          <div className="stat-content">
            <h3>Bookmarks</h3>
            <p className="stat-number">{bookmarks.length}</p>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="stat-icon reviews">
            <Star size={24} />
          </div>
          <div className="stat-content">
            <h3>Reviews</h3>
            <p className="stat-number">{reviews.length}</p>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="stat-icon history">
            <Clock size={24} />
          </div>
          <div className="stat-content">
            <h3>Watch History</h3>
            <p className="stat-number">{history.length}</p>
          </div>
        </motion.div>
      </div>

      <div className="quick-actions">
        <motion.button
          className="action-btn"
          onClick={() => navigate('/movies')}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Film size={20} />
          Browse Movies
        </motion.button>
      </div>

      <Recommendations />

      <div className="content-sections">
        <motion.div
          className="content-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h2>
            <BookMarked size={20} />
            My Bookmarks
          </h2>
          {loading ? (
            <div className="loading">Loading...</div>
          ) : bookmarks.length === 0 ? (
            <div className="empty-state">No bookmarks yet</div>
          ) : (
            <div className="items-grid">
              {bookmarks.slice(0, 6).map((bookmark, index) => (
                <motion.div
                  key={index}
                  className="item-card"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div className="item-title">
                    {bookmark.title || bookmark.movie_id}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>

        <motion.div
          className="content-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <h2>
            <Star size={20} />
            My Reviews
          </h2>
          {loading ? (
            <div className="loading">Loading...</div>
          ) : reviews.length === 0 ? (
            <div className="empty-state">No reviews yet</div>
          ) : (
            <div className="reviews-list">
              {reviews.slice(0, 5).map((review, index) => (
                <motion.div
                  key={index}
                  className="review-item"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div className="review-header">
                    <span className="review-movie">{review.movie_name}</span>
                    <span className="review-rating">★ {review.rating}/10</span>
                  </div>
                  <p className="review-text">{review.comment}</p>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default UserDashboard;

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { BookMarked, Star, Clock, Film, List } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Recommendations from '../components/Recommendations';

const UserDashboard = () => {
  const { user, API_URL } = useAuth();
  const navigate = useNavigate();
  const [bookmarks, setBookmarks] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [history, setHistory] = useState([]);
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      // Fetch bookmarks and lists first
      const [bookmarksRes, listsRes] = await Promise.all([
        axios
          .get(`${API_URL}/api/bookmarks`, { headers })
          .catch(() => ({ data: [] })),
        axios
          .get(`${API_URL}/api/lists`, { headers })
          .catch(() => ({ data: [] })),
      ]);

      setBookmarks(bookmarksRes.data || []);
      setLists(listsRes.data || []);

      // Fetch viewing history via dedicated endpoint
      try {
        const uid = user?.user_id || user?.id || null;
        if (uid) {
          const historyRes = await axios.get(`${API_URL}/history/${uid}`, {
            headers,
          });
          setHistory(historyRes.data || []);
        } else {
          setHistory([]);
        }
      } catch (err) {
        console.warn('Failed to fetch history for user', err);
        setHistory([]);
      }

      // Fetch reviews
      setReviews([]);
      // Enrich bookmarks with movie titles by fetching movie metadata
      if ((bookmarksRes.data || []).length > 0) {
        try {
          const bm = bookmarksRes.data || [];
          const moviePromises = bm.map((b) =>
            axios
              .get(`${API_URL}/api/movies/${b.movie_id}`)
              .then((r) => ({ ...b, title: r.data.title }))
              .catch(() => ({ ...b, title: b.title || b.movie_id }))
          );
          const enriched = await Promise.all(moviePromises);
          setBookmarks(enriched || []);
        } catch (err) {
          // If enrichment fails, just keep original bookmarks
          console.warn('Failed to enrich bookmarks with movie titles', err);
        }
      }
    } catch (err) {
      console.error('Failed to fetch user data:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div>
          <h1>My Dashboard</h1>
          <p>Welcome back, {user?.username}</p>
        </div>
        <div className="header-actions" />
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
          <div className="stat-icon lists">
            <List size={24} />
          </div>
          <div className="stat-content">
            <h3>My Lists</h3>
            <p className="stat-number">{lists.length}</p>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
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
          transition={{ delay: 0.4 }}
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
        <motion.button
          className="action-btn"
          onClick={() => navigate('/lists')}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <List size={20} />
          Manage Lists
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
                <motion.button
                  key={bookmark.id || index}
                  type="button"
                  className="item-card clickable"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => navigate(`/movies/${bookmark.movie_id}`)}
                  aria-label={`Open details for ${bookmark.title || bookmark.movie_id}`}
                >
                  <div className="item-title">
                    {bookmark.title || bookmark.movie_id}
                  </div>
                </motion.button>
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
                  {review.title_review && (
                    <h4 className="review-title">{review.title_review}</h4>
                  )}
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

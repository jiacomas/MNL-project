import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Star, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';

const Recommendations = () => {
  const { user, API_URL } = useAuth();
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.user_id) {
      fetchRecommendations();
    }
  }, [user]);

  const fetchRecommendations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/users/${user.user_id}/recommendations`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setRecommendations(response.data || []);
    } catch (err) {
      console.error('Failed to fetch recommendations:', err);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading recommendations...</div>;
  }

  if (recommendations.length === 0) {
    return (
      <div className="recommendations-empty">
        <Sparkles size={48} />
        <h3>No Recommendations Yet</h3>
        <p>Rate some movies to get personalized recommendations!</p>
      </div>
    );
  }

  return (
    <div className="recommendations-section">
      <div className="section-header">
        <h2>
          <Sparkles size={24} />
          Recommended for You
        </h2>
        <p>Based on your reviews and preferences</p>
      </div>

      <div className="recommendations-grid">
        {recommendations.map((rec, index) => (
          <motion.div
            key={rec.movie_id}
            className="recommendation-card"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -8, boxShadow: '0 12px 24px rgba(0,0,0,0.15)' }}
            onClick={() => navigate(`/movies/${rec.movie_id}`)}
          >
            <div className="recommendation-badge">
              <Sparkles size={14} />
              Recommended
            </div>

            <div className="recommendation-content">
              <h3>{rec.title}</h3>

              <div className="recommendation-meta">
                <span className="genre-tag">{rec.genre}</span>
                <span className="year-tag">{rec.release_year}</span>
              </div>

              {rec.average_rating && (
                <div className="recommendation-rating">
                  <Star size={16} fill="currentColor" />
                  <span>{rec.average_rating.toFixed(1)}</span>
                </div>
              )}

              {rec.reason && (
                <p className="recommendation-reason">{rec.reason}</p>
              )}
            </div>

            <motion.button
              className="btn-view-rec"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              View Details
            </motion.button>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default Recommendations;

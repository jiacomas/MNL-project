import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Star,
  BookmarkPlus,
  BookmarkCheck,
  Edit2,
  Trash2,
  ArrowLeft,
  ListPlus,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import AddToListModal from '../components/AddToListModal';

const MovieDetail = () => {
  const { movieId } = useParams();
  const { user, API_URL } = useAuth();
  const navigate = useNavigate();

  const [movie, setMovie] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [myReview, setMyReview] = useState(null);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [showAddToList, setShowAddToList] = useState(false);
  const [reviewForm, setReviewForm] = useState({
    rating: 5,
    title_review: '',
    comment: '',
  });

  useEffect(() => {
    fetchMovieData();
  }, [movieId]);

  const fetchMovieData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      // Fetch movie details
      const movieRes = await axios.get(`${API_URL}/api/movies/${movieId}`);
      setMovie(movieRes.data);

      // Fetch reviews for this movie (encode title for URL)
      const movieName = encodeURIComponent(movieRes.data.title || movieId);
      const reviewsRes = await axios.get(
        `${API_URL}/api/movies/${movieName}/reviews`,
        { headers }
      );
      const allReviews = reviewsRes.data.items || [];

      // Fetch my review
      let myReviewData = null;
      try {
        const myReviewRes = await axios.get(
          `${API_URL}/api/movies/${movieName}/reviews/me`,
          { headers }
        );
        myReviewData = myReviewRes.data || null;
        setMyReview(myReviewData);
      } catch (err) {
        // No review yet
        myReviewData = null;
        setMyReview(null);
      }

      // Sort reviews newest-first (by created_at).
      const sortDesc = (a, b) => {
        const ta = a?.created_at ? new Date(a.created_at).getTime() : 0;
        const tb = b?.created_at ? new Date(b.created_at).getTime() : 0;
        return tb - ta;
      };

      if (myReviewData) {
        // Make a robust de-duplication: match by review_id when available,
        // otherwise fall back to user_id/username matching.
        const others = (allReviews || []).filter((r) => {
          if (!r) return false;
          if (myReviewData.review_id && r.review_id) {
            return r.review_id !== myReviewData.review_id;
          }
          // Fallback to user id / username matching
          const rUser = r.user_id || r.username;
          const myUser =
            myReviewData.user_id ||
            myReviewData.username ||
            (user && (user.user_id || user.id || user.username));
          return rUser !== myUser;
        });
        others.sort(sortDesc);
        setReviews([myReviewData, ...others]);
      } else {
        setReviews((allReviews || []).sort(sortDesc));
      }

      // Check if bookmarked
      try {
        const bookmarkRes = await axios.get(
          `${API_URL}/api/bookmarks/me?movie_id=${movieId}`,
          { headers }
        );
        setIsBookmarked(!!bookmarkRes.data);
      } catch (err) {
        setIsBookmarked(false);
      }
    } catch (err) {
      console.error('Failed to fetch movie data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const titleForPath = encodeURIComponent(
        (movie && movie.title) || movieId
      );

      let res;
      if (myReview) {
        // Update existing review
        res = await axios.patch(
          `${API_URL}/api/movies/${titleForPath}/reviews/${myReview.review_id}`,
          reviewForm,
          { headers }
        );
      } else {
        // Create new review
        res = await axios.post(
          `${API_URL}/api/movies/${titleForPath}/reviews`,
          reviewForm,
          { headers }
        );
      }

      // Update local state optimistically and refresh list
      if (res && res.data) {
        setMyReview(res.data);
      }
      setShowReviewForm(false);
      // refresh reviews and myReview from server to keep indexes consistent
      await fetchMovieData();
    } catch (err) {
      console.error('Failed to submit review:', err);
      alert(err.response?.data?.detail || 'Failed to submit review');
    }
  };

  const handleDeleteReview = async () => {
    if (!window.confirm('Are you sure you want to delete your review?')) return;

    try {
      const token = localStorage.getItem('token');
      await axios.delete(
        `${API_URL}/api/movies/${encodeURIComponent(movie.title)}/reviews`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setMyReview(null);
      fetchMovieData();
    } catch (err) {
      console.error('Failed to delete review:', err);
    }
  };

  const handleToggleBookmark = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      if (isBookmarked) {
        // Remove bookmark - need to find bookmark ID first
        const bookmarksRes = await axios.get(`${API_URL}/api/bookmarks`, {
          headers,
        });
        const bookmark = bookmarksRes.data.find((b) => b.movie_id === movieId);
        if (bookmark) {
          await axios.delete(
            `${API_URL}/api/bookmarks/me/${bookmark.bookmark_id}`,
            {
              headers,
            }
          );
        }
        setIsBookmarked(false);
      } else {
        // Add bookmark
        await axios.post(
          `${API_URL}/api/bookmarks`,
          { movie_id: movieId },
          { headers }
        );
        setIsBookmarked(true);
      }
    } catch (err) {
      console.error('Failed to toggle bookmark:', err);
      alert(err.response?.data?.detail || 'Failed to update bookmark');
    }
  };

  const handleEditReview = () => {
    setReviewForm({
      rating: myReview.rating,
      title_review: myReview.title_review || '',
      comment: myReview.comment,
    });
    setShowReviewForm(true);
  };

  if (loading) {
    return <div className="loading">Loading movie details...</div>;
  }

  if (!movie) {
    return <div className="error-message">Movie not found</div>;
  }

  return (
    <div className="movie-detail-page">
      <motion.button
        className="btn-back"
        onClick={() => navigate('/movies')}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <ArrowLeft size={20} />
        Back to Movies
      </motion.button>

      <motion.div
        className="movie-detail-header"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="movie-title-section">
          <h1>{movie.title}</h1>
          <div className="movie-meta">
            <span className="genre-badge">{movie.movieGenres}</span>
            <span className="year-badge">
              {(movie.datePublished || '').slice(0, 4)}
            </span>
            <span className="runtime-badge">{movie.duration} min</span>
          </div>
        </div>

        <div className="movie-actions">
          {movie.movieIMDbRating != null && (
            <div className="rating-display">
              <Star size={24} fill="currentColor" />
              <span>{Number(movie.movieIMDbRating).toFixed(1)}</span>
            </div>
          )}

          <motion.button
            className="btn-bookmark"
            onClick={() => setShowAddToList(true)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            title="Add to List"
          >
            <ListPlus size={20} />
            Add to List
          </motion.button>

          <motion.button
            className={`btn-bookmark ${isBookmarked ? 'bookmarked' : ''}`}
            onClick={handleToggleBookmark}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {isBookmarked ? (
              <>
                <BookmarkCheck size={20} />
                Bookmarked
              </>
            ) : (
              <>
                <BookmarkPlus size={20} />
                Bookmark
              </>
            )}
          </motion.button>
        </div>
      </motion.div>

      <AnimatePresence>
        {showAddToList && (
          <AddToListModal
            movieId={movieId}
            onClose={() => setShowAddToList(false)}
          />
        )}
      </AnimatePresence>

      {movie.description && (
        <motion.div
          className="movie-description"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <p>{movie.description}</p>
        </motion.div>
      )}

      <motion.div
        className="reviews-section"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <div className="section-header">
          <h2>Reviews</h2>
          {!myReview && !showReviewForm && (
            <motion.button
              className="btn-primary"
              onClick={() => setShowReviewForm(true)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Star size={18} />
              Write a Review
            </motion.button>
          )}
        </div>

        {myReview && !showReviewForm && (
          <div className="my-review">
            <div className="review-header">
              <h3>Your Review</h3>
              <div className="review-actions">
                <button className="btn-icon" onClick={handleEditReview}>
                  <Edit2 size={16} />
                </button>
                <button
                  className="btn-icon delete"
                  onClick={handleDeleteReview}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
            <div className="review-rating">
              {[...Array(10)].map((_, i) => (
                <Star
                  key={i}
                  size={16}
                  fill={i < myReview.rating ? 'currentColor' : 'none'}
                />
              ))}
              <span>{myReview.rating}/10</span>
            </div>
            {myReview.title_review && (
              <h4 className="review-title">{myReview.title_review}</h4>
            )}
            <p className="review-text">{myReview.comment}</p>
          </div>
        )}

        {showReviewForm && (
          <motion.form
            className="review-form"
            onSubmit={handleSubmitReview}
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="form-group">
              <label>Rating (1-10)</label>
              <div className="rating-input">
                {[...Array(10)].map((_, i) => (
                  <motion.button
                    key={i}
                    type="button"
                    className={`star-btn ${i < reviewForm.rating ? 'active' : ''}`}
                    onClick={() =>
                      setReviewForm({ ...reviewForm, rating: i + 1 })
                    }
                    whileHover={{ scale: 1.2 }}
                    whileTap={{ scale: 0.9 }}
                  >
                    <Star
                      size={24}
                      fill={i < reviewForm.rating ? 'currentColor' : 'none'}
                    />
                  </motion.button>
                ))}
                <span className="rating-value">{reviewForm.rating}/10</span>
              </div>
            </div>

            <div className="form-group">
              <label>Review Title (optional)</label>
              <input
                type="text"
                value={reviewForm.title_review}
                onChange={(e) =>
                  setReviewForm({ ...reviewForm, title_review: e.target.value })
                }
                placeholder="Short title for your review"
                maxLength={120}
              />

              <label>Your Review</label>
              <textarea
                value={reviewForm.comment}
                onChange={(e) =>
                  setReviewForm({ ...reviewForm, comment: e.target.value })
                }
                rows="4"
                placeholder="Share your thoughts about this movie..."
                required
              />
            </div>

            <div className="form-actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowReviewForm(false)}
              >
                Cancel
              </button>
              <motion.button
                type="submit"
                className="btn-primary"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {myReview ? 'Update Review' : 'Submit Review'}
              </motion.button>
            </div>
          </motion.form>
        )}

        <div className="other-reviews">
          <h3>All Reviews ({reviews.length})</h3>
          {reviews.length === 0 ? (
            <div className="empty-state">No reviews yet. Be the first!</div>
          ) : (
            <div className="reviews-list">
              {reviews.map((review, index) => (
                <motion.div
                  key={review.review_id}
                  className="review-item"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <div className="review-header">
                    <div className="reviewer-info">
                      <div className="reviewer-avatar">
                        {(
                          (review.username === user?.user_id
                            ? user?.username
                            : review.username) || 'U'
                        )
                          .charAt(0)
                          .toUpperCase()}
                      </div>
                      <span className="reviewer-name">
                        {review.username === user?.user_id
                          ? 'You'
                          : review.username || 'User'}
                      </span>
                    </div>
                    <div className="review-rating">
                      <Star size={16} fill="currentColor" />
                      {review.rating}/10
                    </div>
                  </div>
                  {review.title_review && (
                    <h4 className="review-title">{review.title_review}</h4>
                  )}
                  <p className="review-text">{review.comment}</p>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default MovieDetail;

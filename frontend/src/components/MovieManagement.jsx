import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Plus, Edit2, Trash2, Search, X, Save } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const MovieManagement = () => {
  const { API_URL } = useAuth();
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingMovie, setEditingMovie] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    genre: '',
    release_year: '',
    runtime: '',
    description: '',
  });

  useEffect(() => {
    fetchMovies();
  }, []);

  const fetchMovies = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/movies`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMovies(response.data.items || []);
    } catch (err) {
      setError('Failed to load movies');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      if (editingMovie) {
        // Update existing movie
        await axios.patch(
          `${API_URL}/api/movies/${editingMovie.movie_id}`,
          formData,
          { headers }
        );
      } else {
        // Create new movie
        await axios.post(`${API_URL}/api/movies`, formData, { headers });
      }

      resetForm();
      fetchMovies();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save movie');
      console.error(err);
    }
  };

  const handleEdit = (movie) => {
    setEditingMovie(movie);
    setFormData({
      title: movie.title,
      genre: movie.genre,
      release_year: movie.release_year,
      runtime: movie.runtime,
      description: movie.description || '',
    });
    setShowAddModal(true);
  };

  const handleDelete = async (movieId) => {
    if (!window.confirm('Are you sure you want to delete this movie?')) return;

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/movies/${movieId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchMovies();
    } catch (err) {
      setError('Failed to delete movie');
      console.error(err);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      genre: '',
      release_year: '',
      runtime: '',
      description: '',
    });
    setEditingMovie(null);
    setShowAddModal(false);
    setError('');
  };

  const filteredMovies = movies.filter((movie) =>
    movie.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="movie-management">
      <div className="management-header">
        <h2>Movie Management</h2>
        <motion.button
          className="btn-primary"
          onClick={() => setShowAddModal(true)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Plus size={20} />
          Add Movie
        </motion.button>
      </div>

      <div className="search-bar">
        <Search size={20} />
        <input
          type="text"
          placeholder="Search movies..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Loading movies...</div>
      ) : (
        <div className="movies-table-container">
          <table className="movies-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Genre</th>
                <th>Year</th>
                <th>Runtime</th>
                <th>Rating</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredMovies.map((movie, index) => (
                <motion.tr
                  key={movie.movie_id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <td className="movie-title">{movie.title}</td>
                  <td>{movie.genre}</td>
                  <td>{movie.release_year}</td>
                  <td>{movie.runtime} min</td>
                  <td>
                    <span className="rating-badge">
                      ★ {movie.average_rating?.toFixed(1) || 'N/A'}
                    </span>
                  </td>
                  <td className="actions-cell">
                    <motion.button
                      className="btn-icon edit"
                      onClick={() => handleEdit(movie)}
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                    >
                      <Edit2 size={16} />
                    </motion.button>
                    <motion.button
                      className="btn-icon delete"
                      onClick={() => handleDelete(movie.movie_id)}
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                    >
                      <Trash2 size={16} />
                    </motion.button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <AnimatePresence>
        {showAddModal && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={resetForm}
          >
            <motion.div
              className="modal-content"
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h3>{editingMovie ? 'Edit Movie' : 'Add New Movie'}</h3>
                <button className="btn-close" onClick={resetForm}>
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="movie-form">
                <div className="form-group">
                  <label>Title *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData({ ...formData, title: e.target.value })
                    }
                    required
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Genre *</label>
                    <input
                      type="text"
                      value={formData.genre}
                      onChange={(e) =>
                        setFormData({ ...formData, genre: e.target.value })
                      }
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Release Year *</label>
                    <input
                      type="number"
                      value={formData.release_year}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          release_year: parseInt(e.target.value),
                        })
                      }
                      min="1900"
                      max="2100"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Runtime (minutes) *</label>
                  <input
                    type="number"
                    value={formData.runtime}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        runtime: parseInt(e.target.value),
                      })
                    }
                    min="1"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    rows="4"
                  />
                </div>

                <div className="form-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={resetForm}
                  >
                    Cancel
                  </button>
                  <motion.button
                    type="submit"
                    className="btn-primary"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Save size={16} />
                    {editingMovie ? 'Update Movie' : 'Add Movie'}
                  </motion.button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MovieManagement;

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  Edit2,
  Trash2,
  Plus,
  Save,
  X,
  MoreVertical,
  Film,
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import * as listsService from '../services/listsService';

const ListDetail = () => {
  const { listId } = useParams();
  const navigate = useNavigate();
  const { API_URL } = useAuth();
  const [list, setList] = useState(null);
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchListDetails();
  }, [listId]);

  const fetchListDetails = async () => {
    try {
      setLoading(true);
      setError('');
      const listData = await listsService.getList(listId);
      setList(listData);
      setEditName(listData.name);
      setEditDescription(listData.description || '');

      // Fetch movie details for each item in the list
      if (listData.items && listData.items.length > 0) {
        const moviePromises = listData.items.map((movieId) =>
          axios
            .get(`${API_URL}/api/movies/${movieId}`, {
              headers: {
                Authorization: `Bearer ${localStorage.getItem('token')}`,
              },
            })
            .then((res) => ({ ...res.data, id: movieId }))
            .catch(() => ({ id: movieId, title: 'Unknown Movie' }))
        );
        const moviesData = await Promise.all(moviePromises);
        setMovies(moviesData);
      } else {
        setMovies([]);
      }
    } catch (err) {
      console.error('Failed to fetch list details:', err);
      setError(
        err.response?.status === 404
          ? 'List not found'
          : 'Failed to load list details'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateList = async (e) => {
    e.preventDefault();
    if (!editName.trim()) return;

    try {
      setSaving(true);
      const updatedList = await listsService.updateList(listId, {
        name: editName,
        description: editDescription,
      });
      setList(updatedList);
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to update list:', err);
      alert('Failed to update list details');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteList = async () => {
    if (
      !window.confirm(
        'Are you sure you want to delete this list? This cannot be undone.'
      )
    ) {
      return;
    }

    try {
      await listsService.deleteList(listId);
      navigate('/lists');
    } catch (err) {
      console.error('Failed to delete list:', err);
      alert('Failed to delete list');
    }
  };

  const handleRemoveMovie = async (movieId, movieTitle) => {
    if (!window.confirm(`Remove "${movieTitle}" from this list?`)) {
      return;
    }

    try {
      await listsService.removeMovieFromList(listId, movieId);
      setMovies((prev) => prev.filter((m) => m.id !== movieId));
      setList((prev) => ({
        ...prev,
        items: prev.items.filter((id) => id !== movieId),
      }));
    } catch (err) {
      console.error('Failed to remove movie:', err);
      alert('Failed to remove movie from list');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading list details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
        <button className="btn-primary" onClick={() => navigate('/lists')}>
          Back to Lists
        </button>
      </div>
    );
  }

  return (
    <div className="list-detail-container">
      <div className="list-detail-header">
        <motion.button
          className="back-btn"
          onClick={() => navigate('/lists')}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          <ArrowLeft size={24} />
        </motion.button>

        <div className="list-header-content">
          {isEditing ? (
            <form onSubmit={handleUpdateList} className="edit-list-form">
              <div className="form-group">
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  placeholder="List Name"
                  className="edit-name-input"
                  maxLength={100}
                  required
                  autoFocus
                />
              </div>
              <div className="form-group">
                <textarea
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  placeholder="Description"
                  className="edit-desc-input"
                  maxLength={500}
                  rows={2}
                />
              </div>
              <div className="edit-actions">
                <button
                  type="button"
                  className="btn-secondary small"
                  onClick={() => setIsEditing(false)}
                  disabled={saving}
                >
                  <X size={16} /> Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary small"
                  disabled={saving || !editName.trim()}
                >
                  <Save size={16} /> Save
                </button>
              </div>
            </form>
          ) : (
            <div className="list-info">
              <div className="title-row">
                <h1>{list.name}</h1>
                <div className="list-actions">
                  <motion.button
                    className="icon-btn"
                    onClick={() => setIsEditing(true)}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    title="Edit List"
                  >
                    <Edit2 size={20} />
                  </motion.button>
                  <motion.button
                    className="icon-btn delete"
                    onClick={handleDeleteList}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    title="Delete List"
                  >
                    <Trash2 size={20} />
                  </motion.button>
                </div>
              </div>
              {list.description && (
                <p className="list-description">{list.description}</p>
              )}
              <div className="list-meta">
                <span>{movies.length} movies</span>
                <span className="bullet">•</span>
                <span>
                  Updated {new Date(list.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="list-content">
        {movies.length === 0 ? (
          <div className="empty-state">
            <Film size={64} />
            <h2>No movies in this list</h2>
            <p>Browse movies and add them to your collection!</p>
            <motion.button
              className="btn-primary"
              onClick={() => navigate('/movies')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Browse Movies
            </motion.button>
          </div>
        ) : (
          <div className="movies-grid">
            {movies.map((movie, index) => (
              <motion.div
                key={movie.id}
                className="movie-card"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
              >
                <div
                  className="movie-poster"
                  onClick={() => navigate(`/movies/${movie.id}`)}
                >
                  {movie.poster_url ? (
                    <img src={movie.poster_url} alt={movie.title} />
                  ) : (
                    <div className="poster-placeholder">
                      <Film size={48} />
                    </div>
                  )}
                  <div className="movie-overlay">
                    <button
                      className="remove-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveMovie(movie.id, movie.title);
                      }}
                      title="Remove from list"
                    >
                      <Trash2 size={20} />
                    </button>
                  </div>
                </div>
                <div className="movie-info">
                  <h3 onClick={() => navigate(`/movies/${movie.id}`)}>
                    {movie.title}
                  </h3>
                  {movie.year && (
                    <span className="movie-year">{movie.year}</span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ListDetail;

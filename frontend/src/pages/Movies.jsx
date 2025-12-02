import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Star } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';

const Movies = () => {
  const { API_URL } = useAuth();
  const navigate = useNavigate();
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [genreFilter, setGenreFilter] = useState('');
  const [yearFilter, setYearFilter] = useState('');
  const [sortBy, setSortBy] = useState('title');
  const [sortDesc, setSortDesc] = useState(false);

  useEffect(() => {
    fetchMovies();
  }, [sortBy, sortDesc]);

  const fetchMovies = async () => {
    try {
      const params = new URLSearchParams();
      if (sortBy) params.append('sort_by', sortBy);
      if (sortDesc) params.append('sort_desc', 'true');

      const response = await axios.get(
        `${API_URL}/movies?${params.toString()}`
      );
      setMovies(response.data.items || []);
    } catch (err) {
      console.error('Failed to fetch movies:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (searchTerm) params.append('title', searchTerm);
      if (genreFilter) params.append('genre', genreFilter);
      if (yearFilter) params.append('release_year', yearFilter);
      if (sortBy) params.append('sort_by', sortBy);
      if (sortDesc) params.append('sort_desc', 'true');

      const response = await axios.get(
        `${API_URL}/movies/search?${params.toString()}`
      );
      setMovies(response.data.items || []);
    } catch (err) {
      console.error('Failed to search movies:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredMovies = movies;

  return (
    <div className="movies-page">
      <div className="page-header">
        <h1>Browse Movies</h1>
        <p>Discover and explore our movie collection</p>
      </div>

      <div className="filters-section">
        <div className="search-container">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search movies by title..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <motion.button
            className="btn-primary"
            onClick={handleSearch}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Search
          </motion.button>
        </div>

        <div className="filter-controls">
          <div className="filter-group">
            <Filter size={18} />
            <input
              type="text"
              placeholder="Genre"
              value={genreFilter}
              onChange={(e) => setGenreFilter(e.target.value)}
            />
          </div>

          <div className="filter-group">
            <input
              type="number"
              placeholder="Year"
              value={yearFilter}
              onChange={(e) => setYearFilter(e.target.value)}
              min="1900"
              max="2100"
            />
          </div>

          <div className="filter-group">
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="title">Title</option>
              <option value="release_year">Year</option>
              <option value="rating">Rating</option>
            </select>
          </div>

          <div className="filter-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={sortDesc}
                onChange={(e) => setSortDesc(e.target.checked)}
              />
              Descending
            </label>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading movies...</div>
      ) : filteredMovies.length === 0 ? (
        <div className="empty-state">No movies found</div>
      ) : (
        <div className="movies-grid">
          {filteredMovies.map((movie, index) => (
            <motion.div
              key={movie.movie_id}
              className="movie-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ y: -8, boxShadow: '0 12px 24px rgba(0,0,0,0.15)' }}
              onClick={() => navigate(`/movies/${movie.movie_id}`)}
            >
              <div className="movie-card-header">
                <h3>{movie.title}</h3>
                {movie.average_rating && (
                  <div className="movie-rating">
                    <Star size={16} fill="currentColor" />
                    {movie.average_rating.toFixed(1)}
                  </div>
                )}
              </div>

              <div className="movie-card-body">
                <div className="movie-info">
                  <span className="genre-tag">{movie.genre}</span>
                  <span className="year-tag">{movie.release_year}</span>
                </div>

                {movie.runtime && (
                  <p className="runtime">{movie.runtime} minutes</p>
                )}

                {movie.description && (
                  <p className="description">
                    {movie.description.length > 120
                      ? `${movie.description.substring(0, 120)}...`
                      : movie.description}
                  </p>
                )}
              </div>

              <div className="movie-card-footer">
                <motion.button
                  className="btn-view"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  View Details
                </motion.button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Movies;

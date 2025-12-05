import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Get authentication headers with bearer token
 */
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    Authorization: `Bearer ${token}`,
  };
};

/**
 * Fetch all lists for the current user
 * @returns {Promise<Array>} Array of list objects
 */
export const getUserLists = async () => {
  const response = await axios.get(`${API_URL}/api/lists`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

/**
 * Fetch a specific list by ID
 * @param {string} listId - The list ID
 * @returns {Promise<Object>} List object with movies
 */
export const getList = async (listId) => {
  const response = await axios.get(`${API_URL}/api/lists/${listId}`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

/**
 * Create a new list
 * @param {string} name - List name
 * @param {string} description - List description (optional)
 * @returns {Promise<Object>} Created list object
 */
export const createList = async (name, description = '') => {
  const response = await axios.post(
    `${API_URL}/api/lists`,
    { name, description },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

/**
 * Update a list's name and/or description
 * @param {string} listId - The list ID
 * @param {Object} updates - Object with name and/or description
 * @returns {Promise<Object>} Updated list object
 */
export const updateList = async (listId, updates) => {
  const response = await axios.patch(
    `${API_URL}/api/lists/${listId}`,
    updates,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

/**
 * Delete a list
 * @param {string} listId - The list ID
 * @returns {Promise<void>}
 */
export const deleteList = async (listId) => {
  await axios.delete(`${API_URL}/api/lists/${listId}`, {
    headers: getAuthHeaders(),
  });
};

/**
 * Add a movie to a list
 * @param {string} listId - The list ID
 * @param {string} movieId - The movie ID to add
 * @returns {Promise<Object>} Updated list object
 */
export const addMovieToList = async (listId, movieId) => {
  const response = await axios.post(
    `${API_URL}/api/lists/${listId}/items`,
    null,
    {
      params: { movie_id: movieId },
      headers: getAuthHeaders(),
    }
  );
  return response.data;
};

/**
 * Remove a movie from a list
 * @param {string} listId - The list ID
 * @param {string} movieId - The movie ID to remove
 * @returns {Promise<Object>} Updated list object
 */
export const removeMovieFromList = async (listId, movieId) => {
  const response = await axios.delete(
    `${API_URL}/api/lists/${listId}/items/${movieId}`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

/**
 * Add multiple movies to a list at once
 * @param {string} listId - The list ID
 * @param {Array<string>} movieIds - Array of movie IDs to add
 * @returns {Promise<Object>} Updated list object
 */
export const bulkAddMovies = async (listId, movieIds) => {
  const response = await axios.post(
    `${API_URL}/api/lists/${listId}/items/bulk`,
    movieIds,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

/**
 * Remove multiple movies from a list at once
 * @param {string} listId - The list ID
 * @param {Array<string>} movieIds - Array of movie IDs to remove
 * @returns {Promise<Object>} Updated list object
 */
export const bulkRemoveMovies = async (listId, movieIds) => {
  const response = await axios.post(
    `${API_URL}/api/lists/${listId}/items/bulk-remove`,
    movieIds,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

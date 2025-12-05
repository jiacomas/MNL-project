import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { List, Plus, Trash2, Film, Edit } from 'lucide-react';
import * as listsService from '../services/listsService';

const MyLists = () => {
  const navigate = useNavigate();
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newListName, setNewListName] = useState('');
  const [newListDescription, setNewListDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchLists();
  }, []);

  const fetchLists = async () => {
    try {
      setLoading(true);
      const data = await listsService.getUserLists();
      setLists(data);
    } catch (err) {
      console.error('Failed to fetch lists:', err);
      setError('Failed to load lists');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateList = async (e) => {
    e.preventDefault();
    if (!newListName.trim()) {
      setError('List name is required');
      return;
    }

    try {
      setCreating(true);
      setError('');
      await listsService.createList(newListName, newListDescription);
      setNewListName('');
      setNewListDescription('');
      setShowCreateModal(false);
      await fetchLists();
    } catch (err) {
      console.error('Failed to create list:', err);
      setError(err.response?.data?.detail || 'Failed to create list');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteList = async (listId, listName) => {
    if (!window.confirm(`Are you sure you want to delete "${listName}"?`)) {
      return;
    }

    try {
      await listsService.deleteList(listId);
      await fetchLists();
    } catch (err) {
      console.error('Failed to delete list:', err);
      alert('Failed to delete list');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading your lists...</p>
      </div>
    );
  }

  return (
    <div className="lists-container">
      <div className="lists-header">
        <div>
          <h1>
            <List size={32} />
            My Lists
          </h1>
          <p>Organize your favorite movies into custom lists</p>
        </div>
        <motion.button
          className="create-list-btn"
          onClick={() => setShowCreateModal(true)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Plus size={20} />
          Create New List
        </motion.button>
      </div>

      {lists.length === 0 ? (
        <div className="empty-state">
          <List size={64} />
          <h2>No lists yet</h2>
          <p>Create your first list to start organizing your movies</p>
          <motion.button
            className="create-list-btn"
            onClick={() => setShowCreateModal(true)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Plus size={20} />
            Create Your First List
          </motion.button>
        </div>
      ) : (
        <div className="lists-grid">
          {lists.map((list, index) => (
            <motion.div
              key={list.id}
              className="list-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <div
                className="list-card-content"
                onClick={() => navigate(`/lists/${list.id}`)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') navigate(`/lists/${list.id}`);
                }}
              >
                <div className="list-card-header">
                  <h3>{list.name}</h3>
                  <div className="list-card-count">
                    <Film size={16} />
                    <span>{list.items?.length || 0}</span>
                  </div>
                </div>
                {list.description && (
                  <p className="list-card-description">{list.description}</p>
                )}
                <div className="list-card-meta">
                  <span className="list-card-date">
                    Created {new Date(list.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <div className="list-card-actions">
                <motion.button
                  className="list-action-btn delete"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteList(list.id, list.name);
                  }}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  title="Delete list"
                >
                  <Trash2 size={16} />
                </motion.button>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowCreateModal(false)}
          >
            <motion.div
              className="modal-content create-list-modal"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h2>Create New List</h2>
              <form onSubmit={handleCreateList}>
                <div className="form-group">
                  <label htmlFor="list-name">List Name *</label>
                  <input
                    id="list-name"
                    type="text"
                    value={newListName}
                    onChange={(e) => setNewListName(e.target.value)}
                    placeholder="e.g., Favorite Action Movies"
                    maxLength={100}
                    required
                    autoFocus
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="list-description">Description</label>
                  <textarea
                    id="list-description"
                    value={newListDescription}
                    onChange={(e) => setNewListDescription(e.target.value)}
                    placeholder="Optional description for your list"
                    maxLength={500}
                    rows={3}
                  />
                </div>
                {error && <div className="error-message">{error}</div>}
                <div className="modal-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setShowCreateModal(false)}
                    disabled={creating}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={creating || !newListName.trim()}
                  >
                    {creating ? 'Creating...' : 'Create List'}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MyLists;

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { List, Plus, Check, X, Film } from 'lucide-react';
import * as listsService from '../services/listsService';

const AddToListModal = ({ movieId, onClose }) => {
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newListName, setNewListName] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [processingState, setProcessingState] = useState({}); // { listId: 'loading' | 'success' | 'error' }

  useEffect(() => {
    fetchLists();
  }, []);

  const fetchLists = async () => {
    try {
      setLoading(true);
      const data = await listsService.getUserLists();
      // Sort lists: those containing the movie first
      const sorted = data.sort((a, b) => {
        const aHas = a.items?.includes(movieId);
        const bHas = b.items?.includes(movieId);
        return bHas - aHas;
      });
      setLists(sorted);
    } catch (err) {
      console.error('Failed to fetch lists:', err);
    } finally {
      setLoading(false);
    }
  };

  const setListState = (listId, state) => {
    setProcessingState((prev) => ({ ...prev, [listId]: state }));
    if (state === 'success' || state === 'error') {
      setTimeout(() => {
        setProcessingState((prev) => {
          const newState = { ...prev };
          delete newState[listId];
          return newState;
        });
      }, 2000);
    }
  };

  const handleToggleList = async (list) => {
    const hasMovie = list.items?.includes(movieId);

    try {
      setListState(list.id, 'loading');

      if (hasMovie) {
        await listsService.removeMovieFromList(list.id, movieId);
        // Update local state
        setLists((prev) =>
          prev.map((l) =>
            l.id === list.id
              ? { ...l, items: l.items.filter((id) => id !== movieId) }
              : l
          )
        );
      } else {
        await listsService.addMovieToList(list.id, movieId);
        // Update local state
        setLists((prev) =>
          prev.map((l) =>
            l.id === list.id
              ? { ...l, items: [...(l.items || []), movieId] }
              : l
          )
        );
      }
      setListState(list.id, 'success');
    } catch (err) {
      console.error('Failed to toggle movie in list:', err);
      setListState(list.id, 'error');
    }
  };

  const handleCreateList = async (e) => {
    e.preventDefault();
    if (!newListName.trim()) return;

    try {
      setCreating(true);
      const newList = await listsService.createList(newListName);
      await listsService.addMovieToList(newList.id, movieId);

      // Update lists and close create form
      const updatedList = { ...newList, items: [movieId] };
      setLists([updatedList, ...lists]);
      setNewListName('');
      setShowCreateForm(false);
      setListState(newList.id, 'success');
    } catch (err) {
      console.error('Failed to create list:', err);
      alert('Failed to create list');
    } finally {
      setCreating(false);
    }
  };

  return (
    <motion.div
      className="modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="modal-content add-to-list-modal"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>Save to List</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="loading-spinner small"></div>
          ) : (
            <div className="lists-selection">
              {lists.map((list) => {
                const isSelected = list.items?.includes(movieId);
                const status = processingState[list.id];

                return (
                  <button
                    key={list.id}
                    className={`list-option ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleToggleList(list)}
                    disabled={status === 'loading'}
                  >
                    <div className="list-option-info">
                      <List size={20} />
                      <div className="list-name-col">
                        <span className="list-name">{list.name}</span>
                        <span className="list-count">
                          {list.items?.length || 0} movies
                        </span>
                      </div>
                    </div>
                    <div className="list-option-status">
                      {status === 'loading' ? (
                        <div className="spinner-mini"></div>
                      ) : status === 'success' ? (
                        <Check size={20} className="success-icon" />
                      ) : isSelected ? (
                        <Check size={20} className="check-icon" />
                      ) : (
                        <Plus size={20} className="plus-icon" />
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {!showCreateForm ? (
            <button
              className="create-new-list-btn"
              onClick={() => setShowCreateForm(true)}
            >
              <Plus size={20} />
              Create New List
            </button>
          ) : (
            <form onSubmit={handleCreateList} className="create-list-form">
              <input
                type="text"
                value={newListName}
                onChange={(e) => setNewListName(e.target.value)}
                placeholder="List Name"
                maxLength={100}
                required
                autoFocus
                disabled={creating}
              />
              <div className="create-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowCreateForm(false)}
                  disabled={creating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-submit"
                  disabled={creating || !newListName.trim()}
                >
                  {creating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default AddToListModal;

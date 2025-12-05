import React, { useEffect, useState } from 'react';
import {
  searchPenalties,
  createPenalty,
  updatePenalty,
  deletePenalty,
  deactivatePenalty,
} from '../api/penalties';
import { useAuth } from '../context/AuthContext';
import {
  Plus,
  Edit2,
  Trash2,
  Search,
  X,
  Save,
  UserX as DeactivateIcon,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const penaltyTypeOptions = [
  { value: 'review_restriction', label: 'Review restriction' },
  { value: 'temporary_ban', label: 'Temporary ban' },
  { value: 'permanent_ban', label: 'Permanent ban' },
];

const severityOptions = [1, 2, 3, 4, 5];

export default function PenaltiesPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    user_id: '',
    penalty_type: '',
    severity: '',
    is_active: '',
  });

  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [data, setData] = useState({
    items: [],
    total: 0,
    total_pages: 1,
  });

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [formData, setFormData] = useState({
    user_id: '',
    penalty_type: 'review_restriction',
    reason: '',
    severity: 1,
    expires_at: '',
  });

  const loadPenalties = async () => {
    if (!token) {
      setError('No auth token, please log in again.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const res = await searchPenalties({
        token,
        filters,
        page,
        pageSize,
      });
      setData(res);
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || 'Failed to load penalties';
      setError(msg);
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPenalties();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, filters, token]);

  const openCreateForm = () => {
    setEditing(null);
    setFormData({
      user_id: '',
      penalty_type: 'review_restriction',
      reason: '',
      severity: 1,
      expires_at: '',
    });
    setIsFormOpen(true);
    setError('');
  };

  const openEditForm = (penalty) => {
    setEditing(penalty);
    setFormData({
      user_id: penalty.user_id,
      penalty_type: penalty.penalty_type,
      reason: penalty.reason,
      severity: penalty.severity,
      expires_at: penalty.expires_at ? penalty.expires_at.slice(0, 16) : '',
    });
    setIsFormOpen(true);
    setError('');
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        name === 'severity'
          ? value === ''
            ? ''
            : Number(value)
          : value,
    }));
  };

  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);
    setFilters((prev) => ({
      ...prev,
      user_id: value,
    }));
    setPage(1);
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({
      ...prev,
      [name]: value,
    }));
    setPage(1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!token) {
      const msg = 'No auth token, please log in again.';
      setError(msg);
      alert(msg);
      return;
    }

    if (!formData.user_id.trim()) {
      const msg = 'User ID is required.';
      setError(msg);
      alert(msg);
      return;
    }

    if (!editing && !formData.reason.trim()) {
      const msg = 'Reason is required.';
      setError(msg);
      alert(msg);
      return;
    }

    setError('');

    let payload = {
      user_id: formData.user_id.trim(),
      penalty_type: formData.penalty_type,
      reason: formData.reason.trim(),
      severity: Number(formData.severity),
    };

    if (formData.penalty_type === 'permanent_ban') {
      payload.expires_at = null;
    } else if (formData.expires_at) {
      payload.expires_at = new Date(formData.expires_at).toISOString();
    } else if (formData.penalty_type === 'temporary_ban') {
      const msg = 'Temporary ban requires an expiration date';
      setError(msg);
      alert(msg);
      return;
    }

    try {
      if (editing) {
        const updateData = {};
        if (payload.reason) updateData.reason = payload.reason;
        if (payload.severity) updateData.severity = payload.severity;
        if ('expires_at' in payload) updateData.expires_at = payload.expires_at;

        await updatePenalty({
          token,
          penaltyId: editing.id,
          data: updateData,
        });
      } else {
        await createPenalty({
          token,
          data: payload,
        });
      }

      setIsFormOpen(false);
      setEditing(null);
      await loadPenalties();
    } catch (e) {
      const msg =
        e?.response?.data?.detail ||
        e?.message ||
        'Failed to save penalty';
      console.error('save penalty error', e);
      setError(msg);
      alert(msg);
    }
  };

  const handleDelete = async (penaltyId) => {
    if (!window.confirm('Delete this penalty permanently?')) return;
    try {
      await deletePenalty({ token, penaltyId });
      await loadPenalties();
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || 'Failed to delete penalty';
      setError(msg);
      alert(msg);
    }
  };

  const handleDeactivate = async (penaltyId) => {
    if (!window.confirm('Mark this penalty as inactive?')) return;
    try {
      await deactivatePenalty({ token, penaltyId });
      await loadPenalties();
    } catch (e) {
      const msg =
        e?.response?.data?.detail || e?.message || 'Failed to deactivate penalty';
      setError(msg);
      alert(msg);
    }
  };

  const closeForm = () => {
    setIsFormOpen(false);
    setEditing(null);
    setError('');
  };

  return (
    <div className="movie-management">
      <div className="management-header">
        <h2>Penalty Management</h2>
        <motion.button
          className="btn-primary"
          onClick={openCreateForm}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Plus size={20} />
          Add Penalty
        </motion.button>
      </div>

      <div className="search-bar">
        <Search size={20} />
        <input
          type="text"
          placeholder="Search by user ID..."
          value={searchTerm}
          onChange={handleSearchChange}
        />
      </div>

      <div className="filter-controls" style={{ marginBottom: '1rem' }}>
        <div className="filter-group">
          <span>Type</span>
          <select
            name="penalty_type"
            value={filters.penalty_type}
            onChange={handleFilterChange}
          >
            <option value="">All types</option>
            {penaltyTypeOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <span>Severity</span>
          <select
            name="severity"
            value={filters.severity}
            onChange={handleFilterChange}
          >
            <option value="">All severities</option>
            {severityOptions.map((s) => (
              <option key={s} value={s}>
                Severity {s}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <span>Status</span>
          <select
            name="is_active"
            value={filters.is_active}
            onChange={handleFilterChange}
          >
            <option value="">All statuses</option>
            <option value="true">Active only</option>
            <option value="false">Inactive only</option>
          </select>
        </div>

        <motion.button
          type="button"
          className="btn-secondary"
          onClick={loadPenalties}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
        >
          Refresh
        </motion.button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Loading penalties...</div>
      ) : (
        <div className="movies-table-container">
          <table className="movies-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>User ID</th>
                <th>Type</th>
                <th>Reason</th>
                <th>Severity</th>
                <th>Expires at</th>
                <th>Active</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items && data.items.length > 0 ? (
                data.items.map((p, index) => (
                  <motion.tr
                    key={p.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.03 }}
                  >
                    <td className="user-id">{p.id.substring(0, 8)}...</td>
                    <td className="user-id">{p.user_id.substring(0, 8)}...</td>
                    <td>{p.penalty_type}</td>
                    <td>{p.reason}</td>
                    <td>{p.severity}</td>
                    <td>{p.expires_at || '—'}</td>
                    <td>
                      <span
                        className={`status-badge ${
                          p.is_active ? 'active' : 'locked'
                        }`}
                      >
                        {p.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>{p.created_at}</td>
                    <td className="actions-cell">
                      <motion.button
                        className="btn-icon edit"
                        onClick={() => openEditForm(p)}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                      >
                        <Edit2 size={16} />
                      </motion.button>
                      <motion.button
                        className="btn-icon"
                        onClick={() => handleDeactivate(p.id)}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        title="Deactivate"
                      >
                        <DeactivateIcon size={16} />
                      </motion.button>
                      <motion.button
                        className="btn-icon delete"
                        onClick={() => handleDelete(p.id)}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                      >
                        <Trash2 size={16} />
                      </motion.button>
                    </td>
                  </motion.tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan="9"
                    style={{ textAlign: 'center', padding: '1rem' }}
                  >
                    No penalties found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          <div
            style={{
              marginTop: '12px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '0.9rem',
              color: 'var(--text-secondary)',
            }}
          >
            <span>
              Total: {data.total} | Page {page} / {data.total_pages}
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className="btn-secondary"
                style={{ padding: '0.4rem 0.9rem' }}
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </button>
              <button
                className="btn-secondary"
                style={{ padding: '0.4rem 0.9rem' }}
                disabled={page >= data.total_pages}
                onClick={() =>
                  setPage((p) => Math.min(data.total_pages || 1, p + 1))
                }
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      <AnimatePresence>
        {isFormOpen && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeForm}
          >
            <motion.div
              className="modal-content"
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h3>{editing ? 'Edit Penalty' : 'Create Penalty'}</h3>
                <button className="btn-close" onClick={closeForm}>
                  <X size={20} />
                </button>
              </div>

              <form
                onSubmit={handleSubmit}
                className="movie-form"
                noValidate
              >
                <div className="form-row">
                  <div className="form-group">
                    <label>User ID *</label>
                    <input
                      type="text"
                      name="user_id"
                      value={formData.user_id}
                      onChange={handleFormChange}
                      disabled={!!editing}
                    />
                  </div>

                  <div className="form-group">
                    <label>Penalty Type *</label>
                    <select
                      name="penalty_type"
                      value={formData.penalty_type}
                      onChange={handleFormChange}
                      disabled={!!editing}
                    >
                      {penaltyTypeOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Severity (1-5)</label>
                    <input
                      type="number"
                      name="severity"
                      min="1"
                      max="5"
                      value={formData.severity}
                      onChange={handleFormChange}
                    />
                  </div>

                  {formData.penalty_type !== 'permanent_ban' && (
                    <div className="form-group">
                      <label>Expires At</label>
                      <input
                        type="datetime-local"
                        name="expires_at"
                        value={formData.expires_at}
                        onChange={handleFormChange}
                      />
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label>Reason {editing ? '' : '*'}</label>
                  <textarea
                    name="reason"
                    value={formData.reason}
                    onChange={handleFormChange}
                    rows="4"
                  />
                </div>

                <div className="form-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={closeForm}
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
                    {editing ? 'Save Changes' : 'Create Penalty'}
                  </motion.button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

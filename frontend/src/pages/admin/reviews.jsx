import React, { useState, useEffect } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function AdminReviews() {
  const [title, setTitle] = useState('');
  const [sort, setSort] = useState('date');
  const [order, setOrder] = useState('desc');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [role, setRole] = useState(null);

  useEffect(() => {
    try {
      setRole(localStorage.getItem('role'));
    } catch (e) {
      // ignore
    }
  }, []);

  const loginAs = (r) => {
    try {
      localStorage.setItem('role', r);
    } catch (e) {}
    setRole(r);
  };

  const logout = () => {
    try {
      localStorage.removeItem('role');
    } catch (e) {}
    setRole(null);
  };

  const search = async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams({ title: title || '', sort, order });
      const res = await fetch(`${API_BASE}/admin/reviews?${qs.toString()}`);
      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }
      const data = await res.json();
      setItems(data.items || []);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const exportCsv = () => {
    try {
      const qs = new URLSearchParams({
        title: title || '',
        sort,
        order,
        export: 'true',
      });
      const url = `${API_BASE}/admin/reviews?${qs.toString()}`;
      window.open(url, '_blank');
    } catch (err) {
      setError(String(err));
    }
  };

  return (
    <div
      style={{
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
        padding: 20,
      }}
    >
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <h2>Admin — Review Search</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            Sort:
            <select value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="date">Date</option>
              <option value="rating">Rating</option>
            </select>
          </label>

          <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            Order:
            <select value={order} onChange={(e) => setOrder(e.target.value)}>
              <option value="desc">Desc</option>
              <option value="asc">Asc</option>
            </select>
          </label>
        </div>
      </header>

      <div
        style={{ marginTop: 12, display: 'flex', gap: 8, alignItems: 'center' }}
      >
        <input
          placeholder="Movie title (case-insensitive)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          style={{ padding: 8, minWidth: 320 }}
        />
        <button
          onClick={search}
          style={{ padding: '8px 12px' }}
          disabled={loading}
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
        <button
          onClick={exportCsv}
          style={{ padding: '8px 12px' }}
          disabled={role !== 'admin'}
          title={role !== 'admin' ? 'Only admins can export' : 'Export as CSV'}
        >
          Export CSV
        </button>
      </div>

      <div style={{ marginTop: 12 }}>
        {role ? (
          <div>
            Signed in as <strong>{role}</strong> —{' '}
            <button onClick={logout}>Sign out</button>
          </div>
        ) : (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span>Quick sign in:</span>
            <button onClick={() => loginAs('admin')}>Sign in as Admin</button>
            <button onClick={() => loginAs('customer')}>
              Sign in as Customer
            </button>
          </div>
        )}
      </div>

      {error ? (
        <div style={{ marginTop: 12, color: 'crimson' }}>{error}</div>
      ) : null}

      <div style={{ marginTop: 16 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th
                style={{
                  textAlign: 'left',
                  borderBottom: '1px solid #ddd',
                  padding: 8,
                }}
              >
                ID
              </th>
              <th
                style={{
                  textAlign: 'left',
                  borderBottom: '1px solid #ddd',
                  padding: 8,
                }}
              >
                Movie
              </th>
              <th
                style={{
                  textAlign: 'left',
                  borderBottom: '1px solid #ddd',
                  padding: 8,
                }}
              >
                Rating
              </th>
              <th
                style={{
                  textAlign: 'left',
                  borderBottom: '1px solid #ddd',
                  padding: 8,
                }}
              >
                Date
              </th>
              <th
                style={{
                  textAlign: 'left',
                  borderBottom: '1px solid #ddd',
                  padding: 8,
                }}
              >
                User
              </th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ padding: 12, color: '#666' }}>
                  No results
                </td>
              </tr>
            ) : (
              items.map((it) => (
                <tr key={it.id}>
                  <td style={{ padding: 8, borderBottom: '1px solid #f3f3f3' }}>
                    {it.id}
                  </td>
                  <td style={{ padding: 8, borderBottom: '1px solid #f3f3f3' }}>
                    {it.movie_title}
                  </td>
                  <td style={{ padding: 8, borderBottom: '1px solid #f3f3f3' }}>
                    {it.rating}
                  </td>
                  <td style={{ padding: 8, borderBottom: '1px solid #f3f3f3' }}>
                    {new Date(it.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: 8, borderBottom: '1px solid #f3f3f3' }}>
                    {it.user_id}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

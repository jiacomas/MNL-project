import React, { useState } from 'react';
import PropTypes from 'prop-types';

/**
 * TopBar - Barra superior del layout
 * Props:
 *  - title: texto del título/empresa
 *  - logo: URL de imagen del logo (opcional)
 *  - onToggleSidebar: callback al pulsar el botón de menú (opcional)
 *  - onSearch: callback con el texto de búsqueda (opcional)
 *  - userName, avatarUrl: datos del usuario (opcionales)
 */

const styles = {
  bar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: 56,
    padding: '0 16px',
    background: '#ffffff',
    borderBottom: '1px solid #e6e6e6',
    gap: 12,
    position: 'sticky',
    top: 0,
    zIndex: 50,
  },
  left: { display: 'flex', alignItems: 'center', gap: 12 },
  logo: { height: 36, width: 36, objectFit: 'contain', borderRadius: 6 },
  title: { fontSize: 16, fontWeight: 600, color: '#111827' },
  center: { flex: 1, display: 'flex', justifyContent: 'center' },
  searchForm: {
    display: 'flex',
    width: '100%',
    maxWidth: 520,
    padding: '0 8px',
  },
  searchInput: {
    flex: 1,
    height: 36,
    borderRadius: 8,
    border: '1px solid #d1d5db',
    padding: '0 12px',
    outline: 'none',
    fontSize: 14,
  },
  right: { display: 'flex', alignItems: 'center', gap: 12 },
  iconButton: {
    height: 36,
    minWidth: 36,
    padding: 8,
    borderRadius: 8,
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
  },
  avatar: { height: 36, width: 36, borderRadius: '50%', objectFit: 'cover' },
  smallText: { fontSize: 13, color: '#374151' },
};

function TopBar({
  title = 'Mi aplicación',
  logo = null,
  onToggleSidebar = null,
  onSearch = null,
  userName = null,
  avatarUrl = null,
}) {
  const [q, setQ] = useState('');

  const submitSearch = (e) => {
    e.preventDefault();
    if (onSearch) onSearch(q);
  };

  return (
    <header style={styles.bar} role="banner" aria-label="Barra superior">
      <div style={styles.left}>
        <button
          onClick={onToggleSidebar}
          style={styles.iconButton}
          aria-label="Alternar menú"
          title="Alternar menú"
        >
          {/* simple hamburger icon using SVG */}
          <svg
            width="20"
            height="14"
            viewBox="0 0 20 14"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden
          >
            <rect width="20" height="2.5" rx="1.25" fill="#111827" />
            <rect y="5.75" width="20" height="2.5" rx="1.25" fill="#111827" />
            <rect y="11.5" width="20" height="2.5" rx="1.25" fill="#111827" />
          </svg>
        </button>

        {logo ? <img src={logo} alt="logo" style={styles.logo} /> : null}
        <div style={styles.title}>{title}</div>
      </div>

      <div style={styles.center}>
        <form
          onSubmit={submitSearch}
          style={styles.searchForm}
          role="search"
          aria-label="Buscar"
        >
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar..."
            style={styles.searchInput}
            aria-label="Buscar"
          />
        </form>
      </div>

      <div style={styles.right}>
        <button
          style={styles.iconButton}
          aria-label="Notificaciones"
          title="Notificaciones"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden
          >
            <path
              d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22z"
              fill="#111827"
            />
            <path
              d="M18 16v-5a6 6 0 1 0-12 0v5l-2 2v1h16v-1l-2-2z"
              fill="#111827"
            />
          </svg>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {avatarUrl ? (
            <img src={avatarUrl} alt="Avatar" style={styles.avatar} />
          ) : (
            <div
              style={{
                ...styles.avatar,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: '#e5e7eb',
                color: '#374151',
                fontWeight: 600,
              }}
              aria-hidden
            >
              {userName ? userName.charAt(0).toUpperCase() : 'U'}
            </div>
          )}
          {userName ? <div style={styles.smallText}>{userName}</div> : null}
        </div>
      </div>
    </header>
  );
}

TopBar.propTypes = {
  title: PropTypes.string,
  logo: PropTypes.string,
  onToggleSidebar: PropTypes.func,
  onSearch: PropTypes.func,
  userName: PropTypes.string,
  avatarUrl: PropTypes.string,
};

export default TopBar;

import React, { useEffect, useMemo, useState } from "react";

/**
 * MoviesDashboard.jsx
 *
 * Fetches movie list from your FastAPI backend and displays a searchable,
 * sortable, paginated dashboard.
 *
 * By default it requests: `${API_BASE}/movies`
 * Set REACT_APP_API_BASE in your environment if your API is hosted elsewhere.
 */

const API_BASE = process.env.REACT_APP_API_BASE || "";

function useMovies() {
    const [movies, setMovies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let mounted = true;
        setLoading(true);
        setError(null);

        fetch(`${API_BASE}/movies`)
            .then(async (res) => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then((data) => {
                if (!mounted) return;
                // Expecting an array; if backend returns object with key, try to adapt
                const list = Array.isArray(data) ? data : data?.movies || [];
                setMovies(list);
            })
            .catch((err) => {
                if (!mounted) return;
                setError(err.message || "Failed to fetch movies");
            })
            .finally(() => mounted && setLoading(false));

        return () => {
            mounted = false;
        };
    }, []);

    return { movies, setMovies, loading, error, refetch: () => window.location.reload() };
}

function truncate(text, n = 140) {
    if (!text) return "";
    return text.length > n ? text.slice(0, n).trim() + "…" : text;
}

export default function MoviesDashboard() {
    const { movies, loading, error, refetch } = useMovies();
    const [query, setQuery] = useState("");
    const [sortKey, setSortKey] = useState("title"); // title | year
    const [sortDir, setSortDir] = useState("asc"); // asc | desc
    const [page, setPage] = useState(1);
    const PAGE_SIZE = 12;

    useEffect(() => {
        setPage(1);
    }, [query, sortKey, sortDir]);

    const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();
        let list = movies.slice();

        if (q) {
            list = list.filter((m) => {
                const title = (m.title || m.name || "").toString().toLowerCase();
                const genre = (Array.isArray(m.genres) ? m.genres.join(" ") : m.genre || "")
                    .toString()
                    .toLowerCase();
                const desc = (m.description || m.overview || "").toString().toLowerCase();
                return title.includes(q) || genre.includes(q) || desc.includes(q);
            });
        }

        list.sort((a, b) => {
            const aKey = (sortKey === "year" ? a.year || a.release_year || a.release_date || "" : a.title || a.name || "").toString();
            const bKey = (sortKey === "year" ? b.year || b.release_year || b.release_date || "" : b.title || b.name || "").toString();
            if (sortKey === "year") {
                // try numeric comparison if possible
                const aNum = parseInt(aKey, 10);
                const bNum = parseInt(bKey, 10);
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return sortDir === "asc" ? aNum - bNum : bNum - aNum;
                }
            }
            if (aKey < bKey) return sortDir === "asc" ? -1 : 1;
            if (aKey > bKey) return sortDir === "asc" ? 1 : -1;
            return 0;
        });

        return list;
    }, [movies, query, sortKey, sortDir]);

    const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
    const current = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

    return (
        <div style={styles.container}>
            <header style={styles.header}>
                <h1 style={{ margin: 0 }}>Movies Dashboard</h1>
                <div style={styles.controls}>
                    <input
                        aria-label="Search movies"
                        placeholder="Search title, genre, description..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        style={styles.search}
                    />
                    <select value={sortKey} onChange={(e) => setSortKey(e.target.value)} style={styles.select}>
                        <option value="title">Sort: Title</option>
                        <option value="year">Sort: Year</option>
                    </select>
                    <button
                        onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
                        aria-label="Toggle sort direction"
                        style={styles.button}
                    >
                        {sortDir === "asc" ? "Asc" : "Desc"}
                    </button>
                    <button onClick={refetch} style={styles.button}>
                        Refresh
                    </button>
                </div>
            </header>

            {loading ? (
                <div style={styles.message}>Loading movies…</div>
            ) : error ? (
                <div style={{ ...styles.message, color: "crimson" }}>
                    Error: {error}
                </div>
            ) : filtered.length === 0 ? (
                <div style={styles.message}>No movies found.</div>
            ) : (
                <>
                    <div style={styles.grid}>
                        {current.map((m) => {
                            const id = m.id ?? m.movie_id ?? Math.random().toString(36).slice(2, 9);
                            const title = m.title || m.name || "Untitled";
                            const year = m.year || m.release_year || (m.release_date ? new Date(m.release_date).getFullYear() : "");
                            const genres = Array.isArray(m.genres) ? m.genres.join(", ") : m.genre || "";
                            const desc = m.description || m.overview || "";
                            const poster = m.poster_url || m.poster || m.image || "";
                            return (
                                <article key={id} style={styles.card}>
                                    <div style={styles.posterWrap}>
                                        {poster ? (
                                            // eslint-disable-next-line jsx-a11y/img-redundant-alt
                                            <img src={poster} alt={`${title} poster`} style={styles.poster} />
                                        ) : (
                                            <div style={styles.posterPlaceholder}>
                                                <span style={{ fontSize: 12, color: "#666" }}>No image</span>
                                            </div>
                                        )}
                                    </div>
                                    <div style={styles.cardBody}>
                                        <div style={styles.cardHeader}>
                                            <h3 style={styles.cardTitle}>{title}</h3>
                                            <div style={styles.cardYear}>{year}</div>
                                        </div>
                                        <div style={styles.genres}>{genres}</div>
                                        <p style={styles.desc}>{truncate(desc, 160)}</p>
                                    </div>
                                </article>
                            );
                        })}
                    </div>

                    <div style={styles.footer}>
                        <div>
                            Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length}
                        </div>
                        <div style={styles.pagination}>
                            <button onClick={() => setPage(1)} disabled={page === 1} style={styles.pageButton}>
                                « First
                            </button>
                            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} style={styles.pageButton}>
                                ‹ Prev
                            </button>
                            <span style={{ minWidth: 80, textAlign: "center" }}>
                                Page {page} / {totalPages}
                            </span>
                            <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} style={styles.pageButton}>
                                Next ›
                            </button>
                            <button onClick={() => setPage(totalPages)} disabled={page === totalPages} style={styles.pageButton}>
                                Last »
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

const styles = {
    container: {
        padding: 20,
        fontFamily: "Inter, Roboto, system-ui, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial",
        color: "#111",
    },
    header: {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 16,
        gap: 12,
    },
    controls: {
        display: "flex",
        gap: 8,
        alignItems: "center",
    },
    search: {
        padding: "8px 10px",
        borderRadius: 6,
        border: "1px solid #ddd",
        minWidth: 260,
    },
    select: {
        padding: "8px 10px",
        borderRadius: 6,
        border: "1px solid #ddd",
    },
    button: {
        padding: "8px 10px",
        borderRadius: 6,
        border: "1px solid #ddd",
        background: "#fff",
        cursor: "pointer",
    },
    message: {
        padding: 24,
        textAlign: "center",
        color: "#444",
    },
    grid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
        gap: 16,
    },
    card: {
        display: "flex",
        flexDirection: "column",
        border: "1px solid #eee",
        borderRadius: 8,
        overflow: "hidden",
        background: "#fff",
        boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
        minHeight: 320,
    },
    posterWrap: {
        height: 0,
        paddingTop: "56.25%", // 16:9
        position: "relative",
        background: "#f6f6f6",
    },
    poster: {
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        objectFit: "cover",
    },
    posterPlaceholder: {
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
    },
    cardBody: {
        padding: 12,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        flex: 1,
    },
    cardHeader: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "baseline",
        gap: 8,
    },
    cardTitle: {
        margin: 0,
        fontSize: 16,
        lineHeight: 1.1,
    },
    cardYear: {
        fontSize: 12,
        color: "#666",
    },
    genres: {
        fontSize: 12,
        color: "#666",
    },
    desc: {
        margin: 0,
        fontSize: 13,
        color: "#333",
        flex: 1,
    },
    footer: {
        marginTop: 16,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 8,
        flexWrap: "wrap",
    },
    pagination: {
        display: "flex",
        gap: 8,
        alignItems: "center",
    },
    pageButton: {
        padding: "6px 10px",
        borderRadius: 6,
        border: "1px solid #ddd",
        background: "#fff",
        cursor: "pointer",
    },
};
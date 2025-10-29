import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

/*
    ReviewDashboard.jsx
    - Expects a FastAPI endpoint at `${API_BASE}/movies/:id/reviews`
    - Endpoint response shape assumed:
        {
            "movie": { "id": 1, "title": "Movie Title" },
            "reviews": [
                { "id": 1, "author": "Alice", "rating": 4, "text": "Nice", "created_at": "2025-01-01T12:00:00Z" },
                ...
            ]
        }
*/

const API_BASE = process.env.REACT_APP_API_BASE || ""; // e.g. http://localhost:8000

export default function ReviewDashboard() {
    const { id: movieId } = useParams();
    const [movie, setMovie] = useState(null);
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!movieId) {
            setError("Missing movie id");
            setLoading(false);
            return;
        }

        const controller = new AbortController();
        setLoading(true);
        setError(null);

        fetch(`${API_BASE}/movies/${movieId}/reviews`, { signal: controller.signal })
            .then(async (res) => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then((data) => {
                setMovie(data.movie || null);
                setReviews(Array.isArray(data.reviews) ? data.reviews : []);
            })
            .catch((err) => {
                if (err.name !== "AbortError") setError(err.message || "Failed to load");
            })
            .finally(() => setLoading(false));

        return () => controller.abort();
    }, [movieId]);

    const stats = React.useMemo(() => {
        const counts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
        let sum = 0;
        reviews.forEach((r) => {
            const v = Number(r.rating) || 0;
            if (v >= 1 && v <= 5) counts[v] = (counts[v] || 0) + 1;
            sum += v;
        });
        const total = reviews.length;
        const avg = total ? +(sum / total).toFixed(2) : 0;
        return { counts, total, avg };
    }, [reviews]);

    if (loading) return <div style={{ padding: 20 }}>Loading reviews…</div>;
    if (error) return <div style={{ padding: 20, color: "red" }}>Error: {error}</div>;

    return (
        <div style={{ padding: 20, fontFamily: "system-ui, Arial", maxWidth: 900 }}>
            <header style={{ marginBottom: 20 }}>
                <h2 style={{ margin: 0 }}>{movie?.title || `Movie #${movieId}`}</h2>
                <div style={{ color: "#555", marginTop: 6 }}>
                    {stats.total} review{stats.total !== 1 ? "s" : ""} — average rating {stats.avg} / 5
                </div>
            </header>

            <section style={{ display: "flex", gap: 24, marginBottom: 24 }}>
                <div style={{ flex: "0 0 320px", padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
                    <h4 style={{ marginTop: 0 }}>Ratings breakdown</h4>
                    {([5, 4, 3, 2, 1] as unknown as number[]).map((star) => {
                        const count = stats.counts[star] || 0;
                        const pct = stats.total ? Math.round((count / stats.total) * 100) : 0;
                        return (
                            <div key={star} style={{ display: "flex", alignItems: "center", marginBottom: 8 }}>
                                <div style={{ width: 36 }}>{star}★</div>
                                <div style={{ flex: 1, background: "#f1f1f1", height: 10, borderRadius: 6, margin: "0 8px" }}>
                                    <div style={{ width: `${pct}%`, height: "100%", background: "#4f46e5", borderRadius: 6 }} />
                                </div>
                                <div style={{ width: 42, textAlign: "right" }}>{count}</div>
                            </div>
                        );
                    })}
                </div>

                <div style={{ flex: 1, padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
                    <h4 style={{ marginTop: 0 }}>Recent reviews</h4>
                    {reviews.length === 0 && <div style={{ color: "#666" }}>No reviews yet.</div>}
                    <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                        {reviews.map((r) => (
                            <li
                                key={r.id}
                                style={{
                                    borderTop: "1px solid #f3f3f3",
                                    paddingTop: 12,
                                    paddingBottom: 12,
                                    marginTop: 12,
                                }}
                            >
                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                                    <strong style={{ fontSize: 14 }}>{r.author || "Anonymous"}</strong>
                                    <span style={{ color: "#333" }}>{r.rating}★</span>
                                </div>
                                <div style={{ color: "#444", marginBottom: 6 }}>{r.text}</div>
                                <div style={{ color: "#888", fontSize: 12 }}>{new Date(r.created_at).toLocaleString()}</div>
                            </li>
                        ))}
                    </ul>
                </div>
            </section>
        </div>
    );
}
import React from 'react';
import Link from 'next/link';

export default function Home() {
  return (
    <div
      style={{
        padding: 24,
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
      }}
    >
      <h1>Frontend demo</h1>
      <p>
        Use the <Link href="/admin/reviews">Admin Reviews</Link> page to search
        and export reviews (requires backend running).
      </p>
    </div>
  );
}

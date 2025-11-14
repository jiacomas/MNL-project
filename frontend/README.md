# Frontend — Admin Reviews (minimal)

This repository contains a minimal Next.js-style page at `src/pages/admin/reviews.jsx` that provides a basic UI to search, sort and export reviews using the backend endpoint `/admin/reviews`.

How to run (example):

1. Ensure the backend is running locally (default at `http://localhost:8000`).
2. If you have an existing Next.js app, copy `src/pages/admin/reviews.jsx` into your Next.js project's `src/pages/admin/reviews.jsx` (or `pages/admin/reviews.jsx`).
3. Start Next.js:

```bash
# install (if you don't have a Next project created yet)
npm init -y
npm install react react-dom next
# add scripts to package.json: "dev": "next dev"
npm run dev
```

4. Open `http://localhost:3000/admin/reviews` and use the UI.

Notes:

- The page expects the backend API base URL in `NEXT_PUBLIC_API_BASE` (defaults to `http://localhost:8000`).
- This is a minimal admin page for convenience and demonstration. In production you should wire proper authentication and role checks before calling admin endpoints.

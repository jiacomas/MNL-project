# Frontend — React + Vite

This folder contains the frontend application built with React and Vite. The project is configured to talk to the FastAPI backend running at `http://localhost:8000` by default.

Below are step-by-step instructions so every developer can run the frontend and connect it to the backend for local development and for simple local production preview.

## Quick Start (Local development)

- **Prerequisites**: Node.js 18+ and npm (or yarn).

- Open one terminal and start the backend (from repo root):

```
export PYTHONPATH=backend
uvicorn backend.main:app --reload
```

- Open a second terminal and start the frontend:

```
cd frontend
npm install
# Run dev server (default will target http://localhost:8000)
npm run dev
```

- Visit the app at `http://localhost:5173`.

## Environment / API URL

- The frontend reads the backend base URL from `import.meta.env.VITE_API_URL`. If that variable is not set, the app falls back to `http://localhost:8000`.
- To override the backend URL for local dev, set it when starting the dev server:

```
VITE_API_URL=http://localhost:8000 npm run dev
```

- You can also create a `frontend/.env` file with the line:

```
VITE_API_URL=http://localhost:8000
```

## Proxy (vite.config.js)

- The Vite dev server is configured to proxy requests under `/api` to `http://localhost:8000`. If your frontend uses absolute URLs (full `http://...` addresses), set `VITE_API_URL` instead.

## Production build and preview

To build and preview a production bundle locally:

```
cd frontend
npm run build
# Make sure the built app points to the backend you want to use:
VITE_API_URL=http://localhost:8000 npm run preview
```

The preview server usually runs at `http://localhost:4173` (check the terminal for the exact URL).

## Docker / Docker Compose notes

- The main `docker-compose.yml` includes a `frontend` service that expects a `frontend/Dockerfile`. If you do not have that `Dockerfile` in `frontend/`, running `docker compose up --build` may fail when building the frontend image.
- If you want to run the frontend inside Docker and connect it to the backend container, ensure the frontend container uses `VITE_API_URL=http://backend:8000` or that the built files reference that URL. Inside the compose network the backend is reachable at `http://backend:8000`.

## Troubleshooting

- If the frontend cannot reach the backend:
  - Verify the backend is up: `curl http://localhost:8000/health` (should return `{ "status": "ok" }`).
  - Confirm `VITE_API_URL` is set correctly or remove it to use the default `http://localhost:8000`.
  - If backend runs in Docker and frontend is on the host, use `http://host.docker.internal:8000` as the API URL on macOS/Windows.

## Where the frontend reads the API URL

- See `frontend/src/context/AuthContext.jsx` — it uses `import.meta.env.VITE_API_URL` and falls back to `http://localhost:8000`.

```

```

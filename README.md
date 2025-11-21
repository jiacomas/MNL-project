# MNL Project – IMDB Movie Reviews Platform

## 1. Overview

This project is a full-stack multiuser system built for the COSC 310 course.
The domain is an IMDB-style movie reviews platform, where users can:

- browse and search movies
- write and edit reviews
- manage bookmarks
- receive personalized recommendations
- be managed by admins through penalties, statistics and external metadata sync

The system follows the course constraints:

- **Backend:** FastAPI (Python)
- **Frontend:** Simple static frontend (Next.js/HTML placeholder during backend phase)
- **Storage:** JSON / CSV files only (no database)
- **Testing:** Pytest (unit + integration)
- **CI:** GitHub Actions
- **Containerization:** Docker + Docker Compose

Dataset used: **IMDB Movies User Reviews**
<https://www.kaggle.com/datasets/sadmadlad/imdb-user-reviews>

---

## 2. Architecture & Tech Stack

**Backend (FastAPI, Python)**

- Layered architecture:
  - `routers/` – HTTP API (REST endpoints)
  - `services/` – business logic and domain rules
  - `repositories/` – file-based persistence (JSON/CSV)
  - `schemas/` – Pydantic models (validation, I/O models)
- Multi-user system:
  - JSON-backed user storage
  - Password hashing
  - JWT authentication
  - Role-based access (regular user vs admin)

**Frontend**

- Simple Dockerized frontend serving a placeholder UI during backend phase.

**Infrastructure**

- Docker Compose for:
  - `backend` (FastAPI)
  - `frontend` (Nginx)
  - `test-runner` (Pytest container)
- CI with GitHub Actions

---

## 3. Project Structure

```
MNL-project/
├── backend/
│   ├── main.py
│   ├── settings.py
│   ├── data.py
│   ├── data/
│   │   ├── bookmarks.json
│   │   ├── users.json
│   │   ├── movies/
│   │   └── exports/
│   ├── repositories/
│   ├── services/
│   ├── routers/
│   ├── schemas/
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   └── src/index.html
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── pytest.ini
├── bandit.yml
├── reports/
└── scrum-documents/
```

---

## 4. Backend Routers

| Router file          | Responsibility                                          |
| -------------------- | ------------------------------------------------------- |
| `auth.py`            | JWT authentication & `/me`                              |
| `movies.py`          | Movie CRUD, filter, search (admin create/update/delete) |
| `reviews.py`         | CRUD reviews, pagination, "my review"                   |
| `bookmarks.py`       | User bookmarks + CSV export                             |
| `recommendations.py` | Personalized movie recommendations                      |
| `password_reset.py`  | Reset tokens (request + set new password)               |
| `admin_analytics.py` | Admin CSV export of platform statistics                 |
| `admin_sync.py`      | Trigger external metadata sync                          |

Swagger UI: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

---

## 5. Installation (Local Dev)

### 5.1 Clone

```
git clone https://github.com/jiacomas/MNL-project.git
cd MNL-project
```

### 5.2 Setup Virtual Environment

```
python3 -m venv venv
source venv/bin/activate       # macOS/Linux
# .\venv\Scripts\activate      # Windows
```

### 5.3 Install Dependencies

```
pip install --upgrade pip
pip install -r requirements.txt
```

### 5.4 Optional: Environment Variables

```
cp .env.example .env
```

External sync uses:

```
MOVIE_API_KEY="<your_api_key>"
```

---

## 6. Run Backend

```
export PYTHONPATH=backend
uvicorn backend.main:app --reload
```

Backend URL:

```
http://localhost:8000
```

---

## 7. Run with Docker Compose

```
docker compose up --build
```

Services:

| Service     | Port               |
| ----------- | ------------------ |
| Backend     | 8000               |
| Frontend    | 3000               |
| Test Runner | runs automatically |

Stop:

```
docker compose down
```

---

## 8. Testing

### Run Local Tests

```
cd backend
pytest -v
```

### Run Tests in Docker

```
docker compose run --rm test-runner
```

Tests include:

- Repository persistence
- Services rules & permissions
- Router integration tests (FastAPI TestClient)
- Mocked external API sync
- Admin analytics, bookmarks export
- Recommendations logic

---

## 9. Data Storage

| Type           | File                                  |
| -------------- | ------------------------------------- |
| Users          | `backend/data/users.json`             |
| Bookmarks      | `backend/data/bookmarks.json`         |
| Movies/Reviews | `backend/data/movies/`                |
| Exports        | `backend/data/exports/`               |
| Sync Log       | `backend/data/external_sync_log.json` |

Persistence rules:

- Atomic write strategy
- Schema validation via Pydantic
- Admin-controlled penalty + sync + export logs

---

## 10. External API Integration

Endpoint:

```
POST /admin/sync-external
```

Functional behavior:

- Fetch metadata (poster, runtime, cast)
- Update missing movie fields
- Record sync log entry:
  - timestamp
  - number updated
  - indices updated

Configuration:

```
MOVIE_API_KEY="<your_api_key>"
```

Testing: mocked async HTTP calls.

---

## 11. Continuous Integration (CI)

Located in `.github/workflows/`.

Features:

- Automatic test execution on push & PR
- Dockerized test environment
- Fail-fast concurrency
- Optional coverage reports

---

## 12. Scrum Documentation

Directory:

```
scrum-documents/
```

Includes:

- meeting notes
- action items
- responsibilities
- discussion summaries

Additional reports stored in:

```
reports/
```

---

## 13. Team

**Team Name:** MNL Project

| Name       | Student ID |
| ---------- | ---------- |
| Jia Comas  | 73041360   |
| Mason Liu  | 10288041   |
| Helin Long | 64904501   |
| Mia Kuang  | 35154913   |

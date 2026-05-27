# <project-name>

> Brief description of what this project does and who it is for.

## Key Links

| Resource | URL |
|----------|-----|
| Frontend | `http://localhost:5173` |
| Backend API | `http://localhost:8000/docs` |
| Admin Panel | _if applicable_ |
| Database Dashboard | _e.g., Adminer, pgAdmin URL_ |
| Production | _when deployed_ |

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, PostgreSQL, SQLAlchemy 2.0
- **Frontend:** React 19, Vite, TypeScript, Tailwind v4
- **Infra:** Docker, Docker Compose

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- uv (`pip install uv`)

### Setup

```bash
# Clone and enter project
git clone <repo-url>
cd <project-name>

# Backend
cd backend
uv sync
cp .env.example .env
# Edit .env with your database credentials

# Frontend
cd ../frontend
npm install

# Start services
docker compose up -d  # PostgreSQL
cd ../backend && uv run alembic upgrade head
uv run uvicorn app.main:app --reload

# In another terminal
cd frontend && npm run dev
```

## Development

### Running Tests

```bash
# Backend
cd backend && uv run pytest

# Frontend
cd frontend && npm test
```

### Linting

```bash
# Backend
uv run ruff check . && uv run ruff format --check .

# Frontend
npm run lint
```

## Project Structure

```
<project-name>/
├── backend/
│   ├── app/
│   │   ├── core/       # Config, database, security
│   │   ├── <module>/   # Feature modules
│   │   └── main.py     # FastAPI app entry
│   ├── tests/
│   ├── alembic/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   └── package.json
└── compose.yaml
```

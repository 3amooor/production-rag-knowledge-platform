# Production RAG Knowledge Platform

A multi-tenant Retrieval-Augmented Generation platform built incrementally with verifiable engineering gates.

## Current phase

**Phase 4 — authentication and tenancy foundation.** The project now includes schema/migrations, FastAPI health/readiness, request IDs, JWT authentication with refresh-token rotation, and workspace-membership authorization primitives. Workspace APIs, ingestion, and RAG are not implemented yet.

## Local prerequisites

- Docker Desktop with Docker Compose
- Optional: Python 3.12+ and Node.js 24+ for running services outside Docker

## Quick start

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Then verify:

- API liveness: `http://localhost:8000/health`
- API documentation: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`
- MinIO console: `http://localhost:9001`

Stop services with `docker compose down`. Add `--volumes` only when you intentionally want to remove local database, Redis, and object-storage data.

## Quality checks

From `backend/` with Python 3.12 installed:

```powershell
pip install ".[dev]"
ruff check .
ruff format --check .
pytest tests/unit
```

From `frontend/`:

```powershell
npm install
npm run build
```

## Architecture status

The full Phase 0 architecture is currently captured in the project discussion. Durable architecture documentation and ADRs will be added in their planned documentation phase, alongside implemented behavior.

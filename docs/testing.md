# Verification

## Local commands

From `backend/`:

```powershell
python -m pip install ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m pytest tests/unit
```

From `frontend/`:

```powershell
npm ci
npm run lint
npm run build
```

The current unit suite covers health/readiness contracts, schema metadata, and
the pure parsing/chunking/embedding primitives. Container-level verification
should additionally cover migrations, MinIO upload, a Celery worker completion,
workspace isolation, refresh-token rotation, and a complete browser flow.

GitHub Actions runs the commands above on pushes to `master` and pull requests.

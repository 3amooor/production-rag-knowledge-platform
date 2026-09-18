# Development environment

Phase 1 establishes the local service topology, not application functionality.

| Service | Local address | Purpose |
|---|---|---|
| API | `http://localhost:8000` | FastAPI service; currently exposes only `/health` |
| Frontend | `http://localhost:5173` | React/Vite development shell |
| PostgreSQL | `localhost:5432` | Future relational, FTS, and pgvector persistence |
| Redis | `localhost:6379` | Future task broker, cache, and rate-limit store |
| MinIO | `http://localhost:9000` | Local S3-compatible object-storage endpoint |
| MinIO Console | `http://localhost:9001` | Local object-storage administration |

The API and worker use development Docker targets with source mounts. Production targets do not use source mounts; deployment configuration is intentionally deferred until the application has database migrations, a real worker pipeline, and security boundaries to deploy.

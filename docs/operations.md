# Operations guide

## Local development

Copy `.env.example` to `.env`, then start the local service topology with
`docker compose up --build`. Apply schema migrations from `backend/` using
`alembic upgrade head`. The API is on port 8000, the Vite client on 5173, and
the MinIO console on 9001.

## Probes and recovery

`/health` checks process liveness. `/ready` checks PostgreSQL and Redis. A
failed processing job marks both the job and document as `FAILED` with a
truncated reason. Requeueing should be performed only after resolving its root
cause (for example object-storage credentials or an unsupported source).

## Production template

`compose.production.yaml` has no source mounts and targets the production
images. It assumes external managed PostgreSQL, Redis, and S3-compatible
storage configured by environment variables. It intentionally does not deploy
development databases or MinIO credentials into production.

## Observability

Every answer stores a retrieval log (strategy, query hash, selected chunks,
latency, configuration) and a generation log. Do not log raw question content
in central logs unless the data policy permits it; the persisted telemetry uses
a SHA-256 query hash for correlation.

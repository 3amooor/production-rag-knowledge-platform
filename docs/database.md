# Database architecture

## Ownership and tenancy

`workspaces` is the tenant boundary. A user gains access through `workspace_members`; all workspace resources have a direct `workspace_id`, including `chunks`, `processing_jobs`, and `retrieval_logs`. This deliberate denormalization makes the authorization predicate explicit and inexpensive in retrieval queries:

```sql
WHERE workspace_id = :authorized_workspace_id
```

The application must apply that predicate inside every dense and lexical query. It must not retrieve globally and filter results in Python.

The implemented hybrid retriever enforces this predicate independently for both its
vector and PostgreSQL full-text candidate queries, then combines the resulting ranks
with reciprocal-rank fusion. This keeps an accidental cross-tenant candidate from
being possible at the query boundary.

## Retrieval storage

`chunks` carries document/version provenance, text, page number, token count, JSON metadata, a `vector(1536)` embedding, and a PostgreSQL `tsvector` lexical index.

The initial embedding dimensionality is fixed at 1536 by the migration. The `EMBEDDING_DIMENSIONS` setting is therefore a compatibility guard, not a live schema switch: changing it requires a deliberate migration and re-embedding of all chunks. Phase 8 will validate provider output against this value before writing vectors.

The initial vector index is HNSW with cosine distance. HNSW serves low-latency approximate nearest-neighbor queries without a separately trained index. Its tradeoff is greater memory and insertion cost. IVFFlat remains a future option after measured corpus growth warrants cheaper indexing and a stable training set.

PostgreSQL FTS is the initial lexical engine because it is transactional with document writes and does not add a new operational service. OpenSearch becomes worth considering only if measured requirements demand advanced linguistic analysis, large-scale relevance tuning, or search-only horizontal scaling.

## Migration workflow

Run migrations from `backend/` after the PostgreSQL service is healthy:

```powershell
alembic upgrade head
```

Inspect the pending/current revision:

```powershell
alembic current
alembic history
```

The initial migration enables `vector` and `pgcrypto`. It intentionally does not remove extensions during downgrade because extensions may be shared by another database component.

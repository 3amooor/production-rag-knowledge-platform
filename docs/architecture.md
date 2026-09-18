# Architecture

## System boundary

The platform is a multi-tenant Retrieval-Augmented Generation (RAG) service.
Each `workspace` is a tenant. Users authenticate with short-lived access JWTs,
and every workspace resource is authorized through `workspace_members`.

```text
React client -> FastAPI -> PostgreSQL + pgvector
                    |          ^
                    v          |
                  MinIO/S3 -> Celery worker -> Redis
```

## Request and data flow

1. A user registers or signs in and receives access and refresh tokens.
2. The user creates a workspace; its creator is saved as the `owner` member.
3. A text/Markdown upload is stored under a random, workspace-prefixed S3 key.
4. A `document_versions` record and `processing_jobs` record are committed.
5. Celery extracts text, makes overlapping chunks, creates embeddings, and
   writes chunks plus PostgreSQL full-text vectors.
6. A question creates a user message, runs dense and lexical retrieval scoped
   to the workspace, fuses candidates with reciprocal-rank fusion, and stores
   an extractive answer, citations, and telemetry.

## Tenant isolation

The authorization dependency resolves the membership for the requested
`workspace_id`. Dense and lexical retrieval apply `chunks.workspace_id = :id`
inside their SQL queries. This is the primary isolation control: callers never
receive global candidates to be filtered in application memory.

## Current provider choices

Object originals use the S3-compatible storage boundary, locally backed by
MinIO. Embeddings use a deterministic normalized hashing implementation at the
schema's fixed dimension of 1536. It is usable for local development and tests,
but a production deployment should replace it with a managed embedding provider
and re-embed the corpus. Answering is currently extractive rather than LLM
generation, preserving inspectable source excerpts without an unconfigured
external API credential.

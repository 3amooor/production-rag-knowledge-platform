# Delivery phases through Phase 22

The initial platform architecture had already established the local topology,
database schema, health probes, authentication, and tenant authorization. The
following implementation milestones are now represented in the codebase.

| Phase | Delivered capability |
|---|---|
| 5 | Authenticated workspace creation, listing, and membership-gated access |
| 6 | Bounded uploads persisted to S3-compatible storage and durable processing jobs |
| 7 | Retryable Celery ingestion worker and visible document lifecycle states |
| 8 | UTF-8 plain-text/Markdown parsing and deterministic overlapping chunking |
| 9 | Normalized development embedding provider with the schema's 1536 dimensions |
| 10 | Tenant-scoped dense and lexical retrieval with reciprocal-rank fusion |
| 11 | Conversation/message APIs with grounded excerpts and persisted citations |
| 12 | API contracts supporting workspace, intake, status polling, and chat clients |
| 13 | Retrieval and generation telemetry persisted with each answer |
| 14 | Explicit object-store failure handling, worker retries, and failure states |
| 15 | Unit coverage for pure ingestion primitives and durable architecture notes |
| 16 | Functional browser client for authentication, workspaces, uploads, and questions |
| 17 | End-to-end API contracts documented for client integration |
| 18 | Security model and deployment controls documented |
| 19 | Operations, architecture, API, and verification guides completed |
| 20 | CI runs backend formatting/lint/tests and frontend lint/build |
| 21 | Production Compose template removes source mounts and expects managed dependencies |
| 22 | Release validation: backend tests, frontend lint/build, and visual client verification |

## Intentional boundaries

This release accepts only `text/plain` and `text/markdown`. PDF/DOCX extraction,
a managed embedding/generation provider, member administration, streaming answers,
and evaluation-run APIs are deliberately out of scope for this implementation; they
need provider and product choices before they can be safely completed.

The current generation path is extractive: it returns the most relevant chunks and
their citations. This makes answers inspectable without introducing an unconfigured
external model credential. A model-backed synthesis adapter should preserve the same
citation and telemetry contract.

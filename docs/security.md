# Security model

## Implemented controls

- Passwords use Argon2 through `pwdlib`.
- Access JWTs are short-lived; refresh JWTs have server-side hashed records,
  expiration, revocation, and rotation.
- Workspace membership is enforced by FastAPI dependencies.
- Object keys include opaque UUIDs and are not exposed as client-controlled
  paths.
- Uploads have allow-listed MIME types and a configurable byte limit.
- Production startup rejects the documented placeholder JWT secret.
- Request IDs flow into logging and responses for incident correlation.

## Deployment requirements

Set a unique `JWT_SECRET_KEY`, strong database/S3 credentials, and explicit
`CORS_ORIGINS` before production. Terminate TLS at an ingress or reverse proxy;
the local compose files do not provide HTTPS. Store secrets in a secret manager,
not a committed `.env` file. Use a private S3 bucket, least-privilege worker
credentials, backups, and encrypted storage.

## Remaining hardening

Add rate limiting, malware scanning, signed upload/download URLs, audit events,
role-specific write authorization, security headers, dependency scanning, and
an external embedding/LLM provider's data-retention review before handling
sensitive production data.

# API reference

All application endpoints use the `/api/v1` prefix except liveness and
readiness probes. Bearer authentication uses `Authorization: Bearer <token>`.

| Endpoint | Method | Purpose |
|---|---:|---|
| `/health` | GET | Process liveness |
| `/ready` | GET | Database and Redis readiness |
| `/api/v1/auth/register` | POST | Create an account and issue a token pair |
| `/api/v1/auth/login` | POST | Issue a token pair |
| `/api/v1/auth/refresh` | POST | Rotate a refresh token |
| `/api/v1/auth/me` | GET | Return the authenticated user |
| `/api/v1/workspaces` | GET/POST | List accessible workspaces or create one |
| `/api/v1/workspaces/{workspace_id}` | GET | Fetch a workspace membership-gated resource |
| `/api/v1/workspaces/{workspace_id}/documents` | GET/POST | List documents or upload text/Markdown |
| `/api/v1/workspaces/{workspace_id}/documents/{document_id}` | GET | Poll the indexing state |
| `/api/v1/workspaces/{workspace_id}/conversations` | POST | Create a conversation |
| `/api/v1/workspaces/{workspace_id}/conversations/{conversation_id}/messages` | GET/POST | List messages or ask a grounded question |

## Common errors

`401` means the bearer token is missing, invalid, expired, or belongs to an
inactive user. `403` means the user is not a workspace member. `404` prevents
cross-workspace discovery for document and conversation identifiers. Uploads
return `413` when they exceed `MAX_UPLOAD_BYTES`, `415` for unsupported media
types, and `503` when object storage is unavailable.

## Upload contract

Use multipart form field `upload`. Supported MIME types are `text/plain` and
`text/markdown`. A `202` response means the original and job were committed;
poll the document resource until `status` becomes `READY` or `FAILED`.

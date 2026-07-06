# API Reference

Quick-reference companion to the endpoints that actually exist right now (see ROADMAP.md for what's not built yet). FastAPI also auto-generates a full interactive spec at `http://localhost:8000/docs` (Swagger UI) straight from the route/schema code below — that's the source of truth if this drifts; this file is for skimming without running the server.

All request/response bodies are JSON unless noted. Base URL in local dev: `http://localhost:8000`.

---

### `GET /health`

Liveness check — no auth.

**Response `200`**
```json
{ "status": "ok" }
```

---

### `POST /auth/signup`

Create an account.

**Request**
```json
{ "email": "you@example.com", "password": "yourpassword" }
```

**Response `201`**
```json
{ "id": 1, "email": "you@example.com", "created_at": "2026-07-05T13:50:49.792793Z" }
```

**Errors**
| Status | When |
|---|---|
| `400` | Email already registered |
| `422` | Body missing `email`/`password`, or `email` isn't a valid email address |

---

### `POST /auth/login`

Exchange credentials for a JWT.

**Request**
```json
{ "email": "you@example.com", "password": "yourpassword" }
```

**Response `200`**
```json
{ "access_token": "eyJhbGciOi...", "token_type": "bearer" }
```

Token expires after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60, see `.env`). Send it on subsequent requests as `Authorization: Bearer <access_token>`.

**Errors**
| Status | When |
|---|---|
| `401` | Email not found, or password doesn't match |

---

### `GET /auth/me`

Return the logged-in user. Requires auth.

**Headers**
```
Authorization: Bearer <access_token>
```

**Response `200`**
```json
{ "id": 1, "email": "you@example.com", "created_at": "2026-07-05T13:50:49.792793Z" }
```

**Errors**
| Status | When |
|---|---|
| `401` | Missing, invalid, or expired token |

---

### `POST /resumes/upload`

Upload a resume file (`.pdf` or `.docx`, max 5MB), extract its text, and store it. Requires auth.

**Headers**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request**: multipart form with one field, `file`, containing the resume file.

**Response `201`**
```json
{
  "id": 1,
  "original_filename": "resume.pdf",
  "extracted_text": "Jane Doe\nBackend Engineer...",
  "uploaded_at": "2026-07-06T09:12:21.541695Z"
}
```

**Errors**
| Status | When |
|---|---|
| `400` | File isn't `.pdf`/`.docx`, exceeds 5MB, or no text could be extracted (e.g. a scanned/image-only PDF with no text layer) |
| `401` | Missing, invalid, or expired token |

---

## Planned endpoints (not yet built — see ROADMAP.md)

| Method & path | Checkpoint |
|---|---|
| `POST /matches` | 5 |
| `POST /matches/{id}/cover-letter` | 6 |

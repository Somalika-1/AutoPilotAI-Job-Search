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

### `POST /matches`

Score a resume against a job description using Gemini. Requires auth.

**Request**
```json
{ "resume_id": 1, "job_description_text": "Looking for a backend engineer with Python and Postgres experience." }
```

**Response `201`**
```json
{
  "id": 1,
  "resume_id": 1,
  "job_description_id": 1,
  "score": 78,
  "missing_skills": ["Kubernetes", "GraphQL"],
  "strengths": ["Python", "PostgreSQL", "REST APIs"],
  "cover_letter": null,
  "created_at": "2026-07-06T10:00:00.000000Z"
}
```
`cover_letter` is always `null` until Checkpoint 6.

**Errors**
| Status | When |
|---|---|
| `401` | Missing, invalid, or expired token |
| `404` | `resume_id` doesn't exist, or belongs to a different user (both look identical on purpose — see V1.md) |
| `502` | The Gemini API call itself failed (network issue, bad key, rate limit, etc.) |

---

### `POST /matches/{match_id}/cover-letter`

Generate a tailored cover letter for an existing match, using its resume + job description. Requires auth.

**Response `200`** — the full, updated match (same shape as `POST /matches`, now with `cover_letter` populated):
```json
{
  "id": 1,
  "resume_id": 1,
  "job_description_id": 1,
  "score": 78,
  "missing_skills": ["Kubernetes", "GraphQL"],
  "strengths": ["Python", "PostgreSQL", "REST APIs"],
  "cover_letter": "Dear Hiring Manager, ...",
  "created_at": "2026-07-06T10:00:00.000000Z"
}
```

**Errors**
| Status | When |
|---|---|
| `401` | Missing, invalid, or expired token |
| `404` | `match_id` doesn't exist, or belongs to a different user |
| `502` | The Gemini API call itself failed |

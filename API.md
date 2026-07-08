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

---

## Planned (V2) — not yet built

Contracts below are the target shape for Checkpoints 9-12 (see ROADMAP.md), written ahead of time so implementation has a spec to build against — same approach used for V1's checkpoints. Not implemented yet; update this section (moving it above the line once real) as each checkpoint lands.

### `GET /jobs/search`

Search live job-board results across all configured providers. Requires auth. Results are **ephemeral** — not persisted until `POST /jobs/save`.

**Query params**: `query` (required), `location` (optional), `date_posted` (optional: `24h` | `3d` | `7d` | `30d`)

**Response `200`**
```json
[
  {
    "external_id": "abc123",
    "source": "remoteok",
    "title": "Backend Engineer",
    "company": "Acme Inc",
    "location": "Remote",
    "url": "https://remoteok.com/remote-jobs/abc123",
    "posted_at": "2026-07-01T00:00:00Z",
    "description": "..."
  }
]
```

### `POST /jobs/save`

Persist one search result as a `job_descriptions` row for the current user. Requires auth.

**Request**: the full `JobListing` object from a `/jobs/search` result.

**Response `201`**: the created `job_descriptions` row (same shape as a saved job in `GET /jobs/saved`).

**Errors**
| Status | When |
|---|---|
| `409` | Already saved (same user + `source` + `external_id`) |

### `GET /jobs/saved`

List the current user's saved jobs, newest first. Requires auth.

**Response `200`**
```json
[
  {
    "id": 1,
    "source": "remoteok",
    "title": "Backend Engineer",
    "company": "Acme Inc",
    "location": "Remote",
    "url": "https://remoteok.com/remote-jobs/abc123",
    "posted_at": "2026-07-01T00:00:00Z",
    "raw_text": "...",
    "created_at": "2026-07-09T12:00:00Z"
  }
]
```

### `DELETE /jobs/saved/{id}`

Unsave a job. Requires auth.

**Response `204`**

**Errors**
| Status | When |
|---|---|
| `404` | Doesn't exist, or belongs to a different user |

---

## Planned (V3) — not yet built

Target shape for Checkpoints 14-20 (see ROADMAP.md). Same disclaimer as the V2 section above: written ahead of time as a build spec, not implemented yet.

### `POST /companies/track`

Track a priority company for alerts. Requires auth. Verifies the board resolves against the given provider before saving.

**Request**
```json
{ "company_name": "Acme Inc", "ats_provider": "greenhouse", "board_token": "acme" }
```

**Response `201`**: the created `tracked_companies` row.

**Errors**
| Status | When |
|---|---|
| `400` | `board_token` doesn't resolve against `ats_provider`'s API |
| `409` | Already tracking this exact `(ats_provider, board_token)` |

### `GET /companies/tracked`

List the current user's tracked companies. Requires auth.

### `DELETE /companies/tracked/{id}`

Stop tracking a company. Requires auth. `404` if not owned.

### `GET /alerts`

List the current user's alerts (new postings at tracked companies that scored above the relevance threshold), newest first. Requires auth.

**Response `200`**
```json
[
  {
    "id": 1,
    "company_name": "Acme Inc",
    "title": "Backend Engineer",
    "url": "https://boards.greenhouse.io/acme/jobs/123",
    "match_score": 82,
    "created_at": "2026-07-09T12:00:00Z"
  }
]
```

### `POST /internal/poll-companies`

**Not a user-facing route** — triggers one polling pass across every tracked company for every user (fetch → diff against seen postings → score new ones → write alerts → send emails). Guarded by a shared-secret header (e.g. `X-Poll-Secret`), not a user JWT — called by a scheduled GitHub Actions workflow, not through the frontend.

**Response `200`**: summary counts (companies polled, new postings found, alerts created, emails sent).

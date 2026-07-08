# High-Level Design

One-page picture of the system. For schema/folder detail see ARCHITECTURE.md; for step-by-step flows see FLOWS.md; for endpoint contracts see API.md; for what's actually built vs. planned see V1.md.

## System diagram (V1)

```
┌─────────────────────┐        JSON over HTTPS        ┌──────────────────────┐
│   React SPA (Vite)  │ ────────────────────────────▶ │   FastAPI backend    │
│  browser, port 5173 │ ◀──────────────────────────── │   port 8000          │
└─────────────────────┘                                └──────────┬───────────┘
                                                                    │
                                              ┌─────────────────────┼─────────────────────┐
                                              │                     │                     │
                                              ▼                     ▼                     ▼
                                     ┌────────────────┐   ┌──────────────────┐   ┌──────────────────┐
                                     │  PostgreSQL     │   │   Gemini API      │   │  Uploaded resume  │
                                     │  (Neon)         │   │  (gemini-2.0-     │   │  file (in-memory, │
                                     │  users/resumes/ │   │  flash) match     │   │  parsed then      │
                                     │  job_descs/     │   │  scoring + cover  │   │  discarded)       │
                                     │  matches        │   │  letters          │   │                   │
                                     └────────────────┘   └──────────────────┘   └──────────────────┘
```

V2 adds outbound calls from the backend to public job-board APIs — RemoteOK and Arbeitnow first (no key needed), then Adzuna and USAJobs (free API key each) — behind one normalized `JobListing` adapter interface (see ARCHITECTURE.md). Search results are ephemeral (not persisted); only explicitly-saved jobs get written to `job_descriptions`.

V3 adds an `applications` table, plus a priority-company alerts pipeline that's the first part of this system *not* driven by a live user request: a scheduled GitHub Actions workflow calls a shared-secret-guarded `POST /internal/poll-companies` on a timer, which fetches postings from tracked companies' ATS boards (Greenhouse/Lever/Ashby), scores new ones against the user's resume via the same Gemini call used in Flow 2, and emails alerts above a relevance threshold. V3 also adds an optional, separately-run Playwright process for auto-apply — deliberately not part of the always-on request path above.

## Components and responsibilities

| Component | Responsibility | Talks to |
|---|---|---|
| React SPA | Renders UI, holds the JWT (after Checkpoint 7), calls the backend REST API | FastAPI backend only — never touches the DB or Gemini directly |
| FastAPI backend | Auth, request validation, business logic, the only thing allowed to talk to Postgres or Gemini | Postgres (Neon), Gemini API, (V2) RemoteOK/Arbeitnow/Adzuna/USAJobs, (V3) Greenhouse/Lever/Ashby, an email provider |
| GitHub Actions (V3) | Wakes the backend on a schedule since Render's free tier sleeps when idle; has no direct access to the DB or any secret beyond the shared poll secret | `POST /internal/poll-companies` only |
| PostgreSQL (Neon) | System of record: users, resumes, job descriptions, match results | Backend only |
| Gemini API | Stateless: given resume text + JD text, returns a structured match score / missing skills / cover letter. Holds no data between calls | Backend only |

The one-way arrows matter: the frontend is intentionally "dumb" (no direct DB/Gemini access, no business logic) — every decision and every credential lives in the backend. This is the same reason a Spring MVC frontend never gets a DB connection string; the browser is untrusted.

## Why this shape (short version — see V1.md for the full reasoning behind each choice)

- **Frontend is a pure SPA**, not Next.js, because the backend already exists (FastAPI) — no server-rendering framework is needed to fill a role that's already filled.
- **One relational DB (Postgres)**, not a document store, because the data is genuinely relational (`users → resumes → job_descriptions → matches`) with real joins needed for V3 analytics.
- **AI calls are stateless and isolated to the backend** — the frontend never sees an API key, and every call happens through a versioned schema, not ad hoc. Originally OpenAI, switched to Gemini for its no-card free tier — see V1.md's "Provider swap" note at the end of Checkpoint 6.
- **Job scraping is out of the request path entirely in V1** — added in V2 via legitimate APIs, not by scraping LinkedIn/Indeed directly (see ARCHITECTURE.md's "Job sourcing strategy").

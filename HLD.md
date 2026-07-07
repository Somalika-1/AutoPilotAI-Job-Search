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

V2 adds outbound calls from the backend to public job-board APIs (Adzuna, RemoteOK, Arbeitnow, USAJobs, Greenhouse/Lever). V3 adds an `applications` table and an optional, separately-run Playwright process for auto-apply — deliberately not part of the always-on request path above.

## Components and responsibilities

| Component | Responsibility | Talks to |
|---|---|---|
| React SPA | Renders UI, holds the JWT (after Checkpoint 7), calls the backend REST API | FastAPI backend only — never touches the DB or Gemini directly |
| FastAPI backend | Auth, request validation, business logic, the only thing allowed to talk to Postgres or Gemini | Postgres (Neon), Gemini API, (V2) job-board APIs |
| PostgreSQL (Neon) | System of record: users, resumes, job descriptions, match results | Backend only |
| Gemini API | Stateless: given resume text + JD text, returns a structured match score / missing skills / cover letter. Holds no data between calls | Backend only |

The one-way arrows matter: the frontend is intentionally "dumb" (no direct DB/Gemini access, no business logic) — every decision and every credential lives in the backend. This is the same reason a Spring MVC frontend never gets a DB connection string; the browser is untrusted.

## Why this shape (short version — see V1.md for the full reasoning behind each choice)

- **Frontend is a pure SPA**, not Next.js, because the backend already exists (FastAPI) — no server-rendering framework is needed to fill a role that's already filled.
- **One relational DB (Postgres)**, not a document store, because the data is genuinely relational (`users → resumes → job_descriptions → matches`) with real joins needed for V3 analytics.
- **AI calls are stateless and isolated to the backend** — the frontend never sees an API key, and every call happens through a versioned schema, not ad hoc. Originally OpenAI, switched to Gemini for its no-card free tier — see V1.md's "Provider swap" note at the end of Checkpoint 6.
- **Job scraping is out of the request path entirely in V1** — added in V2 via legitimate APIs, not by scraping LinkedIn/Indeed directly (see ARCHITECTURE.md's "Job sourcing strategy").

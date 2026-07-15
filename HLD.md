# High-Level Design

One-page picture of the system. For schema/folder detail see ARCHITECTURE.md; for step-by-step flows see FLOWS.md; for endpoint contracts see API.md; for what's actually built vs. planned see V1.md.

## System diagram (V1 + V2 backend, as built)

```
┌─────────────────────┐        JSON over HTTPS        ┌──────────────────────┐
│   React SPA (Vite)  │ ────────────────────────────▶ │   FastAPI backend    │
│  Vercel (prod) /    │ ◀──────────────────────────── │   Render (prod) /    │
│  localhost:5173     │                                │   localhost:8000     │
└─────────────────────┘                                └──────────┬───────────┘
                                                                    │
                       ┌───────────────────┬──────────────────────┼──────────────────────┐
                       │                   │                      │                      │
                       ▼                   ▼                      ▼                      ▼
              ┌────────────────┐ ┌──────────────────┐  ┌───────────────────────┐ ┌──────────────────┐
              │  PostgreSQL     │ │   Gemini API      │  │ RemoteOK / Arbeitnow /│ │  Uploaded resume  │
              │  (Neon)         │ │  match scoring +  │  │ Adzuna / USAJobs      │ │  file (in-memory, │
              │  users/resumes/ │ │  cover letters     │  │ (job search, one     │ │  parsed then      │
              │  job_descs/     │ │                    │  │ adapter per provider,│ │  discarded)       │
              │  matches        │ │                    │  │ Checkpoints 9-12)    │ │                   │
              └────────────────┘ └──────────────────┘  └───────────────────────┘ └──────────────────┘
```

V1 (auth, resume upload, AI matching, cover letters) and V2's job-search backend (search/save/list/unsave against four job boards, Checkpoints 9-12) are both built and deployed. Search results are ephemeral (not persisted); only explicitly-saved jobs get written to `job_descriptions`. What's still missing from this picture: a frontend page for job search/saved jobs (Checkpoint 13) — the boxes above are real and reachable via the API today, just not yet wired into the React UI.

V3 (not yet built) adds an `applications` table, plus a priority-company alerts pipeline that's the first part of this system *not* driven by a live user request: a scheduled GitHub Actions workflow calls a shared-secret-guarded `POST /internal/poll-companies` on a timer, which fetches postings from tracked companies' ATS boards (Greenhouse/Lever/Ashby), scores new ones against the user's resume via the same Gemini call used in Flow 2, and emails alerts above a relevance threshold. V3 also adds an optional, separately-run Playwright process for auto-apply — deliberately not part of the always-on request path above.

## Components and responsibilities

| Component | Responsibility | Talks to |
|---|---|---|
| React SPA | Renders UI, holds the JWT (after Checkpoint 7), calls the backend REST API. Deployed on Vercel | FastAPI backend only — never touches the DB or Gemini directly |
| FastAPI backend | Auth, request validation, business logic, the only thing allowed to talk to Postgres, Gemini, or any job-board API. Deployed on Render (Docker) | Postgres (Neon), Gemini API, RemoteOK/Arbeitnow/Adzuna/USAJobs (built, Checkpoints 9-12), (V3, not yet built) Greenhouse/Lever/Ashby, an email provider |
| RemoteOK / Arbeitnow / Adzuna / USAJobs | External job-board APIs, each behind its own adapter (`app/services/job_scraper/`) normalized to one shared `JobListing` shape. RemoteOK/Arbeitnow need no key; Adzuna/USAJobs each need a free API key | Backend only — a missing key or a failed request for one provider is skipped, not fatal to the request |
| GitHub Actions (V3, not yet built) | Wakes the backend on a schedule since Render's free tier sleeps when idle; has no direct access to the DB or any secret beyond the shared poll secret | `POST /internal/poll-companies` only |
| PostgreSQL (Neon) | System of record: users, resumes, job descriptions (including saved job-board listings since Checkpoint 11), match results | Backend only |
| Gemini API | Stateless: given resume text + JD text, returns a structured match score / missing skills / cover letter. Holds no data between calls | Backend only |

The one-way arrows matter: the frontend is intentionally "dumb" (no direct DB/Gemini access, no business logic) — every decision and every credential lives in the backend. This is the same reason a Spring MVC frontend never gets a DB connection string; the browser is untrusted.

## Why this shape (short version — see V1.md for the full reasoning behind each choice)

- **Frontend is a pure SPA**, not Next.js, because the backend already exists (FastAPI) — no server-rendering framework is needed to fill a role that's already filled.
- **One relational DB (Postgres)**, not a document store, because the data is genuinely relational (`users → resumes → job_descriptions → matches`) with real joins needed for V3 analytics.
- **AI calls are stateless and isolated to the backend** — the frontend never sees an API key, and every call happens through a versioned schema, not ad hoc. Originally OpenAI, switched to Gemini for its no-card free tier — see V1.md's "Provider swap" note at the end of Checkpoint 6.
- **Job scraping is out of the request path entirely in V1** — V2 added real job search via legitimate public APIs (RemoteOK, Arbeitnow, Adzuna, USAJobs), not by scraping LinkedIn/Indeed directly (see ARCHITECTURE.md's "Job sourcing strategy").

# Architecture

## Design principles

1. **No infrastructure before features.** Every piece of tech (Postgres, JWT, Playwright, embeddings) is added at the checkpoint where it's actually needed, not up front.
2. **Structured LLM I/O.** All OpenAI calls that feed application logic use `response_format={"type": "json_schema", ...}` (structured outputs), not "please return JSON" prompted in free text. This is the single biggest reliability win for beginners integrating LLMs into real apps.
3. **One relational schema, designed once.** Auth lands in V1 specifically so the schema (below) doesn't need a breaking migration when V2/V3 add saved jobs and application tracking.

## Folder structure

```
autopilot-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory, router registration
│   │   ├── config.py            # env/settings (pydantic-settings)
│   │   ├── database.py          # SQLAlchemy engine/session
│   │   ├── models/               # SQLAlchemy models (one file per table or grouped)
│   │   ├── routes/               # API routers: auth, resumes, jobs, matches, cover_letters
│   │   ├── services/
│   │   │   ├── resume_parser/    # PyPDF / python-docx text extraction
│   │   │   ├── ai_engine/        # OpenAI client wrapper, prompt templates, structured schemas
│   │   │   └── job_scraper/      # V2+: job-board API clients (Adzuna, RemoteOK, etc.)
│   │   ├── auth/                  # JWT creation/verification, password hashing, dependencies
│   │   └── utils/
│   ├── alembic/                   # DB migrations
│   ├── tests/                     # pytest
│   └── requirements.txt
├── frontend/                       # React + Vite SPA
│   ├── src/
│   │   ├── pages/                  # route components (Login, Upload, Dashboard, Results)
│   │   ├── components/
│   │   ├── lib/                    # API client (fetch/axios wrapper), shared types
│   │   └── router.tsx              # React Router route definitions
│   ├── index.html
│   └── vite.config.ts
├── README.md
├── ARCHITECTURE.md
├── ROADMAP.md
└── .env.example
```

This differs from the original sketch mainly by nesting `resume_parser/`, `ai_engine/`, and `job_scraper/` under `backend/app/services/` instead of as top-level folders — keeps them as normal importable Python submodules of one package instead of orphaned directories.

## Database schema (planned from V1, built incrementally)

```
users
  id (pk)
  email (unique)
  hashed_password
  created_at

resumes
  id (pk)
  user_id (fk -> users.id)
  original_filename
  extracted_text
  uploaded_at

job_descriptions
  id (pk)
  user_id (fk -> users.id)
  source            -- "manual" | "adzuna" | "remoteok" | ... (V2+)
  title
  company
  raw_text
  created_at

matches
  id (pk)
  resume_id (fk -> resumes.id)
  job_description_id (fk -> job_descriptions.id)
  score              -- int 0-100
  missing_skills     -- jsonb array
  strengths          -- jsonb array
  cover_letter       -- text, nullable until generated
  created_at

applications        -- V3
  id (pk)
  match_id (fk -> matches.id)
  status             -- "saved" | "applied" | "interviewing" | "rejected" | "offer"
  applied_at
  notes
```

Only `users`, `resumes`, `job_descriptions`, and `matches` are built in V1. `applications` is added in V3 when tracking lands.

## Core request flow (V1)

```
1. POST /auth/signup, /auth/login          -> JWT issued
2. POST /resumes/upload (multipart, JWT)   -> extract text (PyPDF/docx) -> store in `resumes`
3. POST /matches (resume_id, jd_text, JWT) ->
       a. store `job_descriptions` row
       b. call OpenAI with resume text + JD text, structured output schema:
          { "score": int, "missing_skills": string[], "strengths": string[] }
       c. store result in `matches`
4. POST /matches/{id}/cover-letter (JWT)   -> OpenAI call using resume + JD + match ->
       cover letter text -> stored on `matches.cover_letter`
5. Frontend renders score, skills, strengths, and cover letter
```

## AI integration notes

- Default model: `gpt-4o-mini` (cost-effective for iteration); configurable via `OPENAI_MODEL` env var.
- All prompts live in `backend/app/services/ai_engine/prompts.py` as functions, not inlined in route handlers — keeps routes thin and prompts reviewable/testable in isolation.
- Embeddings/semantic search are **not** part of V1. If keyword-ish matching proves too shallow later, add an embeddings-based similarity step as an additive enhancement to the existing `matches` flow — not a rewrite.

## Job sourcing strategy (V2+)

LinkedIn/Indeed/Naukri scraping was in the original plan but is demoted: those platforms actively detect and block automated access, and scraping them violates their Terms of Service — a common reason beginner clones of this project stall on IP/account bans instead of shipping. V2 instead uses legitimate, free public job-board APIs: **Adzuna, RemoteOK, Arbeitnow, USAJobs, and Greenhouse/Lever public job boards**. These have no scraping risk and are stable enough to build real filtering (date/location) on top of.

Playwright-based LinkedIn/Indeed automation is kept only as an **optional, explicitly risk-flagged V3 stretch goal** — run only against the user's own account, with a manual confirm-before-submit step and heavy rate-limiting, never for other users or at scale.

## Deployment

- Frontend → Vercel (static SPA build via `vite build`, served as a static site)
- Backend → Railway or Render; a `Dockerfile` is added at the deployment checkpoint (end of V1), not before — not needed for local dev with `uvicorn`.
- Database → managed Postgres on the same platform as the backend (Railway/Render Postgres addon), or Supabase as an alternative.
- Redis is **not** part of V1; only considered later if caching becomes a measured problem (e.g. repeated identical match requests).

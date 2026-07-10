# Architecture

## Design principles

1. **No infrastructure before features.** Every piece of tech (Postgres, JWT, Playwright, embeddings) is added at the checkpoint where it's actually needed, not up front.
2. **Structured LLM I/O.** All LLM calls that feed application logic constrain the response to a Pydantic schema (structured outputs), not "please return JSON" prompted in free text. This is the single biggest reliability win for beginners integrating LLMs into real apps.
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
│   │   ├── schemas/               # Pydantic request/response DTOs (separate from DB models)
│   │   ├── routes/               # API routers: auth, resumes, jobs, matches, cover_letters
│   │   ├── services/
│   │   │   ├── resume_parser/    # PyPDF / python-docx text extraction
│   │   │   ├── ai_engine/        # Gemini client wrapper, prompt templates, structured schemas
│   │   │   └── job_scraper/      # V2+: job-board API clients (Adzuna, RemoteOK, etc.)
│   │   ├── auth/                  # JWT creation/verification, password hashing, dependencies
│   │   └── utils/
│   ├── alembic/                   # DB migrations
│   ├── tests/                     # pytest
│   └── requirements.txt
├── frontend/                       # React + Vite SPA
│   ├── src/
│   │   ├── pages/                  # Root, Login, Signup, Dashboard (upload+match+cover-letter, one page)
│   │   ├── components/             # ProtectedRoute (auth-gated route wrapper)
│   │   ├── context/                # AuthContext: token/user state, persisted in localStorage
│   │   ├── lib/                    # api.ts - typed fetch client, one function per backend endpoint
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
  user_id (fk -> users.id, ON DELETE CASCADE)
  original_filename
  extracted_text
  uploaded_at

job_descriptions
  id (pk)
  user_id (fk -> users.id, ON DELETE CASCADE)
  source            -- "manual" | "remoteok" | "arbeitnow" | "adzuna" | "usajobs" (V2+)
  title
  company
  raw_text
  created_at
  -- added in V2 Checkpoint 11, nullable, only populated when source != "manual":
  url               -- listing/apply link
  location
  external_id       -- source's own id, for de-dup; unique together with (user_id, source)
  posted_at         -- when the source says the job was posted (not when we saved it)

matches
  id (pk)
  resume_id (fk -> resumes.id, ON DELETE CASCADE)
  job_description_id (fk -> job_descriptions.id, ON DELETE CASCADE)
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

tracked_companies    -- V3, Checkpoint 14
  id (pk)
  user_id (fk -> users.id, ON DELETE CASCADE)
  company_name        -- display name, user-chosen
  ats_provider         -- "greenhouse" | "lever" | "ashby"
  board_token          -- provider-specific slug identifying this company's board
  created_at
  -- unique (user_id, ats_provider, board_token): can't track the same board twice

company_postings     -- V3, Checkpoint 15 — "seen postings" ledger per tracked company
  id (pk)
  tracked_company_id (fk -> tracked_companies.id, ON DELETE CASCADE)
  external_id          -- provider's own posting id
  title
  url
  first_seen_at
  -- unique (tracked_company_id, external_id): dedup across repeated polls

alerts               -- V3, Checkpoint 16 — a posting that scored well against the user's resume
  id (pk)
  user_id (fk -> users.id, ON DELETE CASCADE)
  company_posting_id (fk -> company_postings.id, ON DELETE CASCADE)
  match_score
  emailed_at           -- null until the notification email actually sends
  created_at
```

Only `users`, `resumes`, `job_descriptions`, and `matches` are built in V1. `applications` is added in V3 when tracking lands.

All child foreign keys cascade on delete — deleting a user removes their resumes, job descriptions, and matches with them. Added after the fact once test data made the lack of it obvious (see V1.md's "Test data cleanup" section); it's also just the correct real-world behavior for account deletion, not only a testing convenience.

## Core request flow (V1)

See FLOWS.md for the step-by-step user flow + data flow diagrams, and API.md for the exact request/response shape of each endpoint. Short version: signup/login issues a JWT → upload a resume (extracted server-side) → submit a job description alongside a resume to get a structured Gemini match result → optionally generate a cover letter from that match.

## AI integration notes

- Provider: **Google Gemini** (`google-genai` SDK), default model `gemini-2.0-flash`, configurable via `GEMINI_MODEL` env var. Originally planned as OpenAI (`gpt-4o-mini`); switched during Checkpoint 5/6 because OpenAI now requires a payment method with no free tier, while Gemini's free tier (via Google AI Studio) needs no card and its SDK supports the same "constrain the response to a Pydantic model" structured-output pattern — see V1.md's Checkpoint 5 for the full reasoning. `MatchResult`/`CoverLetterResult` (the actual contracts) didn't change, only the client calling them.
- All prompts live in `backend/app/services/ai_engine/prompts.py` as functions, not inlined in route handlers — keeps routes thin and prompts reviewable/testable in isolation.
- Embeddings/semantic search are **not** part of V1. If keyword-ish matching proves too shallow later, add an embeddings-based similarity step as an additive enhancement to the existing `matches` flow — not a rewrite.

## Job sourcing strategy (V2+)

LinkedIn/Indeed/Naukri scraping was in the original plan but is demoted: those platforms actively detect and block automated access, and scraping them violates their Terms of Service — a common reason beginner clones of this project stall on IP/account bans instead of shipping. V2 instead uses legitimate, free public job-board APIs: **RemoteOK, Arbeitnow, Adzuna, and USAJobs**. These have no scraping risk and are stable enough to build real filtering (date/location) on top of.

RemoteOK and Arbeitnow shipped first (Checkpoint 9) because both have public JSON endpoints with no API key/signup required — lowest-friction way to get a real multi-provider search working end to end. Adzuna and USAJobs followed (Checkpoint 10) on the same interface; both need a free API key (same "sign up for a free-tier credential" pattern already used for Gemini in Checkpoint 5) — built and unit-tested against each provider's documented response shape, but not yet live-verified with real keys since none were available at build time. Both providers are designed to silently return no results if their key is missing, so the app works today with only the two keyless providers and picks up the other two automatically once real keys are added to `.env` — no code change needed.

**Greenhouse/Lever are deliberately not part of V2's job-search checkpoints.** Their public APIs are scoped per employer (you fetch *one specific company's* board via that company's board token) — there's no global "search every company's postings for 'backend engineer'" endpoint, which is the actual feature V2 builds. They're kept as a documented option for later — e.g. a V3 application-tracking feature could deep-link to a specific employer's Greenhouse/Lever board — not dropped for lack of value, just because they don't fit this feature's shape.

### Provider adapter pattern

Every provider lives in `backend/app/services/job_scraper/<provider>.py` and exposes one function, `search(query: str, location: str | None, date_posted: str | None) -> list[JobListing]`, mapping that provider's raw response onto one shared Pydantic schema (`app/services/job_scraper/schemas.py`):

```
JobListing
  external_id: str    # provider's own id, for de-dup and later "save" persistence
  source: str          # "remoteok" | "arbeitnow" | "adzuna" | "usajobs"
  title: str
  company: str | None
  location: str | None
  url: str             # apply/listing link
  posted_at: datetime | None
  description: str
```

`GET /jobs/search` calls every configured provider's `search()` and concatenates the results — same "one normalized contract, many adapters behind it" shape as `ai_engine`'s structured Gemini output, just for external HTTP APIs instead of an LLM. Search results themselves are **not** persisted; only `POST /jobs/save` (Checkpoint 11) writes a specific result into `job_descriptions`.

## Priority-company alerts (V3, Checkpoints 14-18)

Same adapter pattern as job search, applied per-company instead of by keyword: `app/services/job_scraper/ats/<provider>.py` (Greenhouse, Lever, Ashby), each exposing `fetch_postings(board_token: str) -> list[JobListing]` against that provider's public per-company board API — no API key needed for any of the three. A company not on one of these platforms is simply "not trackable" (surfaced to the user as such), rather than falling back to per-site HTML scraping, which would be fragile and legally murkier than the platforms' own public APIs.

**Polling shape**: for each row in `tracked_companies`, call that provider's `fetch_postings()`, diff the result against `company_postings` (the seen-postings ledger, keyed on `external_id`) to find genuinely new listings, then score each new listing against the user's most recent resume using the *existing* `score_resume_against_job()` from `ai_engine` — no new AI integration, just reusing V1's scoring on a different input source. Only scores at/above a relevance threshold get written to `alerts` and emailed, so an unrelated new posting at a tracked company doesn't spam the user just because it exists.

**Scheduling**: Render's free-tier web service spins down after inactivity, so an in-process scheduler (e.g. APScheduler running inside the FastAPI app) can't be trusted to fire on a wall-clock schedule — it only runs while the process happens to be awake. Instead, `POST /internal/poll-companies` is a plain endpoint guarded by a shared-secret header (not a user JWT — nothing about polling is "as" a particular logged-in user), triggered by a **scheduled GitHub Actions workflow** (e.g. every 6 hours) making an authenticated HTTP call to it. The incoming request itself wakes the Render service if it was asleep, so no always-on server is needed. This is the same "push the trigger in from outside" shape as a Spring `@Scheduled` job, just implemented as an external cron caller instead of an in-process timer, to work around the free-tier sleep behavior.

**Notifications**: email via a free-tier transactional provider (Resend or SendGrid) or Gmail SMTP — chosen at build time, whichever has the least setup friction, same "free tier, no card" bar applied to Gemini in V1.

Playwright-based LinkedIn/Indeed automation is kept only as an **optional, explicitly risk-flagged V3 stretch goal** — run only against the user's own account, with a manual confirm-before-submit step and heavy rate-limiting, never for other users or at scale.

## Deployment

- Frontend → Vercel (static SPA build via `vite build`), `frontend/vercel.json` rewrites all paths to `index.html` so client-side routes survive a hard refresh.
- Backend → Render, deployed from `backend/Dockerfile` (Root Directory `backend`, Docker build context = `backend/`); `alembic upgrade head` runs as part of the container's start command before `uvicorn` starts, so every deploy is auto-migrated.
- Database → the same Neon Postgres provisioned back in Checkpoint 2 — no separate Railway/Render Postgres addon was needed since a working managed DB already existed.
- CORS origins are env-driven (`CORS_ORIGINS` on the backend), not hardcoded, so the Vercel production URL (and any preview URLs) can be allow-listed without a code change.
- Redis is **not** part of V1 or V2; only considered later if caching becomes a measured problem (e.g. repeated identical match requests, or job-search rate limits).

See V1.md's Checkpoint 8 for the full deploy log (Render dashboard field gotchas, CORS/double-slash debugging).

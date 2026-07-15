# Interview Prep — AutoPilotAI

This doc is different from the others: not a technical reference, but a rehearsal script. Everything here is pulled from the real decisions in V1.md/ARCHITECTURE.md — nothing invented — condensed into the form you'd actually *say out loud* in an interview. Practice saying these, don't just read them.

---

## The 60-second pitch

> "AutoPilotAI is a full-stack AI career assistant — you upload a resume, paste a job description, and it gives you a match score, a skill-gap breakdown, and a tailored cover letter, using Google's Gemini API with structured outputs. It also searches real job postings across four job boards and lets you save the ones you care about. I built the backend in FastAPI with hand-rolled JWT auth and a PostgreSQL database, and the frontend in React — it's deployed and live, not just running locally. The part I'm most proud of is that it's not a ChatGPT wrapper — there's a real relational schema, real auth, real automated tests, and every AI call returns schema-validated JSON instead of parsed free text."

That last sentence is the one to lead with — it's the difference between "I called an API" and "I engineered a system."

---

## Tech stack — what and why (one line each)

| Layer | Choice | Why (say this) |
|---|---|---|
| Backend | FastAPI (Python) | Automatic request validation and API docs from Pydantic models — closest Python equivalent to Spring's `@Valid` + springdoc-openapi, but built in |
| Database | PostgreSQL (hosted on Neon) | Data is genuinely relational (users → resumes → job descriptions → matches with real foreign keys); Postgres's `JSONB` also let me store the AI's structured output flexibly without giving up relational integrity elsewhere |
| ORM / migrations | SQLAlchemy 2.0 + Alembic | Same role as Hibernate + Flyway — typed models, versioned reviewable migrations instead of auto-DDL |
| Auth | Hand-rolled JWT (bcrypt + PyJWT) | Built it myself instead of a SaaS (Clerk/Auth0) specifically so I could speak to how auth actually works, not just that I wired one up |
| AI | Google Gemini (`gemini-2.5-flash`), structured outputs | Constrains the model's response to a Pydantic schema — the SDK hands back an already-validated object, not a string I have to hope is valid JSON |
| Frontend | React + Vite + TypeScript + Tailwind | Backend already exists as a separate API, so the frontend is a plain SPA — no need for a meta-framework (Next.js) whose main selling points (SSR, its own API routes) would go unused |
| File parsing | pypdf, python-docx | Extract text server-side from uploaded PDF/DOCX resumes |
| Job search | RemoteOK, Arbeitnow, Adzuna, USAJobs behind one adapter interface | Four real public job-board APIs, not scraping — each provider maps to one shared `JobListing` schema, same "structured contract, swappable implementation" idea used for the AI layer |
| Deployment | Vercel (frontend) + Render (backend, Docker) + Neon (Postgres) | Actually live, not just running locally — CORS origins are env-driven so the same code works in both places with no code change |
| Testing | pytest, 39 tests | Auth, upload, matching, and job search/save covered; external AI and job-board API calls mocked so tests are fast, free, and don't depend on third parties being up |

---

## "Why X over Y" — the questions they'll actually ask

**Why FastAPI over Django or Flask?**
Django is batteries-included but a lot of that (its ORM's admin panel, templating) goes unused in an API-only backend. Flask is minimal but you hand-roll validation and docs yourself. FastAPI gives request/response validation and auto-generated OpenAPI docs for free, straight from the same Pydantic models I'd need to write anyway.

**Why Postgres over MongoDB?**
The schema has real foreign keys and needs real joins (a match belongs to a resume *and* a job description; a user's dashboard needs to join across all of it). Postgres's `JSONB` column type meant I still got flexible storage for the AI's semi-structured output (skill lists) without giving up relational integrity for everything else — best of both, not a tradeoff.

**Why did you build your own auth instead of using Clerk/Auth0?**
Two reasons: it's a stronger interview story — I can actually explain how a JWT is signed and verified, not just that a button says "Sign in" — and it kept all user data in one database instead of splitting identity across a third-party provider.

**Why Gemini and not OpenAI, if the plan originally said OpenAI?**
I actually built it against OpenAI first. Partway through, OpenAI removed free trial credits for new accounts — no free tier without a card on file. I evaluated three alternatives (Gemini's free tier, Groq's OpenAI-compatible free tier, and a local model via Ollama), and picked Gemini because it needed no card and its SDK supported the same "give it a Pydantic model, get a validated object back" pattern I'd already built around. The swap touched exactly 5 files — the config, the AI client, the prompts, the requirements file, and the env vars — because the actual data contracts (`MatchResult`, `CoverLetterResult`) never changed. Every route, schema, and test was completely unaffected. That's the payoff of designing to an interface instead of a concrete implementation.

**Why React instead of Next.js, when your original plan said Next.js?**
Next.js's biggest features — server-side rendering, its own API routes — exist to let a frontend act as its own backend. I already had a real backend, so none of that would get used; the frontend is just a browser app calling my API. Plain React with Vite was the more direct match, with no unused framework machinery to carry.

**Why structured outputs instead of just prompting the AI to "return JSON"?**
Because free-text JSON from an LLM isn't reliable — models add chatty preambles, wrap output in markdown, or occasionally break the JSON shape. Structured outputs constrain the response to a schema at the API level, so what comes back is already validated and typed, not something I parse and hope is correct.

**Why did you build job search against four separate providers instead of just picking one?**
No single free job-board API covers the market, and I wanted the design to prove it could scale to more sources without a rewrite. Each provider (RemoteOK, Arbeitnow, Adzuna, USAJobs) gets one small adapter file that maps its own response shape onto one shared `JobListing` schema — the same "one contract, swappable implementation" pattern I already used for the AI provider swap. Adding a fifth provider later means writing one more adapter file, not touching the route, the tests, or anything else that already works.

**Why did you drop Greenhouse/Lever from job search but mention them in your roadmap for a different feature?**
Greenhouse/Lever's public APIs are scoped per-employer — you fetch one specific company's board, there's no "search every company's postings for a keyword" endpoint. That doesn't fit a keyword-search feature, but it's exactly the shape needed for a *different*, not-yet-built feature: letting a user track specific companies and get alerted to new postings there. Recognizing that the same integration fits a different feature, instead of forcing it into the wrong one, is the actual design decision worth mentioning.

---

## Architecture — if asked to draw it on a whiteboard

```
React SPA  ──HTTP/JSON──▶  FastAPI backend  ──▶  PostgreSQL (Neon)
                                 │
                                 └──▶  Gemini API (structured output)
```

Say: "The frontend never talks to the database or the AI directly — every request goes through the backend, which is the only thing holding credentials. That's deliberate: the browser is untrusted, so no API key or DB connection string ever reaches it."

**Request flow for the core feature** (say this if asked to walk through "what happens when a user uses the app"):
1. Sign up / log in → backend hashes the password with bcrypt, issues a signed JWT
2. Upload a resume → backend extracts text server-side (pypdf/python-docx), stores it
3. Paste a job description → backend calls Gemini with the resume text + JD text, constrained to a `MatchResult` schema → stores the score/skills/strengths
4. Generate a cover letter → separate endpoint, separate structured-output call, updates the same record

---

## Project structure — the folder walkthrough

```
backend/app/
  models/      → SQLAlchemy ORM models (like JPA @Entity classes)
  schemas/     → Pydantic request/response DTOs (kept separate from models on purpose —
                 same reason you don't return an @Entity straight from a Spring controller)
  routes/      → one file per resource (auth, resumes, matches)
  services/
    ai_engine/     → Gemini client, prompt templates, structured-output schemas
    resume_parser/ → PDF/DOCX text extraction
  auth/        → JWT creation/verification, password hashing

frontend/src/
  pages/       → Login, Signup, Dashboard (the whole upload→match→cover-letter flow, one page)
  context/     → AuthContext — holds the JWT, persisted in localStorage
  components/  → ProtectedRoute, and the score meter / skill chip / cover letter display
  lib/api.ts   → one typed function per backend endpoint
```

If asked *why* schemas are separate from models: "Same reason you'd never return a Hibernate entity directly from a Spring REST controller — I don't want a field I add to the database table (like the hashed password) to accidentally leak into an API response just because it exists on the object."

---

## Real challenges faced (concrete, not generic)

Pick 2-3 of these depending on how much time you have — each is a real thing that happened, not a rehearsed platitude.

**"A dependency I chose had a real compatibility bug, and I caught it before shipping."**
I originally planned to use `passlib` for password hashing (per my own initial architecture doc). When I actually installed and tested it, `passlib`'s bcrypt integration threw a warning on every single call because of a version mismatch with modern `bcrypt` — a known issue, not something breaking silently. I tested both before committing to either, found `bcrypt` used directly plus `PyJWT` worked cleanly with no warnings, and switched. Lesson: verify a library actually works before building five files around it, don't just trust what a tutorial says.

**"I found and fixed accessibility bugs by computing real numbers, not eyeballing them."**
When I redesigned the results UI, I picked colors from a validated palette rather than randomly — but even then, I computed the actual WCAG contrast ratio for every text-on-background pairing I introduced. Two failed: a warning-amber color at 1.79 contrast (needs 4.5) when used as text, and my first attempt at a button color came in at 4.42 — just under the threshold. I fixed both before shipping, not after a design review caught it.

**"A stale background process cost me real debugging time, and I turned it into a habit."**
More than once, a leftover `uvicorn` process from a previous test run was still holding port 8000, so my new code changes silently weren't being served — I was hitting old code and got confused by responses that didn't match what I'd just written. Once I understood the cause, I made "check for a process already on the port" a standard first step before starting any server, instead of debugging code that was actually fine.

**"Test data quietly became a real problem, and I fixed the root cause, not just the symptom."**
My test suite created real users in the actual development database on every run, with no cleanup. By the time I noticed, there were 83 stale test users sitting in production-adjacent data. I fixed it two ways: added `ON DELETE CASCADE` to the schema itself (which is also just correct behavior — deleting a user should delete their data), and added one `pytest` fixture that automatically deletes everything a test created, without any test needing to opt in. Verified it actually worked by running the full suite twice and checking real row counts came back to zero both times, not just that the tests passed.

**"I swapped a core external dependency mid-project with minimal blast radius, because of how I'd structured the code."**
(See the Gemini/OpenAI answer above — this is the same story, told as a challenge instead of a decision.)

**"Deploying it for real surfaced three bugs that never showed up in local dev, and I debugged each from first principles instead of guessing."**
Three, in order: (1) Render's dashboard "Root Directory" field silently didn't take effect from the initial service-creation form — the build failed with `Dockerfile: no such file or directory`, and I traced it to needing a Settings-page save plus a fresh manual deploy, not just a retry. (2) Once found, the *build context* was still wrong (`requirements.txt: not found`) because Root Directory controls the Docker build context too, not just where the Dockerfile is looked up — same root cause, one more layer deep. (3) After both were live, signup returned a 404 with a suspicious double slash in the URL — traced to a trailing slash on the frontend's `VITE_API_BASE_URL` env var concatenating badly with the API client's paths, fixed by stripping it and forcing a rebuild (Vite bakes env vars in at build time, so editing the value alone doesn't take effect). None of these were guessed at — each was diagnosed from the actual error message and the actual request URL.

**"I designed for a third-party API being down or unconfigured, not just for the happy path."**
The job search feature calls four independent external APIs (RemoteOK, Arbeitnow, Adzuna, USAJobs). Two need a paid-free-tier signup key; if that key isn't set, or if any single provider's request fails, that one provider is silently skipped rather than failing the whole search — a user searching jobs shouldn't get an error because one of four providers had a hiccup or because I hadn't set up every credential yet. This let the feature ship and be reviewed with only two of four providers actually configured, and the other two turn on automatically the moment real keys are added — no code change needed.

---

## Testing approach

"17 automated tests covering signup/login, resume upload, and AI matching — including negative cases like wrong passwords, someone else's resume, and missing auth tokens. The one deliberate tradeoff: tests hit a real database rather than a mocked one, because I wanted to prove the actual SQL and constraints work, not just that my Python logic is internally consistent — but I mock the actual AI API calls, since those cost real money per call and shouldn't fire on every test run. That's the same reasoning as mocking a payment gateway in a test suite: mock the boundary you don't own, keep everything you do own real."

If pushed on *why not mock the DB too*: "A mocked DB can't catch a real foreign-key violation or a real cascade-delete misconfiguration — and those are exactly the kind of bug that's cheap to catch in a test and expensive to catch in production."

---

## Security considerations (say these if asked "how did you think about security")

- Passwords are bcrypt-hashed (salted, one-way) — never stored or logged in plain text
- JWT signed with a random 48-byte secret (`HS256`); the payload carries only a user ID and expiry, nothing sensitive, since JWT payloads are base64-readable, not encrypted
- Login and signup return the *same* generic error for "no such user" and "wrong password" — distinguishing them would let an attacker enumerate valid emails
- Fetching another user's resume/match returns `404`, not `403` — a `403` would confirm the resource exists, which is itself information leakage
- CORS is restricted to an explicit, env-configured allowlist of frontend origins, not wildcarded
- File uploads are capped at 5MB and validated by extension before parsing
- No credential (DB connection string, JWT secret, Gemini API key, job-board API keys) is ever sent to the frontend — every privileged call happens server-side
- Duplicate-save prevention on job listings is enforced two ways — a friendly API-level check *and* a real database uniqueness constraint as the actual backstop — the same defense-in-depth idea as validating input at the API layer while still trusting the database's own constraints, not one or the other

**Honest gap to mention if asked "what would you improve":** there's no token revocation — a JWT is valid until it naturally expires, since nothing about login state is tracked server-side. Real revocation would need either short-lived tokens with a refresh flow, or a server-side denylist. Also no rate limiting yet, so nothing currently stops someone from hammering the signup or matching endpoints.

---

## What's not done yet (say this proactively, don't wait to be caught)

- **V2 frontend**: job search and save/saved-jobs backend endpoints are built, tested, and deployed — there's just no page in the React UI for them yet, so today they're only reachable via the API directly (Swagger UI or `curl`)
- **Two of the four job-search providers (Adzuna, USAJobs) haven't been live-verified** — built and unit-tested against their documented API shapes, but no free API key was available to actually call them for real yet. Worth saying out loud rather than letting someone assume all four were tested equally.
- **V3**: application status tracking, an analytics dashboard, priority-company alerts (get notified when a company you're watching posts a new job matching your resume), and an optional (explicitly risk-flagged, personal-account-only) browser-automation auto-apply feature

Framing that lands well: "I scoped this to build the hard, valuable part completely and correctly first — real auth, real schema, real AI integration with real tests — rather than spreading effort thin across every planned feature and having nothing fully working."

---

## Curveball questions, answered honestly

**"Why not just use ChatGPT directly instead of building this?"**
A raw ChatGPT conversation doesn't have accounts, doesn't save history, doesn't give you a structured score you can sort or track over time, and doesn't integrate into a workflow (upload once, match against many jobs). The AI call is one piece of a system — the system is the actual engineering.

**"How would this handle 1,000 concurrent users?"**
The stateless JWT design already scales horizontally — any backend instance can verify a token without shared session state. The real bottleneck would be synchronous AI calls blocking a request; in production I'd move those to a background job queue (e.g. Celery or FastAPI's background tasks) and have the frontend poll or use a websocket for the result, rather than holding a request open for a multi-second Gemini call.

**"What if the AI gives a wrong or unfair score?"**
Structured outputs guarantee the *shape* of the response is correct — a valid score, valid skill lists — not that the *content* is correct. That's a model-quality problem, not a schema problem. For production I'd want a way to flag/report a bad result and probably a confidence indicator, but that's out of scope for a V1.

**"What's the single biggest risk in this design?"**
Two real ones: no JWT revocation (already covered above), and a single point of dependency on one AI vendor — if Gemini has an outage or changes its API, matching and cover letters stop working. The provider swap experience is actually good evidence I could migrate again if needed, since the contract (`MatchResult`/`CoverLetterResult`) is decoupled from the specific SDK.

**"What happens if one of the four job-board APIs goes down or gets rate-limited?"**
That provider is skipped for that request — the other three still return results, and the user just gets a slightly smaller combined list instead of an error page. It's the same principle as a circuit breaker, implemented simply (a try/except around each provider call) because at this scale a full circuit-breaker library would be solving a problem I don't have yet. If a provider started failing constantly, adding a real backoff/circuit-breaker would be a natural next step — the adapter boundary already isolates where that change would go.

---

## If you remember nothing else, remember this

1. **It's not a wrapper** — real auth, real schema, real tests, structured (not free-text) AI output
2. **I made real engineering decisions and can defend all of them** — Postgres over Mongo, FastAPI over Flask, hand-rolled auth over Clerk, React over Next.js
3. **I hit real problems and fixed the root cause** — a library compatibility bug, an accessibility contrast failure, stale test data, a mid-project vendor swap — not just "it works now"
4. **I know what's not done and why that was the right call to defer**, not an oversight

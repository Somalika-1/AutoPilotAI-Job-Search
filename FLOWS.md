# User Flows & Data Flow

Each flow below shows the **user-facing steps** first, then the **technical data flow** underneath them. Status marks what's actually implemented as of the current checkpoint (see ROADMAP.md) vs. what's planned.

## Flow 1 — Sign up & log in

**Status: implemented end-to-end (backend Checkpoint 3, frontend Checkpoint 7)**

User flow:
1. User opens the app, enters email + password to create an account (`/signup`)
2. User logs in with the same credentials (`/login`)
3. App remembers the user is logged in for subsequent requests — JWT persisted in `localStorage`, restored on page reload via `AuthContext`

Data flow:
```
Browser                          FastAPI backend                     Postgres
   │  POST /auth/signup              │                                   │
   │  { email, password }  ────────▶ │  bcrypt-hash the password         │
   │                                 │  INSERT INTO users ─────────────▶ │
   │  ◀──────────────────────────── │  { id, email, created_at }        │
   │                                 │                                   │
   │  POST /auth/login               │                                   │
   │  { email, password }  ────────▶ │  SELECT user WHERE email = ... ─▶ │
   │                                 │  ◀─────────────────────────────── │
   │                                 │  verify bcrypt hash               │
   │                                 │  sign JWT { sub: user.id }        │
   │  ◀──────────────────────────── │  { access_token, token_type }     │
   │                                 │                                   │
   │  GET /auth/me                   │                                   │
   │  Authorization: Bearer <jwt> ─▶ │  decode JWT → user.id             │
   │                                 │  SELECT user WHERE id = ... ────▶ │
   │  ◀──────────────────────────── │  { id, email, created_at }        │
```
Full request/response shapes: see API.md. What was built and why (library choices, DTO layer, testing approach): see V1.md's Checkpoint 3. The rest of this section is the one thing neither of those covers — **how the mechanism itself works**, since none of it is Spring Security's filter-chain model.

### How signup actually works (`app/routes/auth.py`, `app/auth/security.py`)

1. FastAPI parses the request body straight into the `UserCreate` schema (`{email, password}`) — same job as `@Valid @RequestBody`.
2. Checks `users` for that email first (`SELECT ... WHERE email = ?`).
3. The password is never stored as-is. `hash_password()` calls `bcrypt.hashpw(password, bcrypt.gensalt())`. `gensalt()` makes a random salt and bcrypt bakes it directly into the output string (`$2b$12$<salt><hash>`) — there's no separate salt column, the hash is self-contained. Same algorithm family as Spring Security's `BCryptPasswordEncoder`.
4. The `User` row is inserted with that hash; `response_model=UserOut` on the route means only `{id, email, created_at}` is ever serialized back — `hashed_password` exists on the object but the DTO layer never exposes it.

### How login actually works

1. Look up the user by email, then `verify_password()` calls `bcrypt.checkpw(password, stored_hash)` — bcrypt pulls the salt back out of the stored hash, re-hashes the input with that same salt, and compares. One-way by design: verification never decrypts anything.
2. **Same error for "no such user" and "wrong password"** (`401 Invalid email or password`) — a deliberate choice, not laziness. Distinguishing the two would let an attacker enumerate which emails have accounts.
3. On success, `create_access_token()` builds a JWT — three base64 chunks joined by dots, `header.payload.signature`:
   - **header**: `{"alg": "HS256", "typ": "JWT"}`
   - **payload**: `{"sub": "<user id>", "exp": <expiry timestamp>}` — readable by anyone who base64-decodes it (not encrypted), so nothing sensitive ever goes in here
   - **signature**: `HMAC-SHA256(header + "." + payload, JWT_SECRET)` — this is what actually secures it. Only the server knows `JWT_SECRET`, so only the server can produce a signature that matches; changing one character of the payload breaks the signature check.

### How an authenticated request actually works (`GET /auth/me`, and any future protected route)

There's no global filter chain here — nothing inspects every incoming request by default. Each protected route opts in individually:

```python
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
```

FastAPI resolves `get_current_user` (and everything *it* depends on) **before** running the route body:
1. `OAuth2PasswordBearer` (a FastAPI built-in) reads the `Authorization: Bearer <token>` header and hands over just the token string. Missing header → automatic `401` before `get_current_user` even runs.
2. `decode_access_token()` calls `jwt.decode(token, JWT_SECRET, algorithms=["HS256"])`, which recomputes the HMAC signature and checks it matches, and checks `exp` hasn't passed. Either failing raises, caught and turned into `None`.
3. `payload["sub"]` (the user id baked in at login) is used to load that user **fresh from Postgres** — the token proves identity, not current data, so `/me` still hits the DB rather than trusting stale claims in the token.
4. The resolved `User` is injected straight into the route function as `current_user`.

Closest Spring Security equivalent: `oauth2_scheme` + `get_current_user` together do what a `JwtAuthenticationFilter` populating `SecurityContextHolder` does — except instead of one global filter guarding URL patterns via a `SecurityFilterChain` bean, every route declares `Depends(get_current_user)` itself. No annotations, no global config.

### Known tradeoff: stateless JWT, no revocation yet

Nothing about "who's logged in" is stored server-side — a validly-signed, non-expired token *is* the proof, which is why `JWT_SECRET` being a strong random value matters (Checkpoint 3 replaced the `.env.example` placeholder with a real 48-byte random secret — whoever holds that secret can mint tokens for any user id). There's currently no logout/revoke mechanism: a token stays valid until `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60) naturally expires. Real revocation would need short-lived tokens plus a refresh-token flow, or a server-side denylist — neither exists yet, added only if it's actually needed.

### How the frontend half actually works (`AuthContext.tsx`, `ProtectedRoute.tsx`)

- `AuthContext` holds `token` and `user` in React state, initialized by reading `localStorage` once on load (`useState(() => localStorage.getItem(...))`). On mount, if a token exists, it calls `GET /auth/me` to fetch the current user and confirm the token is still valid — if that call fails (expired/invalid token), the token is cleared and the user is treated as logged out.
- `login()`/`signup()` call the API, store the returned JWT in `localStorage`, and update state — every component reading `useAuth()` re-renders automatically since context changed.
- `ProtectedRoute` is a layout route (renders `<Outlet />`) that checks `token` from context: while the initial `/auth/me` check is in flight it shows a loading state, then either renders the nested route or redirects to `/login`. This is the client-side equivalent of the backend's `Depends(get_current_user)` — same "check identity before running the protected thing" shape, just running in the browser instead of on the server, and easily bypassed by a motivated user (disabling JS, editing localStorage) since **the frontend check is a UX convenience, not a security boundary** — every actual protected action still requires a valid JWT on the backend regardless of what the React UI shows.

## Flow 2 — Upload resume, match against a job description

**Status: implemented end-to-end, including frontend (Checkpoints 4, 5, 7); backend live-verified against Gemini, frontend verified via build/type-check and direct API tracing — see Checkpoint 7's notes on browser-testing limits**

User flow:
1. Logged-in user uploads a resume file (PDF or DOCX) — **implemented**
2. User pastes in a job description — **implemented**
3. User sees a match score, a list of missing skills, and a list of strengths — **implemented and live-verified against the real Gemini API** (real run: score 85, correctly identified missing Kubernetes/GraphQL and matched Java/Spring Boot/MySQL strengths — see V1.md's "Provider swap" section)

Data flow (upload half — implemented):
```
Browser                     FastAPI backend                     Postgres
  │ POST /resumes/upload         │                                  │
  │ (multipart file + JWT) ────▶ │ read file bytes, reject if       │
  │                              │ >5MB or not .pdf/.docx           │
  │                              │ extract_text() (pypdf/python-docx)│
  │                              │ reject (400) if no text found    │
  │                              │ INSERT INTO resumes ───────────▶ │
  │ ◀─────────────────────────── │ { id, original_filename,         │
  │                              │   extracted_text, uploaded_at }  │
```
Full request/response shape: see API.md. What was built and why (library choice, size limit, error cases): see V1.md's Checkpoint 4.

Data flow (matching half — implemented, `resume.user_id` ownership check omitted below for brevity, see API.md):
```
Browser                     FastAPI backend                  Postgres            Gemini
  │ POST /matches                │                                │                  │
  │ { resume_id, jd_text } ────▶ │ 404 if resume doesn't belong   │                  │
  │                              │ to the caller                 │                  │
  │                              │ INSERT INTO job_descriptions ▶ │                  │
  │                              │ generate_content() call:      │                  │
  │                              │ resume + JD text, config =    │                  │
  │                              │ response_schema=MatchResult ──┼─────────────────▶│
  │                              │ ◀──────────────────────────────────────────────── │
  │                              │ response.parsed → MatchResult │                  │
  │                              │ { score, missing_skills[],    │                  │
  │                              │   strengths[] }                │                  │
  │                              │ INSERT INTO matches ─────────▶ │                  │
  │ ◀─────────────────────────── │ match result                  │                  │
```
What was built and why (structured outputs via `.parse()`, mocked vs. live testing, ownership-check reasoning): see V1.md's Checkpoint 5.

## Flow 3 — Generate a tailored cover letter

**Status: implemented end-to-end, including frontend (Checkpoints 6, 7)**

User flow:
1. From a match result, user clicks "Generate cover letter" — **implemented**
2. User sees (and can copy via a Copy button, `navigator.clipboard`) a cover letter tailored to that resume + job description — backend live-verified against real Gemini: produced a coherent, on-topic letter referencing only real resume content, no invented experience, no placeholder brackets

Data flow:
```
Browser                        FastAPI backend                 Postgres          Gemini
  │ POST /matches/{id}/cover-letter │                              │                │
  │ (JWT) ─────────────────────▶   │ 404 if match doesn't belong  │                │
  │                                 │ to caller (via match.resume  │                │
  │                                 │ .user_id)                    │                │
  │                                 │ load resume + JD text for    │                │
  │                                 │ this match ─────────────────▶│                │
  │                                 │ generate_content() call:     │                │
  │                                 │ resume + JD, config =        │                │
  │                                 │ response_schema=              │                │
  │                                 │ CoverLetterResult ────────────┼───────────────▶│
  │                                 │ ◀───────────────────────────────────────────── │
  │                                 │ already-parsed                │                │
  │                                 │ { cover_letter: string }     │                │
  │                                 │ UPDATE matches SET           │                │
  │                                 │ cover_letter = ... ──────────▶│                │
  │ ◀───────────────────────────── │ full match incl. cover letter │                │
```
What was built and why (structured single-field output, ownership check via `match.resume.user_id`): see V1.md's Checkpoint 6.

## Flow 4 — Job discovery (V2)

**Status: search (Checkpoints 9-10) and save (Checkpoint 11) are implemented, backend only; list/unsave and the frontend are still planned.** Design matches ARCHITECTURE.md's provider-adapter pattern and API.md's contracts.

User flow:
1. Logged-in user searches jobs by keyword, with optional location / date-posted filters — **implemented (Checkpoints 9-10), backend only — no frontend page yet, verified via direct API calls**
2. User sees a merged results list from RemoteOK, Arbeitnow, Adzuna, and USAJobs — **implemented (Checkpoints 9-10)**. Adzuna/USAJobs need a free API key configured in `.env`; without one, that provider is silently skipped (not live-verified with real keys in this environment — see V2.md's Checkpoint 10)
3. User saves a result — **implemented (Checkpoint 11), backend only**. Feeding a saved job straight into the existing match flow (Flow 2) instead of pasting a JD by hand is still **planned, Checkpoint 13** (frontend wiring)
4. User views/removes their saved jobs on a separate page — **planned, Checkpoints 12-13**

Data flow (search — implemented):
```
Browser                     FastAPI backend                RemoteOK / Arbeitnow / Adzuna / USAJobs
  │ GET /jobs/search             │                                       │
  │ ?query=&location=&date ────▶ │ call each provider's search()        │
  │ (JWT)                        │ (adapter per provider) ─────────────▶│
  │                              │ ◀───────────────────────────────────│
  │                              │ RemoteOK/Arbeitnow: query/location/  │
  │                              │ date matched in-app (no native       │
  │                              │ search support). Adzuna/USAJobs:     │
  │                              │ passed through as native params.     │
  │                              │ Unconfigured or failing provider is  │
  │                              │ skipped, not fatal to the request    │
  │ ◀─────────────────────────── │ merged list, not persisted           │
```
What was built and why (client-side vs native filtering, per-provider unit tests, why live verification wasn't possible for the two keyed providers): see V2.md's Checkpoints 9-10.

Data flow (save — implemented):
```
Browser                     FastAPI backend                     Postgres
  │ POST /jobs/save              │                                  │
  │ { JobListing } ────────────▶ │ 409 if (user, source,            │
  │ (JWT)                        │ external_id) already saved       │
  │                              │ (checked in-app, and backed by   │
  │                              │ a real DB unique constraint)     │
  │                              │ INSERT INTO job_descriptions ──▶ │
  │ ◀─────────────────────────── │ saved job row                    │
```
What was built and why (schema migration, duplicate-save handling, cross-user isolation): see V2.md's Checkpoint 11.

Full request/response shapes: see API.md's "Planned (V2)" section. What gets built and why, once each checkpoint actually lands: see V2.md.

## Flow 5 — Priority-company alerts (V3)

**Status: planned, not yet built.** Design matches ARCHITECTURE.md's "Priority-company alerts" section and API.md's "Planned (V3)" contracts.

User flow:
1. User adds a priority company: name + ATS provider (Greenhouse/Lever/Ashby) + board token from that company's careers page URL — **planned, Checkpoint 14**
2. In the background, on a schedule (not user-initiated), the app checks each tracked company for new postings, scores any against the user's resume, and emails the user when a new posting scores well — **planned, Checkpoints 15-17**
3. User can also view alerts in-app on an "Alerts" page, and manage their tracked-company list — **planned, Checkpoint 18**

Data flow (the scheduled poll — planned):
```
GitHub Actions          FastAPI backend                  ATS API              Postgres            Gemini          Email provider
  │ (cron, e.g. every 6h) │                                  │                    │                  │                 │
  │ POST /internal/       │                                  │                    │                  │                 │
  │ poll-companies ─────▶ │ for each tracked_company:        │                    │                  │                 │
  │ (shared secret)       │  fetch_postings(provider,        │                    │                  │                 │
  │                       │  board_token) ──────────────────▶│                    │                  │                 │
  │                       │ ◀─────────────────────────────── │                    │                  │                 │
  │                       │  diff vs company_postings ───────┼───────────────────▶│                  │                 │
  │                       │  (unseen external_ids only)      │                    │                  │                 │
  │                       │  score_resume_against_job() for  │                    │                  │                 │
  │                       │  each new posting ────────────────┼────────────────────┼─────────────────▶│                 │
  │                       │  ◀──────────────────────────────────────────────────────────────────────  │                 │
  │                       │  INSERT alerts WHERE score ≥      │                    │                  │                 │
  │                       │  threshold ───────────────────────┼───────────────────▶│                  │                 │
  │                       │  send email per new alert ─────────────────────────────┼──────────────────┼────────────────▶│
  │ ◀──────────────────── │  summary counts                  │                    │                  │                 │
```

Full request/response shapes: see API.md's "Planned (V3)" section. What gets built and why, once each checkpoint actually lands: see V3.md.

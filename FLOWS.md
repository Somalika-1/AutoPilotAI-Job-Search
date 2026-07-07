# User Flows & Data Flow

Each flow below shows the **user-facing steps** first, then the **technical data flow** underneath them. Status marks what's actually implemented as of the current checkpoint (see ROADMAP.md) vs. what's planned.

## Flow 1 — Sign up & log in

**Status: implemented (Checkpoint 3, backend only — no frontend UI for it yet, Checkpoint 7)**

User flow:
1. User opens the app, enters email + password to create an account
2. User logs in with the same credentials
3. App remembers the user is logged in for subsequent requests

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

## Flow 2 — Upload resume, match against a job description

**Status: implemented and live-verified (Checkpoints 4 and 5)**

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

**Status: implemented and live-verified (Checkpoint 6)**

User flow:
1. From a match result, user clicks "Generate cover letter" — **implemented**
2. User sees (and can copy) a cover letter tailored to that resume + job description — **implemented and live-verified**: real run produced a coherent, on-topic letter referencing only real resume content, no invented experience, no placeholder brackets

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

## Flow 4 — Job discovery (V2) and application tracking (V3)

**Status: planned, not yet designed in detail — will be added here once Checkpoints 9+ (V2/V3) start.** See ROADMAP.md for what's planned at a feature level.

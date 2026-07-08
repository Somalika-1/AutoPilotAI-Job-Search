# Roadmap / Review Checkpoints

Each checkpoint is built and reviewed one at a time — nothing here is built ahead of where the checkmarks stop.

## V1 — MVP core

- [x] **Checkpoint 0** — Repo init, README, ARCHITECTURE, ROADMAP, `.gitignore`, `.env.example`
- [x] **Checkpoint 1** — Backend skeleton (FastAPI app factory, health check, config loading) + Frontend skeleton (React + Vite + Tailwind + TS + React Router, one page)
- [x] **Checkpoint 2** — Postgres models + Alembic migrations: `users`, `resumes`, `job_descriptions`, `matches`
- [x] **Checkpoint 3** — JWT auth: signup / login / me endpoints
- [x] **Checkpoint 4** — Resume upload + text extraction (PyPDF / python-docx)
- [x] **Checkpoint 5** — Job description input + Gemini match score + missing skills (structured output)
- [x] **Checkpoint 6** — Cover letter generation
- [x] **Checkpoint 7** — Frontend flows wired end-to-end (upload → paste JD → view results)
- [x] **Checkpoint 8** — Deploy: Vercel (frontend) + Render (backend), Neon Postgres (already provisioned since Checkpoint 2)

## V2 — Job discovery

- [ ] **Checkpoint 9** — Job-board clients: RemoteOK + Arbeitnow (no API key required), normalized into a shared `JobListing` schema; `GET /jobs/search?query=` (ephemeral results, not persisted)
- [ ] **Checkpoint 10** — Add Adzuna + USAJobs (API-key providers) behind the same interface; `location` / `date_posted` filters on `GET /jobs/search`. Greenhouse/Lever demoted to not-built — see "Notes" below
- [ ] **Checkpoint 11** — Migration: extend `job_descriptions` with `url`, `location`, `external_id`, `posted_at`; `POST /jobs/save` persists a search result for the current user (409 on duplicate save)
- [ ] **Checkpoint 12** — `GET /jobs/saved` (list current user's saved jobs) + `DELETE /jobs/saved/{id}` (unsave)
- [ ] **Checkpoint 13** — Frontend: `JobSearch` page (search form + results, Save + "Match against my resume") and `SavedJobs` page (list + remove), wired to the Checkpoint 9-12 endpoints

## V3 — Tracking & automation

**Priority-company alerts:**

- [ ] **Checkpoint 14** — `tracked_companies` table + ATS adapters (Greenhouse, Lever, Ashby — all have free, unauthenticated per-company job-board APIs); `fetch_postings(provider, board_token)` reuses V2's `JobListing` schema. `POST /companies/track` (verifies the board resolves before saving), `GET /companies/tracked`, `DELETE /companies/tracked/{id}`
- [ ] **Checkpoint 15** — `company_postings` table (a "seen postings" ledger per tracked company) + polling logic that diffs each fetch against it, returning only postings never seen before for that company
- [ ] **Checkpoint 16** — Score each newly-seen posting against the user's most recent resume (reuses the existing Gemini match-scoring service, unchanged); `alerts` table stores only results at/above a relevance threshold (e.g. score ≥ 60), so low-relevance postings don't spam the user
- [ ] **Checkpoint 17** — Scheduled polling + email delivery: a shared-secret-guarded `POST /internal/poll-companies` (not a user-JWT route — triggered by infrastructure, not a logged-in user) runs Checkpoints 15-16 across every tracked company for every user; triggered by a scheduled GitHub Actions workflow, since Render's free tier sleeps when idle and an in-process scheduler can't be trusted to fire — the cron *request itself* wakes the service. Emails via a free-tier transactional provider (Resend/SendGrid) or Gmail SMTP
- [ ] **Checkpoint 18** — Frontend: "Priority Companies" page (add/remove tracked companies — company name + ATS provider + board token/slug) and an "Alerts" page (new-posting alerts with score/company/link, mark-as-read)

**Application tracking & analytics:**

- [ ] **Checkpoint 19** — `applications` table + status tracking (`saved` / `applied` / `interviewing` / `rejected` / `offer`); endpoints to create/update/list; "Save" actions elsewhere in the app create an application row
- [ ] **Checkpoint 20** — Analytics dashboard: match scores over time, application funnel (counts per status)

- [ ] *Optional stretch, unordered:* Playwright auto-apply — own accounts only, manual confirm-before-submit, heavily rate-limited. Not a requirement for a strong resume entry; only build if the earlier checkpoints are solid and there's time left.

## Notes

- Embeddings-based semantic matching is intentionally deferred past V1 — see ARCHITECTURE.md. Add only if keyword/LLM-only matching proves too shallow in practice.
- Redis caching: not planned unless a specific performance problem shows up. Applies to V2 job search too — no result caching layer until a real latency/rate-limit problem shows up.
- Greenhouse/Lever are **not** part of the V2 checkpoints above: both are per-company job-board APIs (you query one specific employer's board via that employer's board token), not a global keyword-search API like the other four. They don't fit "search jobs by keyword across the market," which is what V2 is actually building. That same per-company shape is exactly what V3's priority-company alerts need instead — see Checkpoint 14, which adds Greenhouse/Lever back (plus Ashby) for that reason.
- V3's priority-company alerts intentionally don't attempt generic company-career-page HTML scraping. Most tech-company career pages are actually powered by one of a handful of ATS platforms with free public per-company APIs (Greenhouse, Lever, Ashby chosen first; Workday/SmartRecruiters are candidates for later — Workday in particular doesn't have a simple universal public JSON endpoint per tenant, so it's deferred). A company on none of these would show as "not trackable" rather than the app falling back to fragile, ToS-uncertain HTML scraping.

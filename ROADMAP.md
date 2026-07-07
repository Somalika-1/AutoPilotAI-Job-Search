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
- [ ] **Checkpoint 7** — Frontend flows wired end-to-end (upload → paste JD → view results)
- [ ] **Checkpoint 8** — Deploy: Vercel (frontend) + Railway/Render (backend + Postgres)

## V2 — Job discovery

- [ ] Integrate legitimate job-board APIs: Adzuna, RemoteOK, Arbeitnow, USAJobs, Greenhouse/Lever
- [ ] Filter by date posted / location
- [ ] Save jobs to DB, list saved jobs per user

## V3 — Tracking & automation

- [ ] Application status tracking (`applications` table: saved / applied / interviewing / rejected / offer)
- [ ] Analytics dashboard (match scores over time, application funnel)
- [ ] *Optional stretch:* Playwright auto-apply — own accounts only, manual confirm-before-submit, heavily rate-limited. Not a requirement for a strong resume entry; only build if the earlier checkpoints are solid and there's time left.

## Notes

- Embeddings-based semantic matching is intentionally deferred past V1 — see ARCHITECTURE.md. Add only if keyword/LLM-only matching proves too shallow in practice.
- Redis caching: not planned unless a specific performance problem shows up.

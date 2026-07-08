# AutoPilotAI — Autonomous Job Search & Resume Intelligence Platform



> **Status: V1 complete and live — full stack (auth, DB, resume upload, AI matching, cover letters, frontend) deployed to Vercel + Render.** V2 (job discovery) is next, checkpoints 9-13. See [ROADMAP.md](./ROADMAP.md) for live progress.
>
> Live: [frontend](https://auto-pilot-ai-job-search.vercel.app) · backend on Render

## Docs

| Doc | What's in it |
|---|---|
| [HLD.md](./HLD.md) | One-page system diagram — components and how they talk to each other |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Folder structure, DB schema, design principles, deployment plan |
| [FLOWS.md](./FLOWS.md) | User flows + technical data flow, step by step, per feature |
| [API.md](./API.md) | Endpoint reference — request/response shape for what's actually built |
| [ROADMAP.md](./ROADMAP.md) | Versioned checklist of checkpoints, what's done vs. planned |
| [V1.md](./V1.md) | V1 implementation log — what was built, why, how, per checkpoint (the detailed build history) |
| [V2.md](./V2.md) | V2 implementation log — same format as V1.md, filled in as Checkpoints 9-13 are built |
| [V3.md](./V3.md) | V3 implementation log — same format, filled in as Checkpoints 14-20 are built |
| [INTERVIEW_PREP.md](./INTERVIEW_PREP.md) | Rehearsal script for talking about this project — pitch, tech stack reasoning, alternatives considered, real challenges faced, curveball Q&A |

An AI-powered career assistant that analyzes resumes against job descriptions using LLM-based matching, surfaces missing skills, and drafts tailored cover letters. Built as a portfolio project to go beyond "used ChatGPT" and demonstrate real product + API integration engineering.

## What it does (V1 scope)

- Upload a resume (PDF/DOCX) and extract its text
- Paste in a job description
- Get an AI-generated match score, missing skills, and strengths (structured JSON output, not free text)
- Generate a tailored cover letter from the resume + job description
- Basic account system (signup/login) so results are saved per user

Later versions add legitimate job-board API search, saved jobs, application tracking, and an analytics dashboard. See [ROADMAP.md](./ROADMAP.md).

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React (Vite) + TypeScript + Tailwind CSS + React Router | Backend is a separate FastAPI API, so the frontend is a pure SPA — no need for Next.js's SSR/server-actions/API-routes, which would go unused here |
| Backend | FastAPI (Python) | Clean API structure, strongest ecosystem for AI integration |
| Database | PostgreSQL | Relational data (users, resumes, jobs, matches) fits well; battle-tested |
| Auth | Hand-rolled JWT (FastAPI + bcrypt + PyJWT) | Demonstrates understanding of auth mechanics, not just wiring a SaaS |
| AI | Google Gemini API (`gemini-2.0-flash`), structured outputs | Resume analysis, JD matching, cover letter generation. Switched from OpenAI mid-Checkpoint-5/6 — see V1.md — since Gemini's free tier needs no payment method, and its SDK supports the same Pydantic-schema structured-output pattern |
| File processing | PyPDF, python-docx | Resume text extraction |
| Job sourcing (V2+) | Public job-board APIs (RemoteOK, Arbeitnow, Adzuna, USAJobs) | Legal, stable, no ToS/scraping risk — see ROADMAP.md for why Greenhouse/Lever were dropped from this list |
| Deployment | Vercel (frontend), Render (backend, Docker), Neon (Postgres) | Free tiers, simple CI, already live |

**Deliberately excluded for now:** local LLMs, vector databases, LangChain/agent frameworks, microservices, Docker-for-everything. These add real value later but would burn weeks of setup before a single feature works. See `ARCHITECTURE.md` for the reasoning.

## Project structure

```
autopilot-ai/
├── backend/            # FastAPI app (see ARCHITECTURE.md for internal layout)
├── frontend/           # React (Vite) app
├── README.md
├── HLD.md              # one-page system diagram
├── ARCHITECTURE.md     # system design, DB schema, folder layout
├── FLOWS.md            # user flows + data flow, step by step
├── API.md              # endpoint reference
├── ROADMAP.md          # versioned checklist / review checkpoints
├── V1.md               # V1 implementation log (what/why/how per checkpoint)
├── V2.md               # V2 implementation log (starts filling in at Checkpoint 9)
├── V3.md               # V3 implementation log (starts filling in at Checkpoint 14)
└── .env.example
```

## Local setup

Full stack is wired end-to-end and deployed as of Checkpoint 8: sign up/log in, upload a resume, paste a job description, get an AI match score + missing skills, generate a cover letter — all through the actual UI, not just `curl`. See [V1.md](./V1.md) for exactly what's implemented, and [API.md](./API.md) for the endpoint contracts. V2 (job discovery, Checkpoints 9-13) is next — see [ROADMAP.md](./ROADMAP.md).

```
# backend
cd backend
python -m venv venv
./venv/Scripts/activate   # or source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp ../.env.example .env   # then fill in real values
uvicorn app.main:app --reload

# frontend (separate terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

You'll need real `DATABASE_URL` (Neon), `JWT_SECRET`, and `GEMINI_API_KEY` values in `backend/.env` — see `.env.example` and V1.md's Checkpoints 2/3/5 for how to get each one.

## Why this project

Most "AI project" resume entries are a ChatGPT wrapper with no real engineering behind them. AutoPilotAI is scoped to be honest about that risk and counter it: real auth, a real relational schema, structured (not free-text) LLM outputs, and a job-sourcing strategy that doesn't fall over the first time a site changes its HTML or bans the scraper's IP.

Resume blurb (target, once V1–V3 are complete):

> **AutoPilotAI – Autonomous Job Search & Resume Intelligence Platform**
> Built an AI-powered career assistant that analyzes resumes and job descriptions using LLM-based semantic matching. Automated job discovery, resume customization, and application tracking workflows. Integrated browser automation for reducing manual application effort.

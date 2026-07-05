# AutoPilotAI — Autonomous Job Search & Resume Intelligence Platform



> **Status: V1 in progress — Checkpoint 3 done (auth), Checkpoint 4 (resume upload) next**. See [ROADMAP.md](./ROADMAP.md) for live progress.

## Docs

| Doc | What's in it |
|---|---|
| [HLD.md](./HLD.md) | One-page system diagram — components and how they talk to each other |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Folder structure, DB schema, design principles, deployment plan |
| [FLOWS.md](./FLOWS.md) | User flows + technical data flow, step by step, per feature |
| [API.md](./API.md) | Endpoint reference — request/response shape for what's actually built |
| [ROADMAP.md](./ROADMAP.md) | Versioned checklist of checkpoints, what's done vs. planned |
| [V1.md](./V1.md) | Implementation log — what was built, why, how, per checkpoint (the detailed build history) |

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
| AI | OpenAI API (`gpt-4o-mini` / `gpt-4.1-mini`), structured outputs | Resume analysis, JD matching, cover letter generation |
| File processing | PyPDF, python-docx | Resume text extraction |
| Job sourcing (V2+) | Public job-board APIs (Adzuna, RemoteOK, Arbeitnow, USAJobs, Greenhouse/Lever) | Legal, stable, no ToS/scraping risk |
| Deployment | Vercel (frontend static build), Railway/Render (backend + Postgres) | Free/cheap tiers, simple CI |

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
├── V1.md               # implementation log (what/why/how per checkpoint)
└── .env.example
```

## Local setup

Backend has a working DB (Postgres/Neon) and JWT auth as of Checkpoint 3; resume upload/AI matching/cover letters aren't built yet — see [V1.md](./V1.md) for exactly what's implemented so far, and [API.md](./API.md) for the endpoints that exist right now.

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

This will be extended with DB migrations, auth, etc. as later checkpoints land.

## Why this project

Most "AI project" resume entries are a ChatGPT wrapper with no real engineering behind them. AutoPilotAI is scoped to be honest about that risk and counter it: real auth, a real relational schema, structured (not free-text) LLM outputs, and a job-sourcing strategy that doesn't fall over the first time a site changes its HTML or bans the scraper's IP.

Resume blurb (target, once V1–V3 are complete):

> **AutoPilotAI – Autonomous Job Search & Resume Intelligence Platform**
> Built an AI-powered career assistant that analyzes resumes and job descriptions using LLM-based semantic matching. Automated job discovery, resume customization, and application tracking workflows. Integrated browser automation for reducing manual application effort.

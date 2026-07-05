# AutoPilotAI — Autonomous Job Search & Resume Intelligence Platform

> **Status: V1 in progress — Checkpoint 0 (docs & repo scaffolding)**. See [ROADMAP.md](./ROADMAP.md) for live progress.

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
| Frontend | Next.js + TypeScript + Tailwind CSS | Modern, recruiter-recognizable stack; fast UI iteration |
| Backend | FastAPI (Python) | Clean API structure, strongest ecosystem for AI integration |
| Database | PostgreSQL | Relational data (users, resumes, jobs, matches) fits well; battle-tested |
| Auth | Hand-rolled JWT (FastAPI + passlib + python-jose) | Demonstrates understanding of auth mechanics, not just wiring a SaaS |
| AI | OpenAI API (`gpt-4o-mini` / `gpt-4.1-mini`), structured outputs | Resume analysis, JD matching, cover letter generation |
| File processing | PyPDF, python-docx | Resume text extraction |
| Job sourcing (V2+) | Public job-board APIs (Adzuna, RemoteOK, Arbeitnow, USAJobs, Greenhouse/Lever) | Legal, stable, no ToS/scraping risk |
| Deployment | Vercel (frontend), Railway/Render (backend + Postgres) | Free/cheap tiers, simple CI |

**Deliberately excluded for now:** local LLMs, vector databases, LangChain/agent frameworks, microservices, Docker-for-everything. These add real value later but would burn weeks of setup before a single feature works. See `ARCHITECTURE.md` for the reasoning.

## Project structure

```
autopilot-ai/
├── backend/            # FastAPI app (see ARCHITECTURE.md for internal layout)
├── frontend/           # Next.js app
├── README.md
├── ARCHITECTURE.md     # system design, DB schema, request flow
├── ROADMAP.md          # versioned checklist / review checkpoints
└── .env.example
```

## Local setup

Not yet applicable — backend/frontend scaffolding lands in Checkpoint 1. This section will be filled in with real run instructions (`venv` setup, `npm install`, env vars, `alembic upgrade`, etc.) as each piece is built.

## Why this project

Most "AI project" resume entries are a ChatGPT wrapper with no real engineering behind them. AutoPilotAI is scoped to be honest about that risk and counter it: real auth, a real relational schema, structured (not free-text) LLM outputs, and a job-sourcing strategy that doesn't fall over the first time a site changes its HTML or bans the scraper's IP.

Resume blurb (target, once V1–V3 are complete):

> **AutoPilotAI – Autonomous Job Search & Resume Intelligence Platform**
> Built an AI-powered career assistant that analyzes resumes and job descriptions using LLM-based semantic matching. Automated job discovery, resume customization, and application tracking workflows. Integrated browser automation for reducing manual application effort.

# LPU Campus Assistant

Two retrieval-augmented chat assistants for Lovely Professional University:

- **University Help Desk** — attendance, exams, fees, hostels, scholarships, library, IT services.
- **Placement Assistant** — placement policy, eligibility rules, drives and deadlines, with tool-calling
  against the signed-in student's own record (CGPA, backlogs, offers).

Both answer only from a set of official documents, cite the passage they used, and hand the
question to the right university department when they can't find a reliable answer — including a
dedicated route to counselling and the national mental-health helpline for sensitive messages.
Answers work in English, Hindi and Punjabi.

This repository is the implementation of Projects 5 and 3 from `project_selection_handoff.pdf`:
one shared RAG core, reused across both assistants, plus each project's own data layer.

```
┌─────────────────────┐        ┌──────────────────────────┐
│  React frontend      │  /api  │  FastAPI backend          │
│  (Vite, TypeScript)   │──────▶│  hybrid retrieval (dense +│
│  chat UI, placement   │       │  BM25) → LLM or extractive│
│  dashboard, admin     │       │  → escalation routing      │
└─────────────────────┘        └──────────┬───────────────┘
                                            │
                             ┌──────────────┼───────────────┐
                             ▼              ▼               ▼
                        Chroma vector   SQLite (users,   Config: assistants,
                        store (chunks)  drives, logs)    departments, prompts
```

## Quick start (Docker)

```bash
docker compose up --build
```

Then open <http://localhost:8080>. The backend seeds demo students and placement drives on
first run and indexes the sample documents in `backend/data/docs/`. Without an `LLM_API_KEY` the
assistants run in **extractive mode**: instead of a generated sentence, they show the exact
passages that answer the question. This is intentional — the app is fully functional and honest
about its limits with zero external dependencies. Add a key (see below) for generated,
conversational answers.

Demo accounts (all share one password, `campus@123`): `DEMO001`–`DEMO012` as students, `admin` as
the placement administrator.

## Quick start (without Docker)

```bash
# Backend
cd backend
pip install -e ".[ml,dev]"
cp .env.example .env          # already present in this repo with safe defaults
python -m app.cli.seed
python -m app.cli.ingest
uvicorn app.main:app --reload --port 8000

# Frontend, in a second terminal
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. `EMBEDDING_PROVIDER=sentence-transformers` (the default) downloads a
~470 MB multilingual model on first run; set `EMBEDDING_PROVIDER=hash` in `backend/.env` for a
fast, fully offline keyword-based embedder (used throughout this project's own test suite).

## Adding a language model

Set three variables in `backend/.env` — any OpenAI-compatible `/chat/completions` endpoint works:

```bash
# Gemini, free tier
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=your-google-ai-studio-key

# Groq, free tier, very fast
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=your-groq-key

# Ollama, fully local
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.1
LLM_API_KEY=ollama
```

Restart the backend. `/api/health` reports whether a model is configured.

## Where the data lives, and how to replace it

- **`backend/data/docs/university/`** and **`backend/data/docs/placement/`** — Markdown, plain
  text, and PDF source documents. Add `effective_date` and `department` to a Markdown file's
  front matter (or a `<file>.yaml` sidecar next to a PDF) so answers can cite the right notice and
  prefer the newer one when two conflict. Every sample file in this repo is placeholder content —
  replace it with LPU's real policies before using this for real students, and delete the
  `sample: true` line once you do.
- **`backend/data/seed/students.csv`** and **`drives.csv`** — demo student records and placement
  drives. Drive dates are stored as day-offsets from the seed date so the demo never looks stale;
  point `DATABASE_URL` at a real database and stop calling `app.cli.seed` once you have live data.
- Re-index after editing documents: `python -m app.cli.ingest` (only changed files are
  re-embedded) or `python -m app.cli.ingest --rebuild` (from admin, "Rebuild entire index"). The
  admin page (sign in as `admin`) also has a "Sync changed documents" button and shows recent
  escalations, which is the fastest way to find gaps in the documents.

No connection to a live university database is needed or attempted; see Section 5 of the handoff
document for the reasoning this project follows.

## Evaluation

```bash
cd backend
python -m app.cli.evaluate            # both assistants, ~65 hand-written questions
python -m app.cli.calibrate           # suggests a retrieval threshold for your embedding model
```

`data/eval/university.jsonl` and `placement.jsonl` hold the question sets: expected source
documents (for retrieval hit-rate), required facts in the answer (for answer accuracy), and
questions that should escalate rather than be answered (for escalation precision/recall). The
report lands in `backend/var/eval/` and lists every question the run got wrong, ready to route back
into scope for a real project write-up alongside the actual quantitative numbers.

## Project layout

```
backend/
  app/
    api/            FastAPI routes and request-scoped dependencies
    core/            security (hashing, JWT), rate limiting, error types
    db/               SQLAlchemy models, session, CSV seeding
    rag/              loaders → chunking → embeddings → vector store → hybrid retriever → ingest
    llm/               provider-neutral chat client (any OpenAI-compatible endpoint)
    services/         chat orchestration, placement rules, tool-calling, escalation routing, i18n
    schemas/          Pydantic request/response models
    prompts/          system prompt templates (Markdown, not embedded in code)
    evaluation/       the eval harness used by app/cli/evaluate.py
    cli/               seed / ingest / evaluate / calibrate entry points
  data/
    docs/             source documents, one folder per assistant domain
    config/           assistants.yaml, departments.yaml (+ escalation rules), messages.yaml
    seed/             demo students.csv / drives.csv
    eval/             hand-written evaluation question sets
  tests/              96 pytest tests: unit (chunking, retrieval, rules, security) + API integration
frontend/
  src/
    api/               fetch wrapper + typed endpoint calls
    components/       chat/, placement/, layout/, ui/ (small, single-purpose pieces)
    context/           auth and language state
    pages/             one file per route
  e2e/                Playwright smoke tests against the real backend + built frontend
```

## Design notes

The palette and type choices are explained in [`docs/design-notes.md`](docs/design-notes.md) —
short version: the colors come directly from the LPU wordmark rather than a generic template, and
the three-script type stack (Latin / Devanagari / Gurmukhi) was picked for legibility, not looks.

## Tests

```bash
cd backend  && PYTHONPATH=. pytest --cov=app          # 96 tests
cd frontend && npm test                                # 26 unit tests (Vitest)
cd frontend && npx playwright install chromium          # once
cd frontend && npm run test:e2e                          # 6 end-to-end tests, real browser
```

## Known limitations

- The sample documents are placeholders (marked `sample: true`) and must be replaced with LPU's
  actual, current policies before this is used by real students — see the licence note in
  `backend/data/docs/placement/placement_policy_2026.pdf` itself.
- Cross-lingual retrieval (asking in Hindi/Punjabi about English-only documents) needs the
  `sentence-transformers` embedding provider; the offline `hash` provider used in CI is keyword-only
  and won't bridge scripts.
- The in-process rate limiter and SQLite are sized for a single instance; move to Postgres and a
  shared rate-limit store (e.g. Redis) before scaling beyond one backend process.

# Tradejournal

A trading journal and analytics platform. Next.js frontend, FastAPI backend, PostgreSQL via Prisma (shared schema between Node and Python).

## Stack

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts
- **Backend:** FastAPI, Prisma Client Python, JWT auth
- **Database:** PostgreSQL 16
- **Schema:** Single `prisma/schema.prisma` consumed by both Prisma Client Python (backend) and Prisma Client JS (frontend, optional)

## Local development

### 1. Postgres

```bash
docker compose up -d
```

### 2. Backend

```bash
cd trading_journal_backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # adjust secrets
prisma db push          # create tables
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd trading_journal_frontend
npm install
cp .env.example .env.local
npm run dev
```

App: http://localhost:3000

## Project layout

```
backend/
  app/
    api/         # FastAPI routers
    core/        # config, security, deps
    schemas/     # Pydantic request/response models
    db.py        # Prisma client singleton
    main.py
  prisma/
    schema.prisma
frontend/
  src/
    app/         # App Router routes
    components/  # UI components
    lib/         # api client, auth context, helpers
```

## Status

- [x] Auth (register, login, JWT)
- [x] Dashboard analytics (PNL, profit factor, win rate, drawdown, calendar)
- [x] Trade CRUD
- [x] Strategies CRUD
- [x] Daily journal entries
- [ ] Broker connections (stubbed)
- [ ] Copy trading (stubbed)

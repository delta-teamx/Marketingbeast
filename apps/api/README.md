# Presence API

FastAPI backend (Tier A — official-API-first). Async SQLAlchemy 2.x + Alembic on
Supabase Postgres, Supabase Auth for identity, Celery + Redis for jobs.

## Setup

```bash
uv sync                       # install deps (creates .venv)
cp .env.example .env          # then fill FERNET_KEY etc.
uv run alembic upgrade head   # apply migrations
uv run uvicorn app.main:app --reload --port 8000
```

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Worker

```bash
uv run celery -A app.worker.celery_app.celery_app worker --loglevel=info
```

## Tests

```bash
uv run pytest
```

`test_health` and `test_auth_smoke` run without a database. The DB-backed
provisioning tests connect to `DATABASE_URL` and skip if no database is reachable.

## Layout

- `app/core` — config, logging, Supabase JWT validation
- `app/db` — engine/session + declarative base
- `app/models` — Organization, Membership, Brand, SocialAccount (stub)
- `app/api` — routers + dependencies (`get_current_user`, `require_org_role`)
- `app/services/llm` — `LLMProvider` interface + mock + Claude stub
- `app/services/crypto.py` — Fernet token encryption (used in Phase 1)
- `app/worker` — Celery app + example task
- `alembic` — migrations (revision 0001 enables pgvector + core tables)

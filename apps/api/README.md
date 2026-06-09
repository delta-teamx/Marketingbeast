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
- `app/models` — Organization, Membership, Brand, SocialAccount, Content(Item/Target)
- `app/api` — routers + dependencies (`get_current_user`, `require_org_role`,
  `require_brand_access`); content / social-accounts / Meta integration routes
- `app/services/meta` — Meta Graph client (`mock` + `live` adapters)
- `app/services/publishing.py` — create / schedule / publish pipeline (idempotent)
- `app/services/connections.py`, `oauth_state.py` — connect flow + signed state
- `app/services/llm` — `LLMProvider` interface + mock + Claude stub
- `app/services/crypto.py` — Fernet token encryption
- `app/worker` — Celery app, example task, and the `publish_due` beat poller
- `alembic` — migrations (0001 pgvector + core tables, 0002 content publishing)

## Meta modes

`META_MODE=mock` (default) uses an in-process fake — no credentials, used by the
test suite and local dev. `META_MODE=live` hits the real Graph API and requires
`META_APP_ID` / `META_APP_SECRET` and an approved Meta app.

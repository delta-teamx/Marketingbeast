# Presence

An AI marketing employee for small businesses and agencies. Enter a business URL
and Presence audits your social presence, then generates, schedules, publishes,
and reports on content across Facebook and Instagram — with near-zero effort.

> **Status: Phase 0 (Foundations).** This repo currently contains the runnable
> skeleton — auth, multi-tenant data model, background-job wiring, CI, and smoke
> tests. Feature phases (publishing, audit, content engine, …) build on top.

## Architecture: two tiers with a hard boundary

**Tier A — Safe Core (this codebase).** Everything server-side uses Meta's
**official** Graph/Marketing APIs via OAuth and is fully ToS-compliant:
publishing & scheduling, insights, comments/DMs, ads, multi-account management.
This is ~80% of the product.

**Tier B — Local Automation Layer (separate, later, optional).** A
user-operated browser extension for posting into Facebook groups, running in the
user's own session with non-overridable human-pacing guardrails. **It never runs
on our servers and never receives Facebook credentials.** Tier A never depends on
Tier B.

## Stack

| Area | Choice |
| --- | --- |
| API | FastAPI (async), SQLAlchemy 2.x + Alembic, Pydantic v2, httpx — deploys to **Render** |
| Jobs | Celery + Redis |
| DB | **Supabase** Postgres + `pgvector` |
| Auth | **Supabase Auth** (the API validates Supabase JWTs; we store no passwords) |
| Web | Next.js (App Router) + TS, Tailwind v4, TanStack Query, Zustand — deploys to **Netlify** |
| AI | `LLMProvider` interface over Anthropic Claude (mock provider for dev) |

See [`apps/api`](apps/api/README.md) and [`apps/web`](apps/web/README.md) for
per-app details, and [`supabase`](supabase/README.md) for the local stack.

## Repo layout

```
apps/api        FastAPI backend (Tier A)
apps/web        Next.js web app
packages/shared Shared TS types (API contract)
supabase        Local Supabase stack config
.github         CI (lint, migrate, test for both apps)
```

## Quick start

Prerequisites: Python 3.11+, `uv`, Node 20+, `pnpm`, Docker, and the Supabase CLI.

```bash
# 1. Install
make install                       # uv sync (api) + pnpm install (web)

# 2. Local infra (Postgres+pgvector+Auth via Supabase, Redis via Docker)
supabase start                     # copy the printed JWT secret + anon key into .env
docker compose up -d redis

# 3. Configure env
cp .env.example .env               # fill SUPABASE_JWT_SECRET, FERNET_KEY, ...
cp apps/web/.env.example apps/web/.env.local

# 4. Migrate + run
make migrate                       # alembic upgrade head (enables pgvector + tables)
make api                           # FastAPI on :8000
make web                           # Next.js on :3000
make worker                        # Celery worker (separate terminal)
```

Generate a Fernet key for `FERNET_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Tests (the Phase 0 smoke)

```bash
make test            # backend (pytest) + web (vitest)
```

- **API:** `/health` returns ok; protected routes 401 without a token and accept
  a valid Supabase JWT; the first `/api/auth/me` provisions a personal org which
  is then listable. (DB-backed tests skip if no database is reachable.)
- **Web:** Vitest renders the landing hero + login form and asserts the API
  wrapper attaches the bearer token; Playwright loads `/` and `/login`.

CI (`.github/workflows/ci.yml`) runs lint + migrations + tests for both apps on
every push, against a `pgvector` Postgres and Redis.

## Data model (Phase 0)

- **Organization** — the multi-tenant boundary (a business or agency).
- **Membership** — links a Supabase `auth.users` id to an Organization with a
  role (`owner` / `admin` / `member`). We keep no local users table.
- **Brand** — a managed business within an Organization (voice profile, vertical).
- **SocialAccount** *(stub)* — a connected FB Page / IG account; OAuth tokens are
  encrypted at rest (Fernet) and never logged. The connect flow lands in Phase 1.

## Meta API scopes (Phase 1 — documented now for App Review prep)

Phase 1 (connect a FB Page + IG account, publish, read insights, comments/DMs)
will request:

- **Pages:** `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
  `pages_manage_metadata`, `pages_read_user_content`, `pages_manage_engagement`
- **Instagram:** `instagram_basic`, `instagram_content_publish`,
  `instagram_manage_comments`, `instagram_manage_insights`
- **Insights / business:** `read_insights`, `business_management`
- **Messaging (inbox):** `pages_messaging`, `instagram_manage_messages`
- **Ads (Phase 6):** `ads_management`, `ads_read`

**App Review implications:** Advanced Access requires a Meta **Business** app,
**business verification**, App Review with a screencast per permission, a
published privacy policy, and a data-deletion callback. These are prerequisites
to start before Phase 1 — flag early.

## Roadmap

Phase 0 Foundations *(this)* → 1 Connect & Publish → 2 Flagship Audit →
3 Content Engine → 4 Analytics & Reports → 5 Engagement & Leads → 6 Ads →
7 AI Video → 8 Agency / White-label → 9 Tier B Group Posting → 10 Vertical tuning.

# Presence

An AI marketing employee for small businesses and agencies. Enter a business URL
and Presence audits your social presence, then generates, schedules, publishes,
and reports on content across Facebook and Instagram — with near-zero effort.

> **Status: Phase 1 (Connect & Publish).** On top of the Phase 0 foundation, the
> publishing spine is in: connect a Facebook Page + Instagram account, compose a
> post, schedule it, and auto-publish via the Meta Graph API through a Celery
> queue. A `META_MODE=mock` adapter makes the whole pipeline runnable and tested
> without real Meta credentials. (Audit, content engine, analytics, … come next.)

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

## Connect & Publish (Phase 1)

Tier A publishing runs entirely through Meta's **official** Graph API, behind one
adapter with two modes (`META_MODE`): `mock` (default — an in-process fake, no
creds, used by dev and the test suite) and `live` (the real Graph API).

- **Connect:** `GET /api/integrations/meta/oauth/start` → Facebook login dialog;
  `GET /api/integrations/meta/oauth/callback` exchanges the code (state is signed,
  CSRF-safe) and stores Pages + linked IG accounts as `SocialAccount`s with
  **encrypted tokens**. `POST /api/integrations/meta/connect-mock` connects fake
  accounts in mock mode for dev/tests.
- **Compose & schedule:** `POST /api/content` creates a draft or scheduled item
  targeting one or more connected accounts; `GET /api/content?brand_id=` lists.
- **Publish:** `POST /api/content/{id}/publish` publishes now (inline); scheduled
  items are published by the Celery **beat poller** (`presence.publish_due`) once
  their time arrives.
- **Idempotency:** a target that already has an `external_post_id` is never
  published again — retries and the poller are safe (no double-posting).

The web dashboard ties this together: create a brand, connect accounts, compose,
schedule, and publish.

## Engagement & Leads (Phase 5)

A unified inbox for comments + DMs across FB/IG, with lead detection.

- **Sync:** `POST /api/brands/{id}/inbox/sync` pulls conversations via the Meta
  adapter (mock-first) into `Conversation` + `Message`, idempotently.
- **Lead detection:** an intent scorer (keyword heuristic in mock; LLM few-shot
  in live) flags buyer-intent conversations and scores them; `?leads_only=true`
  surfaces just the leads.
- **AI-drafted replies:** `POST /api/conversations/{id}/draft-reply` suggests a
  reply; the user edits and confirms via `…/reply` (we never blast identical
  auto-replies). Moderate with `…/hide`.
- Models: `Conversation`, `Message` (migration 0008). Web: an "Inbox & leads"
  panel with a conversation list, thread view, draft/send, and hide.

## Analytics & Reports (Phase 4)

Insights flow through the Meta adapter (mock-first) into daily snapshots.

- **Sync:** `POST /api/brands/{id}/insights/sync` ingests per-account insights
  (`MetricSnapshot`); a Celery beat job (`presence.ingest_insights`) does it daily.
- **Dashboard:** `GET /api/brands/{id}/analytics` — followers, growth, reach,
  engagement rate, a time-series, top posts, and per-account breakdown (charted
  with Recharts in the app).
- **Reports:** `POST /api/brands/{id}/reports/generate` (weekly/monthly) with an
  AI summary; `GET /api/reports/{id}/html` is a print-ready, white-label-able page.
- **Competitor tracking:** add competitors and `GET …/competitors/compare` returns
  follower gaps + an AI gap summary.
- Models: `MetricSnapshot`, `Report`, `Competitor` (migration 0007).

## Marketing site & onboarding

The web app's public `/` is a conversion-focused marketing site (hero + clear
CTAs, features, how-it-works, who-it's-for, trust/compliance, pricing, final CTA)
for small businesses and agencies running many FB/IG accounts. New signups flow
into `/onboarding` — a questionnaire (goal, platforms, cadence, budget, audience,
challenge) that creates the brand and an `OnboardingProfile` so the AI can tune
strategy. Endpoint: `POST /api/onboarding` (migration 0006).

## Flagship audit (Phase 2)

The hero feature: enter a brand's website and get a scored Presence audit plus a
running content engine in minutes.

- **Scoring** (`services/audit.py`): deterministic sub-scores (profile
  completeness, platform breadth, posting consistency, engagement, content
  quality) → overall score + **letter grade** (reproducible, not vibes), combined
  with LLM qualitative judgment for the strategy brief + first-week plan.
- **Endpoints:** `POST /api/brands/{id}/audit/run`, `GET /api/brands/{id}/audit`,
  `POST /api/brands/{id}/audit/seed` ("Start running my account" → turns the plan
  into draft posts).
- **Web:** an "Presence audit" panel — grade, per-section bars, strategy brief,
  recommendations, and one-click seeding of the first week.
- Mock LLM mode is deterministic, so the audit runs with no key/network.

## AI Content Engine (Phase 3)

Brand-voice generation that turns one input into a week of content.

- **Generate** (`services/content_engine.py`): `POST /api/content/generate`
  `{brand_id, prompt, count}` → brand-voice draft posts (voice = niche + profile)
  with **hashtags** and a **best-time** hint. Deterministic in mock mode.
- **Best-times:** `GET /api/content/best-times?brand_id=` — rules-based per
  weekday now; upgrade to a learned per-account model once insights exist.
- **Repurpose:** `POST /api/content/{id}/repurpose` → post / reel-script / story
  variants.
- **Approval workflow:** `POST /api/content/{id}/approve` (draft → approved →
  schedule). `ContentItem` gains `approved`, `hashtags`, `suggested_time`
  (migration 0005).
- **Web:** a "Generate content" box plus Approve / Repurpose actions on each item.

## Lead Groups — niche-based Facebook group finder

Detects a brand's niche from its website, then suggests high-potential Facebook
groups to join for leads.

- **Compliance:** Meta deprecated the Groups API, so there's no way to query real
  groups and **group posting is Tier B** (user-operated extension, never
  server-driven). So suggestions are **advisory AI output** — group name, the
  keyword to search on Facebook, an estimated size, relevance + lead-quality
  scores, and a rationale + post angle. The user joins manually.
- **Niche detection** (`services/website.py` + `services/group_finder.py`): fetch
  the site (httpx + stdlib HTML stripper) → LLM classifies niche. `LLM_PROVIDER=mock`
  (default) yields deterministic output so it runs with no key/network.
- **Endpoints:** `POST /api/brands/{id}/niche/detect`,
  `POST /api/group-suggestions/generate`, `GET /api/group-suggestions`,
  `PATCH /api/group-suggestions/{id}` (track/dismiss).
- **Tier B queue (storage only):** `POST/GET /api/automation/group-queue` stores
  posts for the future browser extension to publish locally under the §9 pacing
  guardrails. **The backend never posts to groups.**
- **Web:** a "Lead Groups" panel in the dashboard — find, track, and queue posts.

## Data model

- **Organization** — the multi-tenant boundary (a business or agency).
- **Membership** — links a Supabase `auth.users` id to an Organization with a
  role (`owner` / `admin` / `member`). We keep no local users table.
- **Brand** — a managed business within an Organization (voice profile, vertical).
- **SocialAccount** — a connected FB Page / IG account; OAuth tokens are encrypted
  at rest (Fernet) and never logged.
- **ContentItem / ContentTarget** — a post (draft/scheduled/published) and its
  per-account publish result (external post id, status, error).
- **GroupSuggestion / GroupPostTask** — an AI-suggested Facebook group for lead
  gen, and a queued post for the Tier B extension to publish locally.
- **AuditReport** — a scored Presence audit (grade, sections, strategy brief,
  first-week content plan) for a brand.

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

Phase 0 Foundations ✅ → 1 Connect & Publish ✅ → 2 Flagship Audit ✅ →
3 Content Engine ✅ → 4 Analytics & Reports ✅ → 5 Engagement & Leads ✅ → 6 Ads →
7 AI Video → 8 Agency / White-label → 9 Tier B Group Posting 🚧 → 10 Vertical tuning.

Tier B (the user-operated, paced Facebook **group** posting extension) lives in
[`apps/extension`](apps/extension/README.md) — assisted/confirmed, with hard-coded
§9 guardrails, consuming the group-post queue. The backend never posts to groups.

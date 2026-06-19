# Run the full app locally — Demo mode (no Supabase)

This runs the **whole product**, including the logged-in **dashboard**, with **no
Supabase** and no external API keys. You only need **Docker** (for a local
Postgres), plus Node/pnpm and `uv`.

In demo mode the API uses a single fixed demo user (`AUTH_MODE=dev`) and the web
app skips Supabase auth (`NEXT_PUBLIC_DEMO=1`), so "Sign in" takes you straight
into the dashboard.

> Everything else is already in **mock mode** (Meta, Claude, ads, media, billing),
> so all features work against fake data.

## Prerequisites
- Docker Desktop running
- Node 20+ and `pnpm` (`corepack enable`)
- `uv` (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Terminal 1 — Postgres (one container)
```bash
docker run -d --name presencedb \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=postgres \
  -p 54322:5432 pgvector/pgvector:pg16
```

## Terminal 2 — the API (demo auth, no Supabase)
```bash
cd ~/Marketingbeast/apps/api
uv sync
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres"
export AUTH_MODE=dev
export FERNET_KEY="$(uv run python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
uv run alembic upgrade head
uv run uvicorn app.main:app --port 8000
```

## Terminal 3 — the web app (demo mode)
```bash
cd ~/Marketingbeast
printf 'NEXT_PUBLIC_DEMO=1\nNEXT_PUBLIC_API_BASE_URL=http://localhost:8000\n' > apps/web/.env.local
pnpm install
pnpm --filter @presence/web dev
```

## Use it
1. Open **http://localhost:3000**
2. Click **Get started** (or **Sign in**) → just submit → you're in onboarding/dashboard
3. Create a brand → **"Dev: connect mock accounts"** → explore the tabs:
   Overview/Audit · Content · AI Video · Analytics · Ads · Inbox · Lead Groups · Team
4. Try: **Run audit**, **Generate content**, **Sync insights**, **Launch a campaign**,
   **Generate a reel**, **Sync inbox**, **Find lead groups**, **Upgrade plan**.

## Stop / reset
```bash
docker rm -f presencedb     # stop + delete the demo database
```

Re-run the three terminals to start fresh.

> Note: demo mode is for local exploration only. Production uses real Supabase
> Auth (`AUTH_MODE=supabase`, the default) — see `GO_LIVE.md`.

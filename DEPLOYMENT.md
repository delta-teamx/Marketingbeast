# Deployment status — Netlify + Render + Supabase

This tracks the live hosting setup. **Supabase and Netlify are configured by the
assistant; Render is handled by you.** Mock adapters are on by default, so the
app runs end-to-end before any Meta/Anthropic/Stripe keys are added.

## ✅ Supabase (done) — database + Auth
- Project: **presence-prod** · ref `eurlrgolgntdngyaexqr` · region `us-east-1`
- URL: `https://eurlrgolgntdngyaexqr.supabase.co`
- Schema: all migrations `0001`→`0013` applied; `alembic_version` stamped to
  `0013_webhook_events`, so the API's `alembic upgrade head` is a clean no-op.
- pgvector extension enabled.

## ✅ Netlify (done) — web frontend
- Site: **presence-marketing-app** · `https://presence-marketing-app.netlify.app`
- `netlify.toml` at repo root (base `apps/web`, Next.js plugin, pnpm workspace).
- Build env vars set: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`.

## 🛠 Render (you) — the API (`apps/api`)
Create a **Web Service** from this repo, root dir `apps/api`.
- Build: `pip install uv && uv sync`
- Start: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  (DB schema is already applied; no migration step needed on first boot.)

### Render environment variables
| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres.eurlrgolgntdngyaexqr:[DB_PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres` (Supabase **Session pooler**, IPv4) |
| `SUPABASE_URL` | `https://eurlrgolgntdngyaexqr.supabase.co` |
| `SUPABASE_JWT_SECRET` | from Supabase → Settings → API → **JWT Secret** |
| `FERNET_KEY` | generate once and keep stable (token encryption) |
| `API_ENV` | `production` |
| `API_CORS_ORIGINS` | `https://presence-marketing-app.netlify.app` |
| `WEB_APP_URL` | `https://presence-marketing-app.netlify.app` |
| `LLM_PROVIDER` | `mock` (switch to `anthropic` + `ANTHROPIC_API_KEY` later) |
| `META_MODE` | `mock` (switch to `live` after Meta App Review) |
| `BILLING_PROVIDER` | `mock` (switch to `stripe` + keys later) |
| `MEDIA_PROVIDER` | `mock` |

> Background jobs (scheduled publishing, insights/inbox polling) run via Celery
> beat + a worker against `REDIS_URL`. The web API boots fine without them; add a
> Render Redis instance + a worker service when you want scheduling live.

## 🔧 Remaining manual steps
1. **Netlify → link repo**: Site → Build & deploy → Link repository →
   `delta-teamx/Marketingbeast`. Pick the production branch (merge PR #1 to
   `main`, or set the branch to `claude/wonderful-tesla-2cylma`). First deploy
   then builds automatically.
2. **Netlify → add `NEXT_PUBLIC_API_BASE_URL`** = your Render API URL once it's
   live (e.g. `https://presence-api.onrender.com`), then redeploy.
3. **Supabase → Auth → URL Configuration**: set Site URL to
   `https://presence-marketing-app.netlify.app` and add it to Redirect URLs.
4. **Supabase → Auth → Providers → Email**: confirm email/password is enabled;
   for production sign-ups configure SMTP (or disable email confirmation for a
   smoother demo).

After 1–3 the full product is live in mock mode. Then wire real providers per
`GO_LIVE.md`.

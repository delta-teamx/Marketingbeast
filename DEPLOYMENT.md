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
Deploy via **Blueprint**, not a hand-made service: in Render, New → **Blueprint**,
connect this repo, and point at **`apps/api/render.yaml`**. The blueprint creates
everything in one shot:
- `presence-api` — the web service (Docker; `preDeployCommand` runs
  `alembic upgrade head` each deploy).
- `presence-worker` — the Celery worker (runs queued/scheduled tasks).
- `presence-beat` — the Celery **beat scheduler** (enqueues due work: scheduled
  publishing, daily insights, render polling). Without this nothing scheduled fires.
- `presence-redis` — the Celery broker/backend.

The three app services share one env-var group (`presence-shared`) so the worker
never silently runs in mock while the API is live.

### Render environment variables (set on the `presence-shared` group)
The blueprint declares these as `sync: false` (secrets) — fill them in once in the
Render dashboard after the first apply:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres.eurlrgolgntdngyaexqr:[DB_PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres` (Supabase **Session pooler**, IPv4) |
| `SUPABASE_URL` | `https://eurlrgolgntdngyaexqr.supabase.co` |
| `SUPABASE_JWT_SECRET` | from Supabase → Settings → API → **JWT Secret** |
| `FERNET_KEY` | generate once and keep stable (token encryption) |
| `WEB_APP_URL` | `https://presence-marketing-app.netlify.app` |
| `API_CORS_ORIGINS` | `https://presence-marketing-app.netlify.app` (on the `presence-api` service) |

Provider modes (`LLM_PROVIDER`, `META_MODE`, `BILLING_PROVIDER`, `MEDIA_PROVIDER`)
default to `mock` in the blueprint; flip them to live per `GO_LIVE.md` once the
corresponding keys (and Meta App Review) are in place. `API_ENV` is `production`,
so the API refuses to boot if `SUPABASE_JWT_SECRET` is still the dev default or
`FERNET_KEY` is empty — set both before the first deploy.

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

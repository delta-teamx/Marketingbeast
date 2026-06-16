# Presence — Go-Live Runbook

The product is built and tested end-to-end in **mock mode**. Going live means
flipping each external provider from mock → live (mostly configuration) and
adding **Stripe billing** (the one piece of new code). This runbook is the
step-by-step.

> Key architecture fact: customers **do not give you an API key**. They click
> "Connect Facebook" and authorize **your** single Meta app via OAuth; you store
> a per-customer access token (encrypted). One app, many customer tokens.

---

## 0. Order of operations (do these in parallel where noted)

1. **Start Meta App Review first** — it's the long pole (1–4 weeks). ‖ parallel
2. Get the **Anthropic** key (minutes).
3. Build + wire **Stripe** billing (code; ~1 day).
4. Provision **Supabase / Render / Netlify** and deploy.
5. Flip env flags to live, smoke-test, launch.

---

## 1. Meta (Facebook / Instagram) — the long pole

**What you create:** ONE Meta *Business* app at <https://developers.facebook.com>.

1. Create app → type **Business**. Note the **App ID** and **App Secret**.
2. Add products: **Facebook Login**, **Instagram Graph API**, **Marketing API**
   (for ads), **Messenger** (for the inbox).
3. Set the OAuth **redirect URI** to your API:
   `https://<api-domain>/api/integrations/meta/oauth/callback`.
4. **Business Verification** — verify your legal business entity (Meta requires
   this for advanced access). Have business documents ready.
5. **App Review** — request advanced access for the scopes we use (see README
   "Meta API scopes"). For each permission you must submit:
   - a **screencast** showing the feature using that permission,
   - a written use-case description,
   - a **published privacy policy URL**,
   - a **data-deletion callback** (URL or instructions).
6. Provide the required URLs (host these on the web app):
   - Privacy Policy: `https://<web-domain>/privacy`
   - Terms: `https://<web-domain>/terms`
   - Data Deletion: `https://<web-domain>/data-deletion` (or a callback endpoint)

**Then flip to live:**
```
META_MODE=live
META_APP_ID=...
META_APP_SECRET=...
META_REDIRECT_URI=https://<api-domain>/api/integrations/meta/oauth/callback
META_GRAPH_VERSION=v21.0
WEB_APP_URL=https://<web-domain>
```
No code change — the OAuth + publish + insights + inbox + ads adapters already
have a `live` path. Test by connecting a real test Page before launch.

**Agencies / many client pages:** each client Page is connected by OAuth (the
agency or the client authorizes once). Business-Manager / system-user flows can
be layered later; the multi-account data model already supports it.

---

## 2. Anthropic (Claude) — your platform key

You hold **one** key; customers never bring their own. Usage is metered to them
via the existing **credit system**.

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-sonnet-4-6        # or the current recommended model
LLM_TEMPERATURE=0.7
```
`ClaudeProvider` plugs into the existing `LLMProvider` interface — all mock AI
(audit, content, replies, ad copy, video scripts) becomes real with no other
change. (The provider's SDK call is the only thing to finish wiring — see
`apps/api/app/services/llm/anthropic.py`.)

---

## 3. Stripe — billing (built; flip to live with keys)

The billing module is **implemented** (`services/stripe_client.py`,
`app/api/routers/billing.py`). In `BILLING_PROVIDER=mock` (default) checkout
applies the upgrade instantly for dev; in `stripe` mode it creates a real
Checkout session and applies the plan when the signed webhook arrives.

- `GET /api/billing/plans` — plan catalog (limits + monthly credits).
- `POST /api/billing/checkout` `{org_id, plan}` — returns a Checkout URL (live)
  or completes instantly (mock); grants the plan's monthly credits.
- `POST /api/billing/webhook` — verifies the Stripe signature and, on
  `checkout.session.completed` / `customer.subscription.updated`, sets `org.plan`,
  stores `stripe_customer_id` / `stripe_subscription_id`, and grants credits.

To go live:
1. `pip install stripe` (live client imports it lazily).
2. Create Stripe **Products/Prices** for Growth and Agency.
3. Add a webhook endpoint in Stripe pointing at
   `https://<api-domain>/api/billing/webhook`.
4. Env:
```
BILLING_PROVIDER=stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_GROWTH=price_...
STRIPE_PRICE_AGENCY=price_...
BILLING_SUCCESS_URL=https://<web-domain>/dashboard?upgraded=1
BILLING_CANCEL_URL=https://<web-domain>/pricing
```
Credit grants per plan live in `services/billing.py` (`PLAN_CREDITS`).

---

## 4. Hosting & deployment

**Supabase (DB + Auth + pgvector)**
1. Create a project; enable the `vector` extension (migration `0001` does this).
2. Copy the connection string, JWT secret, anon key, service-role key.
3. Run migrations against it: `alembic upgrade head`.

**Render (API + worker + Redis)** — `apps/api/render.yaml` is the blueprint.
- Web service (uvicorn), Worker (celery), Redis (key-value). `preDeployCommand`
  runs `alembic upgrade head`. Set all secrets (below).

**Netlify (web)** — `apps/web/netlify.toml` is configured for the Next.js plugin.
- Set `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`,
  `NEXT_PUBLIC_API_BASE_URL` (your Render API URL).

---

## 5. Full production env checklist (API)

```
API_ENV=production
API_CORS_ORIGINS=https://<web-domain>
DATABASE_URL=postgresql+asyncpg://...    # Supabase pooled connection
SUPABASE_JWT_SECRET=...
SUPABASE_URL=https://<project>.supabase.co
REDIS_URL=...                            # from Render
FERNET_KEY=...                           # generate once; rotating it invalidates stored tokens
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=...
META_MODE=live
META_APP_ID=...   META_APP_SECRET=...   META_REDIRECT_URI=...
WEB_APP_URL=https://<web-domain>
MEDIA_PROVIDER=...                       # runway/creatify/heygen + MEDIA_API_KEY (or leave mock)
STRIPE_SECRET_KEY=...   STRIPE_WEBHOOK_SECRET=...
```

Generate a Fernet key:
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

---

## 6. Pre-launch smoke test (with real keys)

1. Sign up → onboarding → run an audit on a real URL (real Claude output).
2. Connect a real Facebook Page + IG via OAuth; publish a test post; check it
   appears on the Page.
3. Sync insights, generate a report, run the inbox sync.
4. Subscribe via Stripe (test mode) → confirm `org.plan` flips via webhook.
5. (Optional) AI video render with a real media provider.

---

## 7. Still optional / later

- Object storage (S3-compatible) for uploaded/generated media at scale.
- Email/SMS provider for report delivery + lead alerts.
- Real per-account best-time / engagement ML models (currently rules-based).
- pgvector brand-voice embeddings (extension is enabled; retrieval not yet wired).
- Tier B extension: publish to the Chrome Web Store (it already builds to
  `apps/extension/dist`).

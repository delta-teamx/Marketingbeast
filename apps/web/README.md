# Presence Web

Next.js (App Router) + TypeScript + Tailwind v4. Auth via Supabase Auth;
server state via TanStack Query. Deploys to Netlify.

The frontend reads the API base URL from `NEXT_PUBLIC_API_BASE_URL` (set in the
Netlify site environment); it is inlined at build time, so changing it requires
a rebuild.

## Setup

```bash
pnpm install                  # from the repo root
cp .env.example .env.local    # fill NEXT_PUBLIC_SUPABASE_* and API base URL
pnpm --filter @presence/web dev
```

## Tests

```bash
pnpm --filter @presence/web test       # Vitest unit smoke (hero, auth form, api wrapper)
pnpm --filter @presence/web test:e2e   # Playwright E2E (builds + serves, loads / and /login)
```

`test:e2e` requires a build first (`pnpm --filter @presence/web build`) and a
Chromium download (`pnpm --filter @presence/web exec playwright install chromium`).

## Layout

- `src/app` — routes: `/` (landing), `/login`, `/signup`, `/dashboard` (protected)
- `src/components` — `Hero`, `AuthForm` (kept standalone so they're unit-testable)
- `src/lib/supabase` — browser + server Supabase clients
- `src/lib/api.ts` — fetch wrapper that attaches the Supabase token to API calls
- `src/middleware.ts` — refreshes the auth session per navigation
- `src/providers` — TanStack Query provider

<!-- build: ensure NEXT_PUBLIC_API_BASE_URL is baked into production bundle -->

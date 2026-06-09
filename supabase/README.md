# Supabase (local dev)

Provides Postgres + pgvector + GoTrue auth locally so dev matches production.

## First time

Install the [Supabase CLI](https://supabase.com/docs/guides/local-development),
then from the repo root:

```bash
supabase start          # boots Postgres (54322), Auth/API (54321), Studio (54323)
```

`supabase start` prints your local `anon key`, `service_role key`, and the
`JWT secret`. Copy them into `.env` / `apps/web/.env.local`:

- `SUPABASE_JWT_SECRET` (API) ← the printed JWT secret
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` (web) ← the printed anon key

Then apply the app schema with Alembic:

```bash
cd apps/api && uv run alembic upgrade head
```

## Notes

- App tables live in the `public` schema and are owned by **Alembic**
  (`apps/api/alembic`), not Supabase migrations.
- Supabase owns the `auth` schema (users, sessions). Our `memberships.user_id`
  references `auth.users.id`.
- For a hosted project, set the same env vars from the Supabase dashboard
  (Project Settings → API / Database).

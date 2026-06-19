"use client";

import { createBrowserClient } from "@supabase/ssr";

/** Browser Supabase client. Uses public env vars (safe to ship to the client). */
export function createClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) {
    throw new Error(
      "Supabase is not configured: set NEXT_PUBLIC_SUPABASE_URL and " +
        "NEXT_PUBLIC_SUPABASE_ANON_KEY, or run in demo mode (NEXT_PUBLIC_DEMO=1).",
    );
  }
  return createBrowserClient(url, key);
}

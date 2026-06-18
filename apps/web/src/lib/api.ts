import type { SupabaseClient } from "@supabase/supabase-js";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/**
 * Call the Presence API, attaching the caller's Supabase access token as a
 * bearer credential. The API validates that token (see app/core/security.py).
 *
 * `supabase` may be null in demo mode (NEXT_PUBLIC_DEMO=1), where there is no
 * Supabase project configured — we send no token and the API's dev-auth mode
 * (AUTH_MODE=dev) supplies a fixed demo user.
 */
export async function apiFetch(
  supabase: SupabaseClient | null,
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers);
  if (supabase) {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (session?.access_token) {
      headers.set("Authorization", `Bearer ${session.access_token}`);
    }
  }
  headers.set("Content-Type", "application/json");

  return fetch(`${API_BASE_URL}${path}`, { ...init, headers });
}

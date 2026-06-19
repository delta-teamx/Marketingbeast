"use client";

import { createClient } from "@/lib/supabase/client";

export function SignOutButton() {
  return (
    <button
      onClick={async () => {
        if (process.env.NEXT_PUBLIC_DEMO !== "1") {
          try {
            await createClient().auth.signOut();
          } catch {
            // Ignore logout network errors — we hard-redirect below regardless,
            // which clears the local session and re-renders server components.
          }
        }
        // Hard navigation (not router.push) so the cookie-based server pages
        // re-evaluate auth state and don't serve a cached, still-authed view.
        window.location.assign(
          process.env.NEXT_PUBLIC_DEMO === "1" ? "/" : "/login",
        );
      }}
      className="btn-ghost rounded-lg px-3 py-1.5 text-sm"
    >
      Sign out
    </button>
  );
}

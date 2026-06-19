"use client";

import { useEffect } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/**
 * Fire-and-forget ping to wake the API while the user is on the login/signup
 * screen. The backend runs on a free tier that sleeps after idle, so warming it
 * during sign-in means the dashboard is usually ready by the time they land.
 */
export function ApiPrewarm() {
  useEffect(() => {
    fetch(`${API_BASE_URL}/health`, { method: "GET", cache: "no-store" }).catch(
      () => {
        /* best-effort; ignore failures */
      },
    );
  }, []);
  return null;
}

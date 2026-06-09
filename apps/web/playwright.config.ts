import { defineConfig } from "@playwright/test";

/**
 * E2E smoke. Builds and serves the app, then loads the public pages.
 * Public Supabase env vars use placeholders — the landing and auth pages render
 * without any network call to Supabase.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  use: { baseURL: "http://localhost:3000" },
  webServer: {
    command: "pnpm start",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      NEXT_PUBLIC_SUPABASE_URL: "http://localhost:54321",
      NEXT_PUBLIC_SUPABASE_ANON_KEY: "placeholder-anon-key",
    },
  },
});

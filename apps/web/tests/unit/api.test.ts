import { afterEach, describe, expect, it, vi } from "vitest";
import type { SupabaseClient } from "@supabase/supabase-js";
import { apiFetch } from "@/lib/api";

afterEach(() => vi.restoreAllMocks());

function fakeSupabase(token: string | null): SupabaseClient {
  return {
    auth: {
      getSession: async () => ({
        data: { session: token ? { access_token: token } : null },
      }),
    },
  } as unknown as SupabaseClient;
}

describe("apiFetch", () => {
  it("attaches the Supabase access token as a bearer header", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response("{}"));

    await apiFetch(fakeSupabase("tok-123"), "/api/auth/me");

    const headers = (fetchMock.mock.calls[0][1]?.headers as Headers);
    expect(headers.get("Authorization")).toBe("Bearer tok-123");
  });

  it("omits the Authorization header when there is no session", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response("{}"));

    await apiFetch(fakeSupabase(null), "/api/auth/me");

    const headers = (fetchMock.mock.calls[0][1]?.headers as Headers);
    expect(headers.get("Authorization")).toBeNull();
  });
});

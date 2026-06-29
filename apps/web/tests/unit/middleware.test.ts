import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// The middleware runs as a Netlify Edge Function — an unhandled throw renders the
// "edge function has crashed" page. These tests pin that it never throws.

const NEXT = { __kind: "next-response" };

vi.mock("next/server", () => ({
  NextResponse: { next: vi.fn(() => NEXT) },
}));

const getUser = vi.fn();
vi.mock("@supabase/ssr", () => ({
  createServerClient: vi.fn(() => ({ auth: { getUser } })),
}));

function fakeRequest() {
  return {
    cookies: { getAll: () => [], set: vi.fn() },
    headers: new Headers(),
  } as unknown as Parameters<
    typeof import("@/middleware").middleware
  >[0];
}

const ENV = process.env;

beforeEach(() => {
  vi.clearAllMocks();
  process.env = {
    ...ENV,
    NEXT_PUBLIC_SUPABASE_URL: "https://example.supabase.co",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: "anon-key",
    NEXT_PUBLIC_DEMO: "",
  };
});

afterEach(() => {
  process.env = ENV;
});

describe("middleware", () => {
  it("returns a response even when getUser throws (stale/bad cookie)", async () => {
    getUser.mockRejectedValueOnce(new Error("Auth session missing / bad cookie"));
    const { middleware } = await import("@/middleware");
    await expect(middleware(fakeRequest())).resolves.toBe(NEXT);
  });

  it("refreshes the session on the happy path", async () => {
    getUser.mockResolvedValueOnce({ data: { user: { id: "u1" } } });
    const { middleware } = await import("@/middleware");
    await expect(middleware(fakeRequest())).resolves.toBe(NEXT);
    expect(getUser).toHaveBeenCalledOnce();
  });

  it("skips Supabase entirely when env is missing (no crash)", async () => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = "";
    const { middleware } = await import("@/middleware");
    await expect(middleware(fakeRequest())).resolves.toBe(NEXT);
    expect(getUser).not.toHaveBeenCalled();
  });

  it("skips Supabase in demo mode", async () => {
    process.env.NEXT_PUBLIC_DEMO = "1";
    const { middleware } = await import("@/middleware");
    await expect(middleware(fakeRequest())).resolves.toBe(NEXT);
    expect(getUser).not.toHaveBeenCalled();
  });
});

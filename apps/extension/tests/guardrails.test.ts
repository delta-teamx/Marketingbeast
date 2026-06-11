import { describe, expect, it } from "vitest";
import { GUARDRAILS } from "../src/config";
import {
  clampWindow,
  dailyCap,
  evaluate,
  initialState,
  isDuplicate,
  jitteredDelayMs,
  recordPost,
  rolloverDay,
} from "../src/guardrails";

const NOON = new Date(2026, 0, 2, 12, 0, 0).getTime(); // 12:00 local, within 9–18

describe("dailyCap (warm-up ramp)", () => {
  it("starts small and never exceeds the absolute ceiling", () => {
    expect(dailyCap(0)).toBe(2);
    expect(dailyCap(1)).toBe(3);
    expect(dailyCap(100)).toBe(GUARDRAILS.ABSOLUTE_MAX_POSTS_PER_DAY);
  });
});

describe("jitteredDelayMs", () => {
  it("is always within [MIN, MAX) and varies (never fixed)", () => {
    expect(jitteredDelayMs(() => 0)).toBe(GUARDRAILS.MIN_DELAY_MS);
    expect(jitteredDelayMs(() => 0.999)).toBeLessThan(GUARDRAILS.MAX_DELAY_MS);
    expect(jitteredDelayMs(() => 0.5)).toBeGreaterThan(GUARDRAILS.MIN_DELAY_MS);
  });
});

describe("clampWindow", () => {
  it("caps the active span", () => {
    const [s, e] = clampWindow(8, 23);
    expect(e - s).toBeLessThanOrEqual(GUARDRAILS.MAX_ACTIVE_SPAN_HOURS);
  });
});

describe("isDuplicate", () => {
  it("ignores whitespace/case", () => {
    expect(isDuplicate("Hello  World", ["hello world"])).toBe(true);
    expect(isDuplicate("different", ["hello world"])).toBe(false);
  });
});

describe("evaluate", () => {
  it("allows a fresh post inside waking hours", () => {
    expect(evaluate({ ...initialState(), accountAgeDays: 5 }, "hi", NOON).ok).toBe(true);
  });

  it("blocks outside waking hours", () => {
    const night = new Date(2026, 0, 2, 3, 0, 0).getTime();
    expect(evaluate(initialState(), "hi", night).ok).toBe(false);
  });

  it("blocks once the daily cap is hit", () => {
    const s = { ...initialState(), accountAgeDays: 0, postsToday: 2, dayKey: "2026-1-2" };
    const d = evaluate(s, "hi", NOON);
    expect(d.ok).toBe(false);
    expect(d.reason).toMatch(/Daily limit/);
  });

  it("blocks while pacing has not elapsed", () => {
    const s = { ...initialState(), dayKey: "2026-1-2", nextEligibleAt: NOON + 60_000 };
    expect(evaluate(s, "hi", NOON).ok).toBe(false);
  });

  it("blocks near-duplicate content", () => {
    const s = { ...initialState(), dayKey: "2026-1-2", recentBodies: ["buy now"] };
    expect(evaluate(s, "Buy now", NOON).ok).toBe(false);
  });
});

describe("recordPost", () => {
  it("increments the count and schedules the next jittered slot", () => {
    const next = recordPost(initialState(), "hello", NOON, () => 0.5);
    expect(next.postsToday).toBe(1);
    expect(next.lastPostAt).toBe(NOON);
    expect(next.nextEligibleAt).toBeGreaterThan(NOON);
    expect(next.recentBodies[0]).toBe("hello");
  });
});

describe("rolloverDay", () => {
  it("resets the counter on a new local day", () => {
    const s = { ...initialState(), postsToday: 5, dayKey: "2025-1-1" };
    expect(rolloverDay(s, new Date(NOON)).postsToday).toBe(0);
  });
});

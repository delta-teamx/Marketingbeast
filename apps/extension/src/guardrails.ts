// Human-pacing guardrails (brief §9). Pure, deterministic functions so the
// safety logic is unit-tested. `now`/`rng` are injectable for testing; the hard
// limits in config.ts cannot be overridden by the user.

import { GUARDRAILS } from "./config";

export interface PacingState {
  /** Posts already made in the current local day. */
  postsToday: number;
  /** Epoch ms of the last post, or null. */
  lastPostAt: number | null;
  /** Epoch ms before which the next post is not allowed (jittered). */
  nextEligibleAt: number | null;
  /** Days since the account was connected — drives the warm-up ramp. */
  accountAgeDays: number;
  /** User-chosen active window (local hours), clamped to MAX_ACTIVE_SPAN_HOURS. */
  wakingStartHour: number;
  wakingEndHour: number;
  /** The day (local) postsToday is counted against, as YYYY-MM-DD. */
  dayKey: string;
  /** Recent post bodies, newest first, for duplicate detection. */
  recentBodies: string[];
}

export interface PacingDecision {
  ok: boolean;
  reason?: string;
  nextEligibleAt?: number | null;
}

export function dailyCap(accountAgeDays: number): number {
  const ramp = GUARDRAILS.WARMUP_RAMP;
  const idx = Math.max(0, Math.min(accountAgeDays, ramp.length - 1));
  return Math.min(ramp[idx], GUARDRAILS.ABSOLUTE_MAX_POSTS_PER_DAY);
}

export function jitteredDelayMs(rng: () => number = Math.random): number {
  const { MIN_DELAY_MS, MAX_DELAY_MS } = GUARDRAILS;
  return Math.floor(MIN_DELAY_MS + rng() * (MAX_DELAY_MS - MIN_DELAY_MS));
}

/** Clamp the user's window so its span never exceeds MAX_ACTIVE_SPAN_HOURS. */
export function clampWindow(startHour: number, endHour: number): [number, number] {
  const s = Math.max(0, Math.min(23, Math.floor(startHour)));
  let e = Math.max(0, Math.min(24, Math.floor(endHour)));
  if (e <= s) e = s + 1;
  if (e - s > GUARDRAILS.MAX_ACTIVE_SPAN_HOURS) e = s + GUARDRAILS.MAX_ACTIVE_SPAN_HOURS;
  return [s, e];
}

export function isWithinWakingHours(now: Date, state: PacingState): boolean {
  const [s, e] = clampWindow(state.wakingStartHour, state.wakingEndHour);
  const h = now.getHours();
  return h >= s && h < e;
}

function normalize(body: string): string {
  return body.trim().toLowerCase().replace(/\s+/g, " ");
}

export function isDuplicate(body: string, recent: string[]): boolean {
  const n = normalize(body);
  return recent.some((b) => normalize(b) === n);
}

function dayKeyOf(now: Date): string {
  return `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;
}

/** Reset the per-day counter when the local day rolls over. */
export function rolloverDay(state: PacingState, now: Date = new Date()): PacingState {
  const key = dayKeyOf(now);
  if (state.dayKey === key) return state;
  return { ...state, dayKey: key, postsToday: 0 };
}

/** Decide whether a given post may go out right now. Read-only. */
export function evaluate(
  state: PacingState,
  body: string,
  now: number = Date.now(),
): PacingDecision {
  const d = new Date(now);
  const s = rolloverDay(state, d);

  if (!isWithinWakingHours(d, s)) {
    return { ok: false, reason: "Outside your active hours — paused to look human." };
  }
  if (s.postsToday >= dailyCap(s.accountAgeDays)) {
    return { ok: false, reason: "Daily limit reached — this protects your account." };
  }
  if (s.nextEligibleAt !== null && now < s.nextEligibleAt) {
    return {
      ok: false,
      reason: "Pacing — the next post unlocks shortly.",
      nextEligibleAt: s.nextEligibleAt,
    };
  }
  if (isDuplicate(body, s.recentBodies)) {
    return { ok: false, reason: "Too similar to a recent post — vary the wording." };
  }
  return { ok: true };
}

/** Record a completed post and schedule the next jittered eligibility. */
export function recordPost(
  state: PacingState,
  body: string,
  now: number = Date.now(),
  rng: () => number = Math.random,
): PacingState {
  const s = rolloverDay(state, new Date(now));
  return {
    ...s,
    postsToday: s.postsToday + 1,
    lastPostAt: now,
    nextEligibleAt: now + jitteredDelayMs(rng),
    recentBodies: [body, ...s.recentBodies].slice(0, GUARDRAILS.DUPLICATE_WINDOW),
  };
}

export function initialState(now: Date = new Date()): PacingState {
  return {
    postsToday: 0,
    lastPostAt: null,
    nextEligibleAt: null,
    accountAgeDays: 0,
    wakingStartHour: 9,
    wakingEndHour: 18,
    dayKey: dayKeyOf(now),
    recentBodies: [],
  };
}

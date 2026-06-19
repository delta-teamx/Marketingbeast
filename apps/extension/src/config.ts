// Hard-coded §9 safety limits. These are NOT user-configurable — the whole point
// is that a user cannot turn the protections off. Surfaced in the UI as features
// ("we protect your account"), never as adjustable throttles.
export const GUARDRAILS = {
  // Minimum/maximum jittered delay between two group posts. Never a fixed value.
  MIN_DELAY_MS: 4 * 60_000, // 4 min
  MAX_DELAY_MS: 12 * 60_000, // 12 min
  // Absolute ceiling on posts per day regardless of warm-up.
  ABSOLUTE_MAX_POSTS_PER_DAY: 10,
  // Warm-up ramp by days since the account was connected (a quiet/new account
  // starts slow rather than blasting on day one). Index = age in days.
  WARMUP_RAMP: [2, 3, 4, 5, 6, 8, 10],
  // The active window the user picks is clamped to this many hours.
  MAX_ACTIVE_SPAN_HOURS: 12,
  // How many recent post bodies we compare against to block copy-paste spam.
  DUPLICATE_WINDOW: 20,
} as const;

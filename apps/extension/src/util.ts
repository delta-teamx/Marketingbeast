import { clampWindow, type PacingState } from "./guardrails";
import type { Settings } from "./types";

/** Fold the user's chosen active window into pacing state (clamped). */
export function syncWakingHours(pacing: PacingState, settings: Settings): PacingState {
  const [s, e] = clampWindow(settings.wakingStartHour, settings.wakingEndHour);
  return { ...pacing, wakingStartHour: s, wakingEndHour: e };
}

export function formatCountdown(targetMs: number, now: number = Date.now()): string {
  const remaining = Math.max(0, targetMs - now);
  const mins = Math.ceil(remaining / 60_000);
  return remaining === 0 ? "now" : `~${mins} min`;
}

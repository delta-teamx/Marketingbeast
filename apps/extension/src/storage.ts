import { initialState, type PacingState } from "./guardrails";
import type { Settings } from "./types";

const DEFAULT_SETTINGS: Settings = {
  apiBaseUrl: "http://localhost:8000",
  accessToken: "",
  brandId: "",
  consentAccepted: false,
  wakingStartHour: 9,
  wakingEndHour: 18,
};

export async function getSettings(): Promise<Settings> {
  const { settings } = await chrome.storage.local.get("settings");
  return { ...DEFAULT_SETTINGS, ...(settings ?? {}) };
}

export async function saveSettings(patch: Partial<Settings>): Promise<Settings> {
  const next = { ...(await getSettings()), ...patch };
  await chrome.storage.local.set({ settings: next });
  return next;
}

export async function getPacing(): Promise<PacingState> {
  const { pacing } = await chrome.storage.local.get("pacing");
  return pacing ?? initialState();
}

export async function savePacing(state: PacingState): Promise<void> {
  await chrome.storage.local.set({ pacing: state });
}

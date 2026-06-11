// MV3 service worker. Coordinates the assisted-posting loop but NEVER posts on
// its own — it only decides *whether* the next assisted post may be offered
// (per the guardrails) and keeps pacing state. The user always confirms the
// actual post in their own browser (see content.ts).

import { evaluate, recordPost } from "./guardrails";
import { getPacing, getSettings, savePacing, saveSettings } from "./storage";
import { syncWakingHours } from "./util";

const ALARM = "presence-pacing-tick";

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create(ALARM, { periodInMinutes: 1 });
});

// Messages from the popup / content script.
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    if (msg.type === "evaluate") {
      const settings = await getSettings();
      let pacing = syncWakingHours(await getPacing(), settings);
      await savePacing(pacing);
      sendResponse(evaluate(pacing, msg.body));
    } else if (msg.type === "recordPost") {
      // Called only after the user confirms a real post happened.
      const pacing = await getPacing();
      const next = recordPost(pacing, msg.body);
      await savePacing(next);
      sendResponse(next);
    } else if (msg.type === "getState") {
      sendResponse({ settings: await getSettings(), pacing: await getPacing() });
    } else if (msg.type === "saveSettings") {
      sendResponse(await saveSettings(msg.patch));
    }
  })();
  return true; // async response
});

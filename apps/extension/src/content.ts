// Runs on facebook.com. Strictly ASSISTED: it surfaces the queued post text with
// a Copy button and a reminder to follow the group's rules. The user pastes and
// clicks Post themselves — we never auto-submit, auto-click, or spoof anything.

interface PrefillMessage {
  type: "prefill";
  body: string;
  groupName: string;
}

function showAssistBanner(body: string, groupName: string): void {
  document.getElementById("presence-assist")?.remove();

  const bar = document.createElement("div");
  bar.id = "presence-assist";
  bar.style.cssText = [
    "position:fixed",
    "right:16px",
    "bottom:16px",
    "z-index:2147483647",
    "max-width:360px",
    "background:#111",
    "color:#fff",
    "border:1px solid #333",
    "border-radius:10px",
    "padding:14px",
    "font:13px/1.4 system-ui,sans-serif",
    "box-shadow:0 8px 24px rgba(0,0,0,.4)",
  ].join(";");

  const title = document.createElement("div");
  title.textContent = `Presence — post for: ${groupName}`;
  title.style.cssText = "font-weight:600;margin-bottom:6px";

  const text = document.createElement("textarea");
  text.value = body;
  text.readOnly = true;
  text.style.cssText =
    "width:100%;height:80px;background:#000;color:#eee;border:1px solid #333;border-radius:6px;padding:6px";

  const note = document.createElement("div");
  note.textContent =
    "Review the group's rules, paste, then click Post yourself. You are in control.";
  note.style.cssText = "color:#aaa;margin:8px 0";

  const copy = document.createElement("button");
  copy.textContent = "Copy post";
  copy.style.cssText =
    "background:#fff;color:#000;border:none;border-radius:6px;padding:6px 12px;cursor:pointer;margin-right:8px";
  copy.onclick = () => {
    navigator.clipboard.writeText(body).then(
      () => (copy.textContent = "Copied ✓"),
      () => (copy.textContent = "Copy failed — select & copy manually"),
    );
  };

  const close = document.createElement("button");
  close.textContent = "Dismiss";
  close.style.cssText =
    "background:transparent;color:#aaa;border:1px solid #333;border-radius:6px;padding:6px 12px;cursor:pointer";
  close.onclick = () => bar.remove();

  bar.append(title, text, note, copy, close);
  document.body.appendChild(bar);
}

chrome.runtime.onMessage.addListener((msg: PrefillMessage, _sender, sendResponse) => {
  if (msg.type === "prefill") {
    showAssistBanner(msg.body, msg.groupName);
    sendResponse({ ok: true });
  }
  return true;
});

// On load, surface a pending assist queued by the popup before this tab opened.
chrome.storage.local.get("pendingAssist").then(({ pendingAssist }) => {
  if (pendingAssist?.body) {
    showAssistBanner(pendingAssist.body, pendingAssist.groupName ?? "");
    chrome.storage.local.remove("pendingAssist");
  }
});


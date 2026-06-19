// Popup UI. Drives the ASSISTED loop: sync the queue, check guardrails, claim a
// task, open the group, and let the user post + confirm. No silent automation.

import { dailyCap, type PacingState } from "./guardrails";
import { claimTask, completeTask, listQueue, listSuggestions, skipTask } from "./queue-client";
import type { GroupPostTask, Settings } from "./types";
import { formatCountdown } from "./util";

const app = document.getElementById("app")!;

function send<T>(message: unknown): Promise<T> {
  return new Promise((resolve) => chrome.runtime.sendMessage(message, resolve));
}

async function getState(): Promise<{ settings: Settings; pacing: PacingState }> {
  return send({ type: "getState" });
}

function el(html: string): HTMLElement {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild as HTMLElement;
}

async function render(): Promise<void> {
  const { settings, pacing } = await getState();

  if (!settings.consentAccepted) {
    app.innerHTML = "";
    const box = el(`<div>
      <p>Group posting is higher-risk and runs in <b>your</b> browser. You must
      read and accept the safety terms before using it.</p>
      <button id="consent">Read &amp; accept terms</button>
    </div>`);
    box.querySelector("#consent")!.addEventListener("click", () =>
      chrome.tabs.create({ url: chrome.runtime.getURL("consent.html") }),
    );
    app.append(box);
    return;
  }

  app.innerHTML = "";
  const cap = dailyCap(pacing.accountAgeDays);
  app.append(
    el(`<div class="row">
      <span class="pill">Today: ${pacing.postsToday}/${cap}</span>
      <span class="pill">Next: ${
        pacing.nextEligibleAt ? formatCountdown(pacing.nextEligibleAt) : "now"
      }</span>
    </div>`),
  );

  // Settings form.
  const form = el(`<div>
    <label>API base URL</label><input id="api" value="${settings.apiBaseUrl}" />
    <label>Access token (from the Presence web app)</label><input id="tok" type="password" value="${settings.accessToken}" />
    <label>Brand ID</label><input id="brand" value="${settings.brandId}" />
    <div class="row">
      <div><label>Active from (h)</label><input id="ws" type="number" min="0" max="23" value="${settings.wakingStartHour}" /></div>
      <div><label>to (h)</label><input id="we" type="number" min="0" max="24" value="${settings.wakingEndHour}" /></div>
    </div>
    <div class="row"><button id="save">Save</button><button id="sync" class="ghost">Sync queue</button></div>
  </div>`);
  form.querySelector("#save")!.addEventListener("click", async () => {
    await send({
      type: "saveSettings",
      patch: {
        apiBaseUrl: (form.querySelector("#api") as HTMLInputElement).value,
        accessToken: (form.querySelector("#tok") as HTMLInputElement).value,
        brandId: (form.querySelector("#brand") as HTMLInputElement).value,
        wakingStartHour: Number((form.querySelector("#ws") as HTMLInputElement).value),
        wakingEndHour: Number((form.querySelector("#we") as HTMLInputElement).value),
      },
    });
    render();
  });
  form.querySelector("#sync")!.addEventListener("click", () => renderQueue(settings));
  app.append(form);

  const queueRoot = el(`<div id="queue"></div>`);
  app.append(queueRoot);
}

async function renderQueue(settings: Settings): Promise<void> {
  const root = document.getElementById("queue")!;
  root.innerHTML = '<p class="muted">Loading queue…</p>';
  try {
    const [tasks, suggestions] = await Promise.all([
      listQueue(settings),
      listSuggestions(settings),
    ]);
    const keywordById = new Map(suggestions.map((s) => [s.id, s.search_keyword]));
    const nameById = new Map(suggestions.map((s) => [s.id, s.name]));
    root.innerHTML = "";
    const open = tasks.filter((t) => t.status === "queued" || t.status === "claimed");
    if (open.length === 0) {
      root.append(el('<p class="muted">No queued posts.</p>'));
      return;
    }
    for (const task of open) {
      root.append(
        taskCard(
          settings,
          task,
          keywordById.get(task.group_suggestion_id) ?? "",
          nameById.get(task.group_suggestion_id) ?? "group",
        ),
      );
    }
  } catch (e) {
    root.innerHTML = `<p id="blocked">${(e as Error).message}</p>`;
  }
}

function taskCard(
  settings: Settings,
  task: GroupPostTask,
  keyword: string,
  groupName: string,
): HTMLElement {
  const card = el(`<div class="task">
    <div>${task.body}</div>
    <div class="muted">${groupName} · ${task.status}</div>
    <div class="row"></div>
    <div class="note"></div>
  </div>`);
  const row = card.querySelector(".row")!;
  const note = card.querySelector(".note") as HTMLElement;

  const prepare = el(`<button>Prepare in Facebook</button>`);
  prepare.addEventListener("click", async () => {
    const decision = await send<{ ok: boolean; reason?: string }>({
      type: "evaluate",
      body: task.body,
    });
    if (!decision.ok) {
      note.innerHTML = `<span id="blocked">${decision.reason}</span>`;
      return;
    }
    await claimTask(settings, task.id);
    await chrome.storage.local.set({
      pendingAssist: { body: task.body, groupName },
    });
    chrome.tabs.create({
      url: `https://www.facebook.com/search/groups/?q=${encodeURIComponent(keyword)}`,
    });
    note.innerHTML = "Opened Facebook. After you post, click “I posted it”.";
  });

  const done = el(`<button class="ghost">I posted it</button>`);
  done.addEventListener("click", async () => {
    await completeTask(settings, task.id, `manual:${Date.now()}`);
    await send({ type: "recordPost", body: task.body });
    renderQueue(settings);
  });

  const skip = el(`<button class="ghost">Skip</button>`);
  skip.addEventListener("click", async () => {
    await skipTask(settings, task.id);
    renderQueue(settings);
  });

  row.append(prepare, done, skip);
  return card;
}

render();

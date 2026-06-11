// Talks to the Presence backend. The backend is ONLY a queue store — it never
// posts to groups. This client fetches tasks and reports status back after the
// user confirms a post locally.

import type { GroupPostTask, GroupSuggestion, Settings } from "./types";

async function call<T>(s: Settings, path: string, init: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${s.apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${s.accessToken}`,
      ...(init.headers || {}),
    },
  });
  if (!resp.ok) throw new Error(`API ${resp.status}: ${await resp.text()}`);
  return (await resp.json()) as T;
}

export function listQueue(s: Settings): Promise<GroupPostTask[]> {
  return call<GroupPostTask[]>(s, `/api/automation/group-queue?brand_id=${s.brandId}`);
}

export function listSuggestions(s: Settings): Promise<GroupSuggestion[]> {
  return call<GroupSuggestion[]>(s, `/api/group-suggestions?brand_id=${s.brandId}`);
}

function updateTask(
  s: Settings,
  taskId: string,
  status: GroupPostTask["status"],
  externalRef?: string,
): Promise<GroupPostTask> {
  return call<GroupPostTask>(s, `/api/automation/group-queue/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify({ status, external_ref: externalRef ?? null }),
  });
}

export const claimTask = (s: Settings, id: string) => updateTask(s, id, "claimed");
export const completeTask = (s: Settings, id: string, ref: string) =>
  updateTask(s, id, "posted", ref);
export const skipTask = (s: Settings, id: string) => updateTask(s, id, "skipped");

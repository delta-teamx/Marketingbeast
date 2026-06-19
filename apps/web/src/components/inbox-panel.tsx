"use client";

import { useState } from "react";
import type { Conversation, ConversationDetail } from "@presence/shared";
import { api } from "@/lib/api-client";

export function InboxPanel({ brandId }: { brandId: string }) {
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [active, setActive] = useState<ConversationDetail | null>(null);
  const [draft, setDraft] = useState("");
  const [leadsOnly, setLeadsOnly] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [synced, setSynced] = useState(false);

  async function run(fn: () => Promise<void>) {
    setError(null);
    setBusy(true);
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const shown = leadsOnly ? convs.filter((c) => c.is_lead) : convs;

  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-medium">Inbox &amp; leads</h2>
        <div className="flex items-center gap-3 text-sm">
          <label className="flex items-center gap-2 text-white/60">
            <input
              type="checkbox"
              checked={leadsOnly}
              onChange={(e) => setLeadsOnly(e.target.checked)}
            />
            Leads only
          </label>
          <button
            disabled={busy}
            onClick={() =>
              run(async () => {
                setConvs(await api.syncInbox(brandId));
                setSynced(true);
              })
            }
            className="btn-primary rounded-lg px-4 py-2 font-medium disabled:opacity-50"
          >
            {busy ? "Syncing…" : "Sync inbox"}
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {!synced ? (
        <p className="text-sm text-white/60">
          Pull comments &amp; DMs from Facebook and Instagram into one inbox, with
          buyer-intent leads flagged automatically.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          <ul className="flex max-h-96 flex-col gap-2 overflow-auto">
            {shown.map((c) => (
              <li key={c.id}>
                <button
                  onClick={() =>
                    run(async () => {
                      const detail = await api.getConversation(c.id);
                      setActive(detail);
                      setDraft("");
                    })
                  }
                  className={`w-full rounded-lg border p-3 text-left text-sm ${
                    active?.id === c.id ? "border-[#6d5efc]" : "border-white/10"
                  } hover:bg-white/5`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{c.participant_name}</span>
                    {c.is_lead && (
                      <span className="rounded-full bg-[#22d3ee]/20 px-2 py-0.5 text-xs text-[#a5f3fc]">
                        Lead · {c.lead_score}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-white/40">
                    {c.conv_type} · {c.status}
                  </div>
                </button>
              </li>
            ))}
          </ul>

          <div className="card flex flex-col gap-3 p-4">
            {!active ? (
              <p className="text-sm text-white/50">Select a conversation.</p>
            ) : (
              <>
                <div className="flex flex-col gap-2">
                  {active.messages.map((m) => (
                    <div
                      key={m.id}
                      className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                        m.is_inbound
                          ? "self-start bg-white/10"
                          : "self-end bg-[#6d5efc]/30"
                      }`}
                    >
                      {m.text}
                    </div>
                  ))}
                </div>

                {active.status !== "hidden" && (
                  <>
                    <div className="flex gap-2">
                      <button
                        disabled={busy}
                        onClick={() =>
                          run(async () => {
                            const d = await api.draftReply(active.id);
                            setDraft(d.text);
                          })
                        }
                        className="btn-ghost rounded-lg px-3 py-1.5 text-sm"
                      >
                        ✨ Draft reply
                      </button>
                      <button
                        disabled={busy}
                        onClick={() =>
                          run(async () => {
                            const d = await api.hideConversation(active.id);
                            setActive(d);
                            setConvs(await api.listInbox(brandId));
                          })
                        }
                        className="btn-ghost rounded-lg px-3 py-1.5 text-sm text-white/60"
                      >
                        Hide
                      </button>
                    </div>
                    <textarea
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      placeholder="Write or edit a reply…"
                      rows={3}
                      className="rounded-lg border border-white/15 bg-transparent px-3 py-2 text-sm"
                    />
                    <button
                      disabled={busy || !draft}
                      onClick={() =>
                        run(async () => {
                          const d = await api.sendReply(active.id, draft);
                          setActive(d);
                          setDraft("");
                          setConvs(await api.listInbox(brandId));
                        })
                      }
                      className="btn-primary rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
                    >
                      Send reply
                    </button>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

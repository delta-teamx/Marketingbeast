"use client";

import { useEffect, useState } from "react";
import type { MediaAsset, MediaJob, SocialAccount } from "@presence/shared";
import { api } from "@/lib/api-client";

export function MediaPanel({
  brandId,
  accounts = [],
}: {
  brandId: string;
  accounts?: SocialAccount[];
}) {
  const [credits, setCredits] = useState<number | null>(null);
  const [jobs, setJobs] = useState<MediaJob[]>([]);
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const reload = async () => {
    const [c, j, a] = await Promise.all([
      api.getCredits(brandId),
      api.listMediaJobs(brandId),
      api.listMediaAssets(brandId),
    ]);
    setCredits(c.credit_balance);
    setJobs(j);
    setAssets(a);
  };

  useEffect(() => {
    reload().catch((e) => setError((e as Error).message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brandId]);

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-medium">AI video &amp; reels</h2>
        <div className="flex items-center gap-2 text-sm">
          <span className="rounded-full bg-white/10 px-3 py-1">
            {credits ?? "—"} credits
          </span>
          <button
            disabled={busy}
            onClick={() => run(async () => {
              await api.topupCredits(brandId, 50);
              await reload();
            })}
            className="btn-ghost rounded-lg px-3 py-1 text-xs"
          >
            +50
          </button>
        </div>
      </div>
      <p className="text-xs text-white/50">
        Turn a note or product link into a UGC-style reel. Each render costs 10 credits.
      </p>
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="flex gap-2">
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="What's the video about? (e.g. fall menu launch)"
          className="flex-1 rounded-lg border border-white/15 bg-transparent px-3 py-2 text-sm"
        />
        <button
          disabled={busy || !note}
          onClick={() => run(async () => {
            await api.generateVideo(brandId, note);
            setNote("");
            await reload();
          })}
          className="btn-primary rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          Generate reel
        </button>
      </div>

      {jobs.length > 0 && (
        <ul className="flex flex-col gap-2">
          {jobs.map((j) => (
            <li key={j.id} className="card flex items-center justify-between gap-3 p-3 text-sm">
              <div className="min-w-0">
                <div className="truncate">{j.prompt || "Untitled reel"}</div>
                <div className="text-xs text-white/50">
                  {j.provider} · {j.status}
                  {j.asset_url ? (
                    <>
                      {" · "}
                      <a href={j.asset_url} target="_blank" rel="noreferrer" className="underline">
                        view
                      </a>
                    </>
                  ) : (
                    ""
                  )}
                </div>
              </div>
              {j.status === "rendering" && (
                <button
                  onClick={() => run(async () => {
                    await api.pollMediaJob(j.id);
                    await reload();
                  })}
                  className="btn-ghost rounded-lg px-3 py-1 text-xs"
                >
                  Check status
                </button>
              )}
              {j.status === "ready" && (() => {
                const asset = assets.find((a) => a.url === j.asset_url);
                if (!asset) {
                  // The job is ready but its asset hasn't shown up in the list
                  // yet (brief sync lag) — show a clear waiting state, not a
                  // silently missing button.
                  return (
                    <span className="text-xs text-white/50">Preparing reel…</span>
                  );
                }
                return (
                  <button
                    disabled={busy || accounts.length === 0}
                    onClick={() => run(async () => {
                      await api.publishReel(asset.id, {
                        body: j.prompt || j.script || "",
                        target_account_ids: accounts.map((a) => a.id),
                      });
                      await reload();
                    })}
                    className="btn-primary rounded-lg px-3 py-1 text-xs disabled:opacity-50"
                  >
                    Publish as reel
                  </button>
                );
              })()}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

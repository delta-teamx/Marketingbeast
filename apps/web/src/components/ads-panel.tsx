"use client";

import { useEffect, useState } from "react";
import type {
  AdAccount,
  AdCampaign,
  AdCampaignDetail,
  AdRecommendations,
} from "@presence/shared";
import { api } from "@/lib/api-client";

export function AdsPanel({ brandId }: { brandId: string }) {
  const [accounts, setAccounts] = useState<AdAccount[]>([]);
  const [campaigns, setCampaigns] = useState<AdCampaign[]>([]);
  const [active, setActive] = useState<AdCampaignDetail | null>(null);
  const [recs, setRecs] = useState<AdRecommendations | null>(null);
  const [name, setName] = useState("");
  const [concept, setConcept] = useState("");
  const [budget, setBudget] = useState("25");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // null = still loading; false = live mode (Ads Manager is coming soon).
  const [adsEnabled, setAdsEnabled] = useState<boolean | null>(null);

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
    const [accts, camps] = await Promise.all([
      api.listAdAccounts(brandId),
      api.listCampaigns(brandId),
    ]);
    setAccounts(accts);
    setCampaigns(camps);
  };

  useEffect(() => {
    api
      .config()
      .then((c) => {
        setAdsEnabled(c.ads_enabled);
        if (c.ads_enabled) return reload();
      })
      .catch((e) => setError((e as Error).message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brandId]);

  // Live mode: the real Meta Marketing API path isn't built yet — show a clear
  // coming-soon state instead of a connect flow that can't work.
  if (adsEnabled === false) {
    return (
      <section className="flex flex-col gap-3">
        <h2 className="text-xl font-medium">Ads manager</h2>
        <div className="card flex flex-col gap-2 p-5">
          <div className="flex items-center gap-2">
            <span className="text-lg">🚧</span>
            <span className="font-medium">Coming soon</span>
          </div>
          <p className="text-sm text-white/60">
            Launch and optimize paid Meta ad campaigns from here — auto-generated
            creatives and pause/scale recommendations. It needs Meta Marketing API
            access (<code className="text-white/70">ads_management</code>) and its
            own App Review, which we&apos;re rolling out next.
          </p>
          <p className="text-xs text-white/40">
            Your organic posting, content, and Instagram/Facebook publishing are
            live and unaffected.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-xl font-medium">Ads manager</h2>
      {error && <p className="text-sm text-red-400">{error}</p>}

      {accounts.length === 0 ? (
        <div className="flex flex-col gap-2">
          <p className="text-sm text-white/60">
            Connect an ad account to plan campaigns and auto-generate creative variations.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <button
              disabled={busy}
              onClick={() => run(async () => {
                await api.connectAdAccount(brandId);
                await reload();
              })}
              className="btn-primary rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
            >
              Connect ad account
            </button>
            <span className="text-xs text-white/40">
              Live Meta ad spend arrives after Marketing API approval — available now in demo mode.
            </span>
          </div>
        </div>
      ) : (
        <>
          <div className="card flex flex-col gap-2 p-4">
            <div className="text-sm text-white/60">
              New campaign — we auto-generate 12 creative variations to find winners.
            </div>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Campaign name"
              className="rounded-lg border border-white/15 bg-transparent px-3 py-2 text-sm"
            />
            <input
              value={concept}
              onChange={(e) => setConcept(e.target.value)}
              placeholder="Concept / offer (e.g. fall menu launch)"
              className="rounded-lg border border-white/15 bg-transparent px-3 py-2 text-sm"
            />
            <div className="flex items-center gap-2">
              <label className="text-sm text-white/60">Daily budget $</label>
              <input
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                type="number"
                className="w-24 rounded-lg border border-white/15 bg-transparent px-3 py-2 text-sm"
              />
              <button
                disabled={busy || !name}
                onClick={() => run(async () => {
                  const detail = await api.createCampaign(brandId, {
                    ad_account_id: accounts[0].id,
                    name,
                    objective: "LEADS",
                    daily_budget: Number(budget) || 10,
                    concept,
                    n_variations: 12,
                  });
                  setActive(detail);
                  setName("");
                  setConcept("");
                  await reload();
                })}
                className="btn-primary rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                Launch campaign
              </button>
            </div>
          </div>

          {campaigns.length > 0 && (
            <ul className="flex flex-col gap-2">
              {campaigns.map((c) => (
                <li
                  key={c.id}
                  className="card flex items-center justify-between gap-3 p-3 text-sm"
                >
                  <div>
                    <div className="font-medium">{c.name}</div>
                    <div className="text-xs text-white/50">
                      {c.status} · ${c.daily_budget}/day
                      {c.metrics_json?.ctr != null ? ` · CTR ${c.metrics_json.ctr}%` : ""}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => run(async () => {
                        const d = await api.syncCampaign(c.id);
                        setActive(d);
                        setRecs(await api.campaignRecommendations(c.id));
                        await reload();
                      })}
                      className="btn-ghost rounded-lg px-3 py-1 text-xs"
                    >
                      Sync
                    </button>
                    <button
                      onClick={() => run(async () => {
                        await api.setCampaignStatus(
                          c.id,
                          c.status === "active" ? "paused" : "active",
                        );
                        await reload();
                      })}
                      className="btn-ghost rounded-lg px-3 py-1 text-xs"
                    >
                      {c.status === "active" ? "Pause" : "Activate"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {recs && recs.recommendations.length > 0 && (
            <div className="card p-4 text-sm">
              <div className="mb-1 font-medium">AI recommendations</div>
              <p className="text-white/70">{recs.summary}</p>
              <ul className="mt-2 flex flex-col gap-1 text-white/60">
                {recs.recommendations.map((r, i) => (
                  <li key={i}>
                    <span className={r.action === "scale" ? "text-emerald-400" : "text-amber-400"}>
                      {r.action}
                    </span>{" "}
                    — {r.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {active && (
            <details className="card p-4 text-sm">
              <summary className="cursor-pointer text-white/70">
                {active.creatives.length} creatives for “{active.name}”
              </summary>
              <ul className="mt-2 flex flex-col gap-1 text-white/60">
                {active.creatives.map((cr) => (
                  <li key={cr.id} className="flex justify-between gap-3">
                    <span className="truncate">{cr.headline}</span>
                    <span className="shrink-0">
                      {cr.metrics_json?.ctr != null ? `CTR ${cr.metrics_json.ctr}%` : "—"}
                    </span>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </>
      )}
    </section>
  );
}

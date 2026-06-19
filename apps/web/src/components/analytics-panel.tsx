"use client";

import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type {
  CompetitorComparison,
  DashboardData,
  Report,
  ReportPeriod,
} from "@presence/shared";
import { api } from "@/lib/api-client";

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="card p-4">
      <div className="text-xs text-white/50">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
}

export function AnalyticsPanel({ brandId }: { brandId: string }) {
  const [dash, setDash] = useState<DashboardData | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [comparison, setComparison] = useState<CompetitorComparison | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [compName, setCompName] = useState("");
  const [compFollowers, setCompFollowers] = useState("");

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

  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-medium">Analytics</h2>
        <button
          disabled={busy}
          onClick={() =>
            run(async () => {
              const [d, r] = await Promise.all([
                api.syncInsights(brandId),
                api.listReports(brandId),
              ]);
              setDash(d);
              setReports(r);
            })
          }
          className="btn-primary rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {busy ? "Syncing…" : "Sync insights"}
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {!dash ? (
        <p className="text-sm text-white/60">
          Sync insights to see reach, engagement and growth across your accounts.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Kpi label="Followers" value={dash.followers.toLocaleString()} />
            <Kpi label="Growth" value={`+${dash.follower_growth.toLocaleString()}`} />
            <Kpi label="Reach" value={dash.total_reach.toLocaleString()} />
            <Kpi label="Engagement rate" value={`${dash.engagement_rate}%`} />
          </div>

          <div className="card p-4">
            <div className="mb-2 text-sm text-white/60">Followers &amp; engagement</div>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={dash.time_series}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="date" stroke="#9aa0b4" fontSize={11} tickFormatter={(d) => d.slice(5)} />
                <YAxis stroke="#9aa0b4" fontSize={11} width={40} />
                <Tooltip
                  contentStyle={{ background: "#0e0e16", border: "1px solid rgba(255,255,255,.1)" }}
                />
                <Line type="monotone" dataKey="followers" stroke="#6d5efc" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="engagement" stroke="#22d3ee" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {dash.top_posts.length > 0 && (
            <div className="card p-4">
              <div className="mb-2 text-sm text-white/60">Top posts</div>
              <ul className="flex flex-col gap-2 text-sm">
                {dash.top_posts.map((p) => (
                  <li key={p.id} className="flex justify-between gap-3">
                    <span className="truncate text-white/80">{p.body}</span>
                    <span className="shrink-0 text-white/50">{p.engagement} eng</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-2">
            {(["weekly", "monthly"] as ReportPeriod[]).map((period) => (
              <button
                key={period}
                disabled={busy}
                onClick={() =>
                  run(async () => {
                    await api.generateReport(brandId, period);
                    setReports(await api.listReports(brandId));
                  })
                }
                className="btn-ghost rounded-lg px-3 py-1.5 text-sm capitalize"
              >
                Generate {period} report
              </button>
            ))}
          </div>

          {reports.length > 0 && (
            <div className="flex flex-col gap-2">
              {reports.slice(0, 4).map((r) => (
                <div key={r.id} className="card p-3 text-sm">
                  <div className="text-white/50">
                    {r.period} · {r.starts_on} → {r.ends_on}
                  </div>
                  <div className="mt-1 text-white/80">{r.summary}</div>
                </div>
              ))}
            </div>
          )}

          <div className="card flex flex-col gap-3 p-4">
            <div className="text-sm text-white/60">Competitor tracking</div>
            <div className="flex flex-wrap gap-2">
              <input
                value={compName}
                onChange={(e) => setCompName(e.target.value)}
                placeholder="Competitor name"
                className="flex-1 rounded-lg border border-white/15 bg-transparent px-3 py-1.5 text-sm"
              />
              <input
                value={compFollowers}
                onChange={(e) => setCompFollowers(e.target.value)}
                placeholder="Followers"
                type="number"
                className="w-28 rounded-lg border border-white/15 bg-transparent px-3 py-1.5 text-sm"
              />
              <button
                disabled={busy || !compName}
                onClick={() =>
                  run(async () => {
                    await api.addCompetitor(brandId, {
                      name: compName,
                      followers: Number(compFollowers) || 0,
                      engagement_rate: 0,
                    });
                    setComparison(await api.compareCompetitors(brandId));
                    setCompName("");
                    setCompFollowers("");
                  })
                }
                className="btn-ghost rounded-lg px-3 py-1.5 text-sm"
              >
                Add &amp; compare
              </button>
            </div>
            {comparison && (
              <div className="text-sm">
                <p className="text-white/70">{comparison.summary}</p>
                <ul className="mt-2 flex flex-col gap-1 text-white/60">
                  {comparison.competitors.map((c) => (
                    <li key={c.name}>
                      {c.name}: {c.followers.toLocaleString()} followers (
                      {c.follower_gap >= 0 ? "+" : ""}
                      {c.follower_gap.toLocaleString()} vs you)
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
}

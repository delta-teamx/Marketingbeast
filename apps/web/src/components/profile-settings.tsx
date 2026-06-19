"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import type {
  Brand,
  Me,
  OnboardingResult,
  Organization,
  OrgSettings,
} from "@presence/shared";
import { api } from "@/lib/api-client";

const PLANS: { key: OrgSettings["plan"]; label: string; blurb: string }[] = [
  { key: "free", label: "Free", blurb: "1 brand · 1 seat" },
  { key: "growth", label: "Growth", blurb: "3 brands · 3 seats · 200 credits" },
  { key: "agency", label: "Agency", blurb: "Unlimited brands & seats · 1000 credits" },
];

export function ProfileSettings() {
  const [me, setMe] = useState<Me | null>(null);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [orgId, setOrgId] = useState<string | null>(null);
  const [settings, setSettings] = useState<OrgSettings | null>(null);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [profile, setProfile] = useState<OnboardingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingPlan, setSavingPlan] = useState<string | null>(null);

  const loadOrg = useCallback(async (id: string) => {
    const [s, b] = await Promise.all([api.orgSettings(id), api.listBrands(id)]);
    setSettings(s);
    setBrands(b);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        // /api/auth/me idempotently provisions the personal org; await it before
        // listing so a brand-new user's org is guaranteed to exist.
        const meRes = await api.me();
        const [orgList, onboarding] = await Promise.all([
          api.listOrgs(),
          api.getOnboarding().catch(() => null),
        ]);
        setMe(meRes);
        setOrgs(orgList);
        setProfile(onboarding);
        const first = orgList[0]?.id ?? null;
        setOrgId(first);
        if (first) await loadOrg(first);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, [loadOrg]);

  async function selectOrg(id: string) {
    setOrgId(id);
    setError(null);
    try {
      await loadOrg(id);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function changePlan(plan: OrgSettings["plan"]) {
    if (!orgId) return;
    setError(null);
    setSavingPlan(plan);
    try {
      setSettings(await api.changePlan(orgId, plan));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSavingPlan(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-3 text-white/60">
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white/70" />
        Loading your profile…
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Profile &amp; workspace</h1>
        <Link href="/dashboard" className="btn-ghost rounded-lg px-3 py-1.5 text-sm">
          ← Dashboard
        </Link>
      </div>

      {error && (
        <p className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {/* Account */}
      <section className="card flex flex-col gap-3 p-4">
        <h2 className="text-sm uppercase tracking-wider text-white/40">Account</h2>
        <Row label="Email" value={me?.email ?? "—"} />
        <Row label="User ID" value={me?.id ?? "—"} mono />
        <Row label="Workspaces" value={String(orgs.length)} />
      </section>

      {/* Workspace */}
      <section className="card flex flex-col gap-4 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm uppercase tracking-wider text-white/40">Workspace</h2>
          {orgs.length > 1 && (
            <select
              value={orgId ?? ""}
              onChange={(e) => selectOrg(e.target.value)}
              className="rounded-lg border border-white/15 bg-transparent px-3 py-1.5 text-sm"
            >
              {orgs.map((o) => (
                <option key={o.id} value={o.id} className="bg-[#0e0e16]">
                  {o.name}
                  {o.is_personal ? " (personal)" : ""}
                </option>
              ))}
            </select>
          )}
        </div>

        {settings && (
          <>
            <Row label="Name" value={settings.name} />
            <Row
              label="Plan"
              value={
                <span className="rounded-full bg-white/10 px-2.5 py-0.5 text-xs uppercase tracking-wide">
                  {settings.plan}
                </span>
              }
            />
            <Row label="Credits" value={String(settings.credit_balance)} />

            <div className="flex flex-col gap-2 pt-2">
              <span className="text-xs text-white/50">
                Change plan (mock billing — applies instantly)
              </span>
              <div className="flex flex-wrap gap-2">
                {PLANS.map((p) => {
                  const active = settings.plan === p.key;
                  return (
                    <button
                      key={p.key}
                      disabled={active || savingPlan !== null}
                      onClick={() => changePlan(p.key)}
                      className={`flex flex-col items-start gap-0.5 rounded-lg border px-3 py-2 text-left text-sm transition disabled:opacity-60 ${
                        active
                          ? "border-[#6d5efc] bg-[#6d5efc]/10"
                          : "border-white/15 hover:bg-white/5"
                      }`}
                    >
                      <span className="font-medium">
                        {p.label}
                        {active ? " · current" : ""}
                        {savingPlan === p.key ? " · saving…" : ""}
                      </span>
                      <span className="text-xs text-white/50">{p.blurb}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </section>

      {/* Brands */}
      <section className="card flex flex-col gap-3 p-4">
        <h2 className="text-sm uppercase tracking-wider text-white/40">
          Brands ({brands.length})
        </h2>
        {brands.length === 0 ? (
          <p className="text-sm text-white/60">No brands yet.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {brands.map((b) => (
              <li
                key={b.id}
                className="flex flex-col gap-0.5 rounded-md border border-white/10 p-3"
              >
                <span className="font-medium">{b.name}</span>
                <span className="text-xs text-white/50">
                  {b.industry_vertical || "industry not set"}
                  {b.website_url ? ` · ${b.website_url}` : ""}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Business profile (onboarding) */}
      <section className="card flex flex-col gap-3 p-4">
        <h2 className="text-sm uppercase tracking-wider text-white/40">
          Business profile
        </h2>
        {!profile ? (
          <p className="text-sm text-white/60">
            No onboarding profile yet.{" "}
            <Link href="/onboarding" className="underline">
              Complete onboarding
            </Link>{" "}
            to tailor your audit, voice and content.
          </p>
        ) : (
          <>
            <Row label="Business" value={profile.brand.name} />
            <Row label="Goal" value={profile.profile.goal ?? "—"} />
            <Row
              label="Platforms"
              value={(profile.profile.platforms ?? []).join(", ") || "—"}
            />
            <Row label="Cadence" value={profile.profile.posting_frequency ?? "—"} />
            <Row label="Budget" value={profile.profile.monthly_budget ?? "—"} />
            <Row
              label="Biggest challenge"
              value={profile.profile.biggest_challenge ?? "—"}
            />
            <Row label="Audience" value={profile.profile.target_audience ?? "—"} />
          </>
        )}
      </section>
    </div>
  );
}

function Row({
  label,
  value,
  mono,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
      <span className="text-white/50">{label}</span>
      <span className={mono ? "font-mono text-xs text-white/70" : "text-white/90"}>
        {value}
      </span>
    </div>
  );
}

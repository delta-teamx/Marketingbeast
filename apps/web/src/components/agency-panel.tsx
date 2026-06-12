"use client";

import { useCallback, useEffect, useState } from "react";
import type { Invite, Member, OrgSettings } from "@presence/shared";
import { api } from "@/lib/api-client";

const PLANS: OrgSettings["plan"][] = ["free", "growth", "agency"];

export function AgencyPanel({ orgId }: { orgId: string }) {
  const [settings, setSettings] = useState<OrgSettings | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [email, setEmail] = useState("");
  const [brandName, setBrandName] = useState("");
  const [logoUrl, setLogoUrl] = useState("");
  const [color, setColor] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const [s, m, inv] = await Promise.all([
      api.orgSettings(orgId),
      api.listMembers(orgId),
      api.listInvites(orgId).catch(() => []),
    ]);
    setSettings(s);
    setMembers(m);
    setInvites(inv);
    setBrandName(s.white_label_json?.brand_name ?? "");
    setLogoUrl(s.white_label_json?.logo_url ?? "");
    setColor(s.white_label_json?.primary_color ?? "");
  }, [orgId]);

  useEffect(() => {
    reload().catch((e) => setError((e as Error).message));
  }, [reload]);

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

  if (!settings) return null;

  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-xl font-medium">Agency &amp; team</h2>
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="card flex flex-wrap items-center gap-3 p-4 text-sm">
        <span>
          Plan: <span className="font-medium capitalize">{settings.plan}</span>
        </span>
        <span className="text-white/40">·</span>
        {PLANS.map((p) => (
          <button
            key={p}
            disabled={busy || p === settings.plan}
            onClick={() => run(async () => {
              await api.changePlan(orgId, p);
              await reload();
            })}
            className="btn-ghost rounded-lg px-3 py-1 text-xs capitalize disabled:opacity-40"
          >
            {p}
          </button>
        ))}
      </div>

      <div className="card flex flex-col gap-2 p-4">
        <div className="text-sm text-white/60">White-label (reports &amp; branding)</div>
        <div className="grid gap-2 md:grid-cols-3">
          <input
            value={brandName}
            onChange={(e) => setBrandName(e.target.value)}
            placeholder="Agency name"
            className="rounded-lg border border-white/15 bg-transparent px-3 py-2 text-sm"
          />
          <input
            value={logoUrl}
            onChange={(e) => setLogoUrl(e.target.value)}
            placeholder="Logo URL"
            className="rounded-lg border border-white/15 bg-transparent px-3 py-2 text-sm"
          />
          <input
            value={color}
            onChange={(e) => setColor(e.target.value)}
            placeholder="#6d5efc"
            className="rounded-lg border border-white/15 bg-transparent px-3 py-2 text-sm"
          />
        </div>
        <button
          disabled={busy}
          onClick={() => run(async () => {
            await api.updateWhiteLabel(orgId, {
              brand_name: brandName,
              logo_url: logoUrl,
              primary_color: color,
            });
            await reload();
          })}
          className="btn-ghost w-fit rounded-lg px-3 py-1.5 text-sm"
        >
          Save branding
        </button>
      </div>

      <div className="card flex flex-col gap-2 p-4">
        <div className="text-sm text-white/60">Team</div>
        <ul className="flex flex-col gap-1 text-sm">
          {members.map((m) => (
            <li key={m.id} className="flex items-center justify-between">
              <span>{m.email ?? m.user_id.slice(0, 8)}</span>
              <span className="text-xs text-white/50">{m.role}</span>
            </li>
          ))}
        </ul>
        <div className="flex gap-2">
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="teammate@email.com"
            className="flex-1 rounded-lg border border-white/15 bg-transparent px-3 py-2 text-sm"
          />
          <button
            disabled={busy || !email}
            onClick={() => run(async () => {
              await api.createInvite(orgId, email, "member");
              setEmail("");
              await reload();
            })}
            className="btn-primary rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            Invite
          </button>
        </div>
        {invites.filter((i) => i.status === "pending").length > 0 && (
          <div className="text-xs text-white/50">
            Pending:{" "}
            {invites
              .filter((i) => i.status === "pending")
              .map((i) => i.email)
              .join(", ")}
          </div>
        )}
      </div>
    </section>
  );
}

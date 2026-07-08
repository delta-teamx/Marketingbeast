"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  AuditReport,
  Brand,
  ContentItem,
  GroupPostTask,
  GroupSuggestion,
  Invite,
  Organization,
  SocialAccount,
} from "@presence/shared";
import { api } from "@/lib/api-client";
import { AnalyticsPanel } from "@/components/analytics-panel";
import { InboxPanel } from "@/components/inbox-panel";
import { AdsPanel } from "@/components/ads-panel";
import { MediaPanel } from "@/components/media-panel";
import { AgencyPanel } from "@/components/agency-panel";
import { OnboardingForm } from "@/components/onboarding-form";

export function Workspace() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [orgId, setOrgId] = useState<string | null>(null);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [brand, setBrand] = useState<Brand | null>(null);
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [groups, setGroups] = useState<GroupSuggestion[]>([]);
  const [groupQueue, setGroupQueue] = useState<GroupPostTask[]>([]);
  const [audit, setAudit] = useState<AuditReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [slow, setSlow] = useState(false);
  const [tab, setTab] = useState<TabKey>("overview");

  const refreshBrandData = useCallback(async (brandId: string) => {
    const [accts, items, sugg, queue, report] = await Promise.all([
      api.listSocialAccounts(brandId),
      api.listContent(brandId),
      api.listGroupSuggestions(brandId),
      api.listGroupQueue(brandId),
      api.getAudit(brandId),
    ]);
    setAccounts(accts);
    setContent(items);
    setGroups(sugg);
    setGroupQueue(queue);
    setAudit(report);
  }, []);

  const selectOrgBrands = useCallback(
    async (id: string) => {
      const brands = await api.listBrands(id);
      setBrand(brands[0] ?? null);
      if (brands[0]) await refreshBrandData(brands[0].id);
      else {
        setAccounts([]);
        setContent([]);
        setGroups([]);
        setGroupQueue([]);
        setAudit(null);
      }
    },
    [refreshBrandData],
  );

  useEffect(() => {
    // The API runs on a free tier that sleeps after idle; the first request
    // wakes it (cold start). Surface a hint if loading drags on so it doesn't
    // look frozen.
    const slowTimer = setTimeout(() => setSlow(true), 4000);
    (async () => {
      try {
        await api.me(); // provision personal org
        const [orgList, pending] = await Promise.all([api.listOrgs(), api.myInvites()]);
        setOrgs(orgList);
        setInvites(pending);
        if (!orgList[0]) {
          // me() provisions a personal org, so this is only reachable if that
          // raced or failed — fail with a clear, recoverable message.
          setError("We couldn't finish setting up your workspace. Please refresh to try again.");
          return;
        }
        setOrgId(orgList[0].id);
        await selectOrgBrands(orgList[0].id);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        clearTimeout(slowTimer);
        setLoading(false);
      }
    })();
    return () => clearTimeout(slowTimer);
  }, [selectOrgBrands]);

  async function run(fn: () => Promise<void>) {
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col gap-2 text-white/60">
        <div className="flex items-center gap-3">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white/70" />
          Loading workspace…
        </div>
        {slow && (
          <p className="text-xs text-white/40">
            Waking up the server — the first load after a quiet spell can take up
            to a minute. Hang tight.
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Workspace bar */}
      <div className="glass flex flex-wrap items-center justify-between gap-3 p-3">
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase tracking-wider text-white/40">Workspace</span>
          <select
            value={orgId ?? ""}
            onChange={(e) =>
              run(async () => {
                setOrgId(e.target.value);
                await selectOrgBrands(e.target.value);
              })
            }
            className="rounded-lg border border-white/15 bg-transparent px-3 py-1.5 text-sm"
          >
            {orgs.map((o) => (
              <option key={o.id} value={o.id} className="bg-[#0e0e16]">
                {o.name}
                {o.is_personal ? " (personal)" : ""}
              </option>
            ))}
          </select>
          {brand && (
            <span className="rounded-full bg-white/5 px-3 py-1 text-sm text-white/70">
              {brand.name}
            </span>
          )}
        </div>
        <button
          onClick={() =>
            run(async () => {
              const name = prompt("New agency workspace name");
              if (!name) return;
              const o = await api.createOrg(name);
              setOrgs(await api.listOrgs());
              setOrgId(o.id);
              await selectOrgBrands(o.id);
            })
          }
          className="btn-ghost rounded-lg px-3 py-1.5 text-xs"
        >
          + New workspace
        </button>
      </div>

      {error && (
        <p className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {invites.length > 0 && (
        <div className="card flex flex-col gap-2 p-3 text-sm">
          <span className="text-white/70">You have pending invitations:</span>
          {invites.map((i) => (
            <div key={i.id} className="flex items-center justify-between">
              <span>
                {i.email} · {i.role}
              </span>
              <button
                onClick={() =>
                  run(async () => {
                    await api.acceptInvite(i.id);
                    const [orgList, pending] = await Promise.all([
                      api.listOrgs(),
                      api.myInvites(),
                    ]);
                    setOrgs(orgList);
                    setInvites(pending);
                  })
                }
                className="btn-primary rounded-md px-3 py-1 text-xs font-medium"
              >
                Accept
              </button>
            </div>
          ))}
        </div>
      )}

      {!brand ? (
        <section className="card flex flex-col gap-4 p-5">
          <OnboardingForm
            embedded
            onDone={() =>
              run(async () => {
                if (orgId) await selectOrgBrands(orgId);
              })
            }
          />
        </section>
      ) : (
        <div className="flex flex-col gap-6 md:flex-row md:items-start">
          {/* Sidebar navigation */}
          <aside className="md:w-56 md:shrink-0">
            <nav className="card flex gap-1 overflow-x-auto p-2 md:flex-col">
              {TABS.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  className={`flex shrink-0 items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition ${
                    tab === t.key
                      ? "bg-[#6d5efc] font-medium text-white"
                      : "text-white/60 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <NavIcon name={t.key} />
                  <span>{t.label}</span>
                </button>
              ))}
              <a
                href="/settings"
                className="flex shrink-0 items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-white/60 transition hover:bg-white/5 hover:text-white"
              >
                <NavIcon name="settings" />
                <span>Settings</span>
              </a>
            </nav>
          </aside>

          <main className="flex min-w-0 flex-1 flex-col gap-6">
            {tab === "overview" && (
              <>
                <AiSuggestions
                  report={audit}
                  onRun={() => run(async () => { await api.runAudit(brand.id); await refreshBrandData(brand.id); })}
                  goTo={setTab}
                />
                <GrowthRoadmap
                  hasAudit={!!audit}
                  accountsConnected={accounts.length > 0}
                  contentCount={content.length}
                  groupCount={groups.length}
                  onRunAudit={() =>
                    run(async () => {
                      await api.runAudit(brand.id);
                      await refreshBrandData(brand.id);
                    })
                  }
                  goTo={setTab}
                />
                <AuditPanel
                  report={audit}
                  onRun={() => run(async () => { await api.runAudit(brand.id); await refreshBrandData(brand.id); })}
                  onSeed={() => run(async () => { await api.seedFirstWeek(brand.id); await refreshBrandData(brand.id); })}
                />
                <Connections
                  brand={brand}
                  accounts={accounts}
                  onConnect={() =>
                    run(async () => {
                      const { authorize_url } = await api.startOAuth(brand.id);
                      window.location.href = authorize_url;
                    })
                  }
                />
              </>
            )}

            {tab === "content" && (
              <>
                <WeeklyPlanner items={content} />
                <GenerateWeek
                  onGenerate={(prompt) => run(async () => { await api.generateContent(brand.id, prompt); await refreshBrandData(brand.id); })}
                />
                <Composer
                  accounts={accounts}
                  onCreate={(input) => run(async () => { await api.createContent({ ...input, brand_id: brand.id }); await refreshBrandData(brand.id); })}
                />
                <ContentList
                  items={content}
                  onPublish={(id) => run(async () => { await api.publishNow(id); await refreshBrandData(brand.id); })}
                  onApprove={(id) => run(async () => { await api.approveContent(id); await refreshBrandData(brand.id); })}
                  onRepurpose={(id) => run(async () => { await api.repurposeContent(id); await refreshBrandData(brand.id); })}
                />
              </>
            )}

            {tab === "video" && <MediaPanel brandId={brand.id} accounts={accounts} />}
            {tab === "analytics" && <AnalyticsPanel brandId={brand.id} />}
            {tab === "ads" && <AdsPanel brandId={brand.id} />}
            {tab === "inbox" && <InboxPanel brandId={brand.id} />}

            {tab === "groups" && (
              <LeadGroups
                suggestions={groups}
                queue={groupQueue}
                onFind={() => run(async () => { await api.generateGroupSuggestions(brand.id); await refreshBrandData(brand.id); })}
                onUpdate={(id, status) => run(async () => { await api.updateGroupSuggestion(id, status); await refreshBrandData(brand.id); })}
                onQueue={(suggestionId, body) =>
                  run(async () => {
                    await api.queueGroupPost({ brand_id: brand.id, group_suggestion_id: suggestionId, body });
                    await refreshBrandData(brand.id);
                  })
                }
              />
            )}

            {tab === "team" && orgId && <AgencyPanel orgId={orgId} />}
          </main>
        </div>
      )}
    </div>
  );
}

type TabKey =
  | "overview"
  | "content"
  | "video"
  | "analytics"
  | "ads"
  | "inbox"
  | "groups"
  | "team";

const TABS: { key: TabKey; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "content", label: "Content" },
  { key: "video", label: "Reels & Video" },
  { key: "analytics", label: "Analytics" },
  { key: "ads", label: "Ad Manager" },
  { key: "inbox", label: "Inbox & Leads" },
  { key: "groups", label: "Lead Groups" },
  { key: "team", label: "Team" },
];

// Compact inline icons for the sidebar (no icon dependency). 18px, stroke-based.
function NavIcon({ name }: { name: TabKey | "settings" }) {
  const paths: Record<string, string> = {
    overview: "M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z",
    content: "M4 4h16v12H4zM8 20h8",
    video: "M4 5h12v14H4zM16 9l4-2v10l-4-2",
    analytics: "M4 20V10M10 20V4M16 20v-7M22 20H2",
    ads: "M3 11l18-7v16L3 13zM3 11v2",
    inbox: "M4 4h16v16H4zM4 13h4l2 3h4l2-3h4",
    groups: "M9 11a3 3 0 100-6 3 3 0 000 6zM3 20a6 6 0 0112 0M17 11a3 3 0 100-6M16 20a6 6 0 016 0",
    team: "M16 4a4 4 0 010 8M8 4a4 4 0 100 8 4 4 0 000-8zM2 21a6 6 0 0112 0M16 13a6 6 0 016 8",
    settings:
      "M12 15a3 3 0 100-6 3 3 0 000 6zM19 12a7 7 0 00-.1-1l2-1.5-2-3.4-2.3 1a7 7 0 00-1.7-1L14.5 3h-5l-.4 2.6a7 7 0 00-1.7 1l-2.3-1-2 3.4 2 1.5a7 7 0 000 2l-2 1.5 2 3.4 2.3-1a7 7 0 001.7 1l.4 2.6h5l.4-2.6a7 7 0 001.7-1l2.3 1 2-3.4-2-1.5a7 7 0 00.1-1z",
  };
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="shrink-0"
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  );
}

const SECTION_TIP: Record<string, string> = {
  profile: "Fill out your bio, profile photo, link, and contact info on every platform.",
  breadth: "You're not active on enough platforms — connect and post to Facebook + Instagram.",
  consistency: "Post on a steady cadence. Generate a week of content and schedule it.",
  engagement: "Engagement is low — reply in the inbox and post more conversation-starting content.",
  quality: "Lift content quality — use the AI content engine and on-brand reels.",
};

// Audit-driven AI suggestions: surface WHERE the brand is losing ground and what
// to do about it, ranked by the weakest scoring sections.
function AiSuggestions({
  report,
  onRun,
  goTo,
}: {
  report: AuditReport | null;
  onRun: () => void;
  goTo: (tab: TabKey) => void;
}) {
  if (!report) {
    return (
      <section className="card flex flex-col gap-3 p-5">
        <div className="flex items-center gap-2">
          <span className="text-lg">✨</span>
          <h2 className="text-lg font-medium">AI suggestions</h2>
        </div>
        <p className="text-sm text-white/60">
          Run a Presence audit and the AI will pinpoint exactly where you’re
          losing reach and followers — and what to fix first.
        </p>
        <div>
          <button onClick={onRun} className="btn-primary rounded-lg px-4 py-2 text-sm font-medium">
            Run audit
          </button>
        </div>
      </section>
    );
  }

  // Weakest 3 sections = where the brand is losing ground.
  const weak = [...report.sections].sort((a, b) => a.score - b.score).slice(0, 3);
  const ctaFor = (key: string): { label: string; tab: TabKey } => {
    if (key === "engagement") return { label: "Open inbox", tab: "inbox" };
    if (key === "breadth") return { label: "Connect accounts", tab: "overview" };
    if (key === "quality" || key === "consistency") return { label: "Generate content", tab: "content" };
    return { label: "Generate content", tab: "content" };
  };

  return (
    <section className="card flex flex-col gap-4 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">✨</span>
          <h2 className="text-lg font-medium">AI suggestions</h2>
          <span className={`text-sm ${gradeColor(report.overall_grade)}`}>
            Grade {report.overall_grade} · {report.overall_score}/100
          </span>
        </div>
        <button onClick={onRun} className="btn-ghost rounded-lg px-3 py-1.5 text-xs">
          Re-run audit
        </button>
      </div>

      <p className="text-xs uppercase tracking-wider text-white/40">Where you’re losing ground</p>
      <div className="grid gap-3 sm:grid-cols-3">
        {weak.map((s) => {
          const cta = ctaFor(s.key);
          return (
            <div
              key={s.key}
              className="flex flex-col gap-2 rounded-lg border border-white/10 bg-white/[0.03] p-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{s.label}</span>
                <span className={`text-sm font-semibold ${scoreColor(s.score)}`}>{s.score}</span>
              </div>
              <p className="text-xs text-white/55">
                {s.notes || SECTION_TIP[s.key] || "Room to improve here."}
              </p>
              <button
                onClick={() => goTo(cta.tab)}
                className="mt-auto self-start text-xs font-medium text-[#9d92ff] hover:underline"
              >
                {cta.label} →
              </button>
            </div>
          );
        })}
      </div>

      {report.recommendations.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <p className="text-xs uppercase tracking-wider text-white/40">Do this next</p>
          <ul className="flex flex-col gap-1.5 text-sm text-white/70">
            {report.recommendations.slice(0, 5).map((r, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-[#9d92ff]">→</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function GrowthRoadmap({
  hasAudit,
  accountsConnected,
  contentCount,
  groupCount,
  onRunAudit,
  goTo,
}: {
  hasAudit: boolean;
  accountsConnected: boolean;
  contentCount: number;
  groupCount: number;
  onRunAudit: () => void;
  goTo: (tab: TabKey) => void;
}) {
  const steps: {
    label: string;
    desc: string;
    done: boolean;
    cta?: { text: string; onClick: () => void };
  }[] = [
    {
      label: "Tell us about your business",
      desc: "Your profile and website power every recommendation below.",
      done: true,
    },
    {
      label: "Run your AI audit",
      desc: "We read your website, score your social presence, and draft a 7-day content plan — your organic starting line.",
      done: hasAudit,
      cta: hasAudit ? undefined : { text: "Run audit", onClick: onRunAudit },
    },
    {
      label: "Connect Facebook & Instagram",
      desc: "Link your accounts to publish posts and measure real engagement. Use the Connections panel just below.",
      done: accountsConnected,
    },
    {
      label: "Approve your first week of content",
      desc: "Turn one idea into a week of brand-voice posts with hashtags and best-time hints, then approve them.",
      done: contentCount > 0,
      cta: { text: "Go to Content", onClick: () => goTo("content") },
    },
    {
      label: "Find free lead groups",
      desc: "AI surfaces Facebook groups full of your ideal customers — organic leads with zero ad spend.",
      done: groupCount > 0,
      cta: { text: "Find lead groups", onClick: () => goTo("groups") },
    },
    {
      label: "Track your results",
      desc: "Sync insights regularly to prove your organic growth over time.",
      done: false,
      cta: { text: "Open Analytics", onClick: () => goTo("analytics") },
    },
  ];

  const doneCount = steps.filter((s) => s.done).length;
  const pct = Math.round((doneCount / steps.length) * 100);

  return (
    <section className="card flex flex-col gap-4 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-xl font-medium">Your organic growth roadmap</h2>
          <p className="text-sm text-white/50">
            Follow these steps to grow without ad spend — and to prove it works.
          </p>
        </div>
        <span className="text-sm text-white/60">
          {doneCount}/{steps.length} done
        </span>
      </div>

      <div className="h-2 w-full overflow-hidden rounded bg-white/10">
        <div
          className="h-full bg-gradient-to-r from-[#6d5efc] to-[#22d3ee] transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>

      <ol className="flex flex-col gap-2">
        {steps.map((s, i) => (
          <li
            key={s.label}
            className="flex items-start gap-3 rounded-lg border border-white/10 p-3"
          >
            <span
              className={`mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs font-semibold ${
                s.done
                  ? "bg-emerald-500/20 text-emerald-300"
                  : "bg-white/10 text-white/60"
              }`}
            >
              {s.done ? "✓" : i + 1}
            </span>
            <div className="flex flex-1 flex-col gap-0.5">
              <span className={s.done ? "text-white/60 line-through" : "font-medium"}>
                {s.label}
              </span>
              <span className="text-xs text-white/50">{s.desc}</span>
            </div>
            {s.cta && (
              <button
                onClick={s.cta.onClick}
                className="btn-ghost shrink-0 self-center rounded-lg px-3 py-1.5 text-xs"
              >
                {s.cta.text}
              </button>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}

function Connections({
  brand,
  accounts,
  onConnect,
}: {
  brand: Brand;
  accounts: SocialAccount[];
  onConnect: () => void;
}) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-xl font-medium">{brand.name} — connections</h2>
      {accounts.length === 0 ? (
        <p className="text-sm text-white/60">No accounts connected yet.</p>
      ) : (
        <ul className="flex flex-col gap-1 text-sm">
          {accounts.map((a) => (
            <li key={a.id} className="flex items-center gap-2">
              <span className="rounded bg-white/10 px-2 py-0.5 text-xs">
                {a.provider === "instagram" ? "Instagram" : "Facebook"}
              </span>
              {a.display_name} — {a.status}
            </li>
          ))}
        </ul>
      )}
      <div className="flex gap-2">
        <button
          onClick={() => onConnect()}
          className="btn-primary rounded-lg px-4 py-2 text-sm font-medium"
        >
          Connect Facebook &amp; Instagram
        </button>
      </div>
    </section>
  );
}

function Composer({
  accounts,
  onCreate,
}: {
  accounts: SocialAccount[];
  onCreate: (input: {
    body: string;
    target_account_ids: string[];
    scheduled_time?: string | null;
  }) => void | Promise<void>;
}) {
  const [body, setBody] = useState("");
  const [targets, setTargets] = useState<string[]>([]);
  const [scheduledAt, setScheduledAt] = useState("");
  const [busy, setBusy] = useState(false);

  function toggle(id: string) {
    setTargets((t) => (t.includes(id) ? t.filter((x) => x !== id) : [...t, id]));
  }

  // A draft only needs body text. Scheduling to publish needs a target account.
  const needsTarget = !!scheduledAt;
  const disabled = !body || busy || (needsTarget && targets.length === 0);

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-xl font-medium">Compose</h2>
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="What's happening?"
        rows={3}
        className="rounded-md border border-white/15 bg-transparent px-3 py-2"
      />
      {accounts.length > 0 && (
        <div className="flex flex-wrap gap-3 text-sm">
          {accounts.map((a) => (
            <label key={a.id} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={targets.includes(a.id)}
                onChange={() => toggle(a.id)}
              />
              {a.display_name}
            </label>
          ))}
        </div>
      )}
      <div className="flex items-center gap-3 text-sm">
        <label className="flex items-center gap-2">
          Schedule (optional)
          <input
            type="datetime-local"
            value={scheduledAt}
            onChange={(e) => setScheduledAt(e.target.value)}
            className="rounded-md border border-white/15 bg-transparent px-2 py-1"
          />
        </label>
        <button
          disabled={disabled}
          onClick={async () => {
            setBusy(true);
            try {
              await onCreate({
                body,
                target_account_ids: targets,
                scheduled_time: scheduledAt
                  ? new Date(scheduledAt).toISOString()
                  : null,
              });
              setBody("");
              setTargets([]);
              setScheduledAt("");
            } finally {
              setBusy(false);
            }
          }}
          className="rounded-md bg-white px-4 py-2 font-medium text-black disabled:opacity-40"
        >
          {busy ? "Saving…" : scheduledAt ? "Schedule" : "Save draft"}
        </button>
      </div>
      {needsTarget && targets.length === 0 && (
        <p className="text-xs text-white/50">
          Pick at least one account above to schedule. You can also save it as a draft
          (clear the schedule) and choose accounts later.
        </p>
      )}
    </section>
  );
}

function GenerateWeek({ onGenerate }: { onGenerate: (prompt: string) => void }) {
  const [prompt, setPrompt] = useState("");
  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-xl font-medium">Generate content</h2>
      <p className="text-xs text-white/50">
        One idea → a week of brand-voice drafts with hashtags and best-time hints.
      </p>
      <div className="flex gap-2">
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g. fall menu launch, a photo, a link…"
          className="flex-1 rounded-md border border-white/15 bg-transparent px-3 py-2 text-sm"
        />
        <button
          onClick={() => onGenerate(prompt)}
          className="rounded-md bg-white px-4 py-2 text-sm font-medium text-black"
        >
          Generate a week
        </button>
      </div>
    </section>
  );
}

// A weekly calendar view of scheduled content — see the whole week's plan at a
// glance instead of a lone date field.
function WeeklyPlanner({ items }: { items: ContentItem[] }) {
  const [weekOffset, setWeekOffset] = useState(0);

  const DAY = 86_400_000;
  const now = new Date();
  // Monday of the target week (local time).
  const monday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const dow = (monday.getDay() + 6) % 7; // 0 = Monday
  monday.setDate(monday.getDate() - dow + weekOffset * 7);

  const days = Array.from({ length: 7 }, (_, i) => new Date(monday.getTime() + i * DAY));
  const sameDay = (a: Date, b: Date) =>
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate();

  const scheduled = items.filter((it) => it.scheduled_time);
  const unscheduledDrafts = items.filter(
    (it) => !it.scheduled_time && it.status === "draft",
  );

  const forDay = (d: Date) =>
    scheduled
      .filter((it) => sameDay(new Date(it.scheduled_time as string), d))
      .sort(
        (a, b) =>
          new Date(a.scheduled_time as string).getTime() -
          new Date(b.scheduled_time as string).getTime(),
      );

  const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const monthDay = (d: Date) =>
    d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  const time = (iso: string) =>
    new Date(iso).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });

  const rangeLabel = `${monthDay(days[0])} – ${monthDay(days[6])}`;
  const statusDot: Record<string, string> = {
    draft: "bg-white/40",
    scheduled: "bg-amber-400",
    publishing: "bg-blue-400",
    published: "bg-emerald-400",
    failed: "bg-red-400",
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-medium">Weekly planner</h2>
          <span className="text-sm text-white/50">{rangeLabel}</span>
        </div>
        <div className="flex items-center gap-1 text-sm">
          <button
            onClick={() => setWeekOffset((w) => w - 1)}
            className="btn-ghost rounded-md px-2.5 py-1"
            aria-label="Previous week"
          >
            ‹
          </button>
          <button
            onClick={() => setWeekOffset(0)}
            className="btn-ghost rounded-md px-3 py-1 text-xs"
          >
            Today
          </button>
          <button
            onClick={() => setWeekOffset((w) => w + 1)}
            className="btn-ghost rounded-md px-2.5 py-1"
            aria-label="Next week"
          >
            ›
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
        {days.map((d, i) => {
          const dayItems = forDay(d);
          const isToday = sameDay(d, now);
          return (
            <div
              key={i}
              className={`flex min-h-28 flex-col gap-1.5 rounded-lg border p-2 ${
                isToday ? "border-[#6d5efc]/60 bg-[#6d5efc]/5" : "border-white/10 bg-white/[0.02]"
              }`}
            >
              <div className="flex items-baseline justify-between">
                <span className={`text-xs font-medium ${isToday ? "text-[#9d92ff]" : "text-white/70"}`}>
                  {DOW[i]}
                </span>
                <span className="text-[10px] text-white/40">{d.getDate()}</span>
              </div>
              {dayItems.length === 0 ? (
                <span className="text-[10px] text-white/25">—</span>
              ) : (
                dayItems.map((it) => (
                  <div
                    key={it.id}
                    title={it.body}
                    className="flex flex-col gap-0.5 rounded-md bg-white/[0.04] p-1.5"
                  >
                    <div className="flex items-center gap-1">
                      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${statusDot[it.status] ?? "bg-white/40"}`} />
                      <span className="text-[10px] text-white/50">
                        {time(it.scheduled_time as string)}
                      </span>
                      {it.media_urls?.[0] && <span className="text-[10px]">🖼</span>}
                    </div>
                    <span className="line-clamp-2 text-[11px] text-white/80">{it.body}</span>
                  </div>
                ))
              )}
            </div>
          );
        })}
      </div>

      {unscheduledDrafts.length > 0 && (
        <p className="text-xs text-white/50">
          {unscheduledDrafts.length} unscheduled draft{unscheduledDrafts.length > 1 ? "s" : ""} —
          set a schedule time when composing to place them on the planner.
        </p>
      )}
    </section>
  );
}

function ContentList({
  items,
  onPublish,
  onApprove,
  onRepurpose,
}: {
  items: ContentItem[];
  onPublish: (id: string) => void;
  onApprove: (id: string) => void;
  onRepurpose: (id: string) => void;
}) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-xl font-medium">Content</h2>
      {items.length === 0 ? (
        <p className="text-sm text-white/60">Nothing yet.</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex items-start justify-between gap-4 rounded-md border border-white/10 p-3"
            >
              <div className="flex min-w-0 items-start gap-3">
                {item.media_urls?.[0] && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={item.media_urls[0]}
                    alt="AI-generated post image"
                    className="h-16 w-16 shrink-0 rounded-md object-cover"
                  />
                )}
                <div className="flex min-w-0 flex-col gap-1">
                  <span className="text-sm">{item.body}</span>
                  <span className="text-xs text-white/50">
                    {item.content_type} · {item.status}
                    {item.media_urls?.[0] ? " · 🖼 image" : ""}
                    {item.approved ? " · ✓ approved" : ""}
                    {item.suggested_time ? ` · best ~${item.suggested_time}` : ""}
                    {` · ${item.targets.length} target(s)`}
                  </span>
                </div>
              </div>
              <div className="flex shrink-0 flex-col gap-1">
                {!item.approved && (
                  <button
                    onClick={() => onApprove(item.id)}
                    className="rounded-md border border-white/20 px-3 py-1 text-sm hover:bg-white/5"
                  >
                    Approve
                  </button>
                )}
                <button
                  onClick={() => onRepurpose(item.id)}
                  className="rounded-md border border-white/10 px-3 py-1 text-xs text-white/60 hover:bg-white/5"
                >
                  Repurpose
                </button>
                {(item.status === "draft" || item.status === "failed") && (
                  <button
                    onClick={() => onPublish(item.id)}
                    className="rounded-md border border-white/20 px-3 py-1 text-sm hover:bg-white/5"
                  >
                    Publish now
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function LeadGroups({
  suggestions,
  queue,
  onFind,
  onUpdate,
  onQueue,
}: {
  suggestions: GroupSuggestion[];
  queue: GroupPostTask[];
  onFind: () => void;
  onUpdate: (id: string, status: GroupSuggestion["status"]) => void;
  onQueue: (suggestionId: string, body: string) => void;
}) {
  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-medium">Lead groups</h2>
        <button
          onClick={onFind}
          className="rounded-md bg-white px-4 py-2 text-sm font-medium text-black"
        >
          Find lead groups
        </button>
      </div>
      <p className="text-xs text-white/50">
        AI-suggested Facebook groups to join for leads. Search the keyword on
        Facebook to find each group. Queued posts are handled locally by the
        Presence browser extension — never posted from our servers.
      </p>
      {suggestions.length === 0 ? (
        <p className="text-sm text-white/60">
          No suggestions yet — click “Find lead groups”.
        </p>
      ) : (
        <ul className="flex flex-col gap-3">
          {suggestions
            .filter((s) => s.status !== "dismissed")
            .map((s) => (
              <SuggestionCard
                key={s.id}
                s={s}
                onUpdate={onUpdate}
                onQueue={onQueue}
              />
            ))}
        </ul>
      )}
      {queue.length > 0 && (
        <div className="flex flex-col gap-1">
          <h3 className="text-sm font-medium text-white/80">
            Queued group posts (Tier B)
          </h3>
          <ul className="flex flex-col gap-1 text-xs text-white/60">
            {queue.map((t) => (
              <li key={t.id}>
                {t.status} · {t.body.slice(0, 60)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function SuggestionCard({
  s,
  onUpdate,
  onQueue,
}: {
  s: GroupSuggestion;
  onUpdate: (id: string, status: GroupSuggestion["status"]) => void;
  onQueue: (suggestionId: string, body: string) => void;
}) {
  const [body, setBody] = useState("");
  const searchUrl = `https://www.facebook.com/search/groups/?q=${encodeURIComponent(
    s.search_keyword,
  )}`;
  return (
    <li className="flex flex-col gap-2 rounded-md border border-white/10 p-3">
      <div className="flex items-center justify-between gap-3">
        <span className="flex items-center gap-2 font-medium">
          {s.name}
          {s.group_url && (
            <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-emerald-400">
              Real group
            </span>
          )}
        </span>
        <span className="text-xs text-white/50">
          relevance {s.relevance_score} · leads {s.lead_quality_score}
          {s.estimated_size ? ` · ${s.estimated_size}` : ""}
        </span>
      </div>
      {s.rationale && <p className="text-sm text-white/70">{s.rationale}</p>}
      <div className="flex flex-wrap items-center gap-2 text-sm">
        {s.group_url ? (
          <a
            href={s.group_url}
            target="_blank"
            rel="noreferrer"
            className="rounded-md border border-white/20 px-3 py-1 hover:bg-white/5"
          >
            Open group ↗
          </a>
        ) : (
          <a
            href={searchUrl}
            target="_blank"
            rel="noreferrer"
            className="rounded-md border border-white/20 px-3 py-1 hover:bg-white/5"
          >
            Search on Facebook
          </a>
        )}
        {s.status === "tracked" ? (
          <span className="text-xs text-emerald-400">Tracked</span>
        ) : (
          <button
            onClick={() => onUpdate(s.id, "tracked")}
            className="rounded-md border border-white/20 px-3 py-1 hover:bg-white/5"
          >
            Track
          </button>
        )}
        <button
          onClick={() => onUpdate(s.id, "dismissed")}
          className="rounded-md border border-white/10 px-3 py-1 text-white/60 hover:bg-white/5"
        >
          Dismiss
        </button>
      </div>
      {s.status === "tracked" && (
        <div className="flex gap-2">
          <input
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder={s.suggested_post_angle || "Write a post for this group…"}
            className="flex-1 rounded-md border border-white/15 bg-transparent px-3 py-1 text-sm"
          />
          <button
            disabled={!body}
            onClick={() => {
              onQueue(s.id, body);
              setBody("");
            }}
            className="rounded-md bg-white px-3 py-1 text-sm font-medium text-black disabled:opacity-40"
          >
            Queue post
          </button>
        </div>
      )}
    </li>
  );
}

function gradeColor(grade: string): string {
  if (grade === "A" || grade === "B") return "text-emerald-400";
  if (grade === "C" || grade === "D") return "text-amber-400";
  return "text-red-400";
}

function scoreColor(score: number): string {
  if (score >= 70) return "text-emerald-400";
  if (score >= 40) return "text-amber-400";
  return "text-red-400";
}

function AuditPanel({
  report,
  onRun,
  onSeed,
}: {
  report: AuditReport | null;
  onRun: () => void;
  onSeed: () => void;
}) {
  return (
    <section className="flex flex-col gap-3 rounded-md border border-white/10 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-medium">Presence audit</h2>
        <button
          onClick={onRun}
          className="rounded-md bg-white px-4 py-2 text-sm font-medium text-black"
        >
          {report ? "Re-run audit" : "Run audit"}
        </button>
      </div>

      {!report ? (
        <p className="text-sm text-white/60">
          Audit this brand’s social presence — get a scored report and a ready-to-go
          first week of content.
        </p>
      ) : (
        <>
          <div className="flex items-baseline gap-3">
            <span className={`text-5xl font-bold ${gradeColor(report.overall_grade)}`}>
              {report.overall_grade}
            </span>
            <span className="text-white/60">{report.overall_score}/100 overall</span>
          </div>

          <div className="flex flex-col gap-2">
            {report.sections.map((s) => (
              <div key={s.key} className="flex items-center gap-3">
                <span className="w-40 text-sm text-white/70">{s.label}</span>
                <div className="h-2 flex-1 overflow-hidden rounded bg-white/10">
                  <div
                    className="h-full bg-white/70"
                    style={{ width: `${s.score}%` }}
                  />
                </div>
                <span className="w-10 text-right text-xs text-white/50">{s.score}</span>
              </div>
            ))}
          </div>

          {report.strategy_brief && (
            <p className="text-sm text-white/70">{report.strategy_brief}</p>
          )}

          {report.recommendations.length > 0 && (
            <ul className="list-disc pl-5 text-sm text-white/60">
              {report.recommendations.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          )}

          <div>
            <button
              onClick={onSeed}
              className="rounded-md border border-white/20 px-4 py-2 text-sm hover:bg-white/5"
            >
              Start running my account → seed first week
            </button>
          </div>
        </>
      )}
    </section>
  );
}

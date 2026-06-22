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
        <>
          <nav className="flex flex-wrap gap-1 border-b border-white/10 pb-px">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`rounded-t-lg px-4 py-2 text-sm transition ${
                  tab === t.key
                    ? "border-b-2 border-[#6d5efc] font-medium text-white"
                    : "text-white/55 hover:text-white"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>

          <div className="flex flex-col gap-6">
            {tab === "overview" && (
              <>
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
                  onConnect={(mode) =>
                    run(async () => {
                      if (mode === "mock") {
                        await api.connectMock(brand.id);
                        await refreshBrandData(brand.id);
                      } else {
                        const { authorize_url } = await api.startOAuth(brand.id);
                        window.location.href = authorize_url;
                      }
                    })
                  }
                />
              </>
            )}

            {tab === "content" && (
              <>
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

            {tab === "video" && <MediaPanel brandId={brand.id} />}
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
          </div>
        </>
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
  { key: "video", label: "AI Video" },
  { key: "analytics", label: "Analytics" },
  { key: "ads", label: "Ads" },
  { key: "inbox", label: "Inbox" },
  { key: "groups", label: "Lead Groups" },
  { key: "team", label: "Team" },
];

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
  onConnect: (mode: "oauth" | "mock") => void;
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
          onClick={() => onConnect("oauth")}
          className="rounded-md border border-white/20 px-4 py-2 text-sm hover:bg-white/5"
        >
          Connect Facebook &amp; Instagram
        </button>
        <button
          onClick={() => onConnect("mock")}
          className="rounded-md border border-white/10 px-4 py-2 text-sm text-white/60 hover:bg-white/5"
        >
          Dev: connect mock accounts
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
  }) => void;
}) {
  const [body, setBody] = useState("");
  const [targets, setTargets] = useState<string[]>([]);
  const [scheduledAt, setScheduledAt] = useState("");

  function toggle(id: string) {
    setTargets((t) => (t.includes(id) ? t.filter((x) => x !== id) : [...t, id]));
  }

  const disabled = !body || targets.length === 0;

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
          onClick={() => {
            onCreate({
              body,
              target_account_ids: targets,
              scheduled_time: scheduledAt
                ? new Date(scheduledAt).toISOString()
                : null,
            });
            setBody("");
            setTargets([]);
            setScheduledAt("");
          }}
          className="rounded-md bg-white px-4 py-2 font-medium text-black disabled:opacity-40"
        >
          {scheduledAt ? "Schedule" : "Save draft"}
        </button>
      </div>
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
              <div className="flex flex-col gap-1">
                <span className="text-sm">{item.body}</span>
                <span className="text-xs text-white/50">
                  {item.content_type} · {item.status}
                  {item.approved ? " · ✓ approved" : ""}
                  {item.suggested_time ? ` · best ~${item.suggested_time}` : ""}
                  {` · ${item.targets.length} target(s)`}
                </span>
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
        <span className="font-medium">{s.name}</span>
        <span className="text-xs text-white/50">
          relevance {s.relevance_score} · leads {s.lead_quality_score}
          {s.estimated_size ? ` · ${s.estimated_size}` : ""}
        </span>
      </div>
      {s.rationale && <p className="text-sm text-white/70">{s.rationale}</p>}
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <a
          href={searchUrl}
          target="_blank"
          rel="noreferrer"
          className="rounded-md border border-white/20 px-3 py-1 hover:bg-white/5"
        >
          Search on Facebook
        </a>
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

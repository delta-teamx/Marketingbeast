"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  AuditReport,
  Brand,
  ContentItem,
  GroupPostTask,
  GroupSuggestion,
  SocialAccount,
} from "@presence/shared";
import { api } from "@/lib/api-client";
import { AnalyticsPanel } from "@/components/analytics-panel";
import { InboxPanel } from "@/components/inbox-panel";

export function Workspace() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [brand, setBrand] = useState<Brand | null>(null);
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [groups, setGroups] = useState<GroupSuggestion[]>([]);
  const [groupQueue, setGroupQueue] = useState<GroupPostTask[]>([]);
  const [audit, setAudit] = useState<AuditReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
    (async () => {
      try {
        await api.me(); // provision personal org
        const orgs = await api.listOrgs();
        const org = orgs[0];
        setOrgId(org.id);
        const brands = await api.listBrands(org.id);
        if (brands[0]) {
          setBrand(brands[0]);
          await refreshBrandData(brands[0].id);
        }
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, [refreshBrandData]);

  async function run(fn: () => Promise<void>) {
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (loading) return <p className="text-white/60">Loading workspace…</p>;

  return (
    <div className="flex flex-col gap-8">
      {error && (
        <p className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {!brand ? (
        <CreateBrand
          onCreate={(name) =>
            run(async () => {
              if (!orgId) return;
              const b = await api.createBrand(orgId, name);
              setBrand(b);
              await refreshBrandData(b.id);
            })
          }
        />
      ) : (
        <>
          <AuditPanel
            report={audit}
            onRun={() =>
              run(async () => {
                await api.runAudit(brand.id);
                await refreshBrandData(brand.id);
              })
            }
            onSeed={() =>
              run(async () => {
                await api.seedFirstWeek(brand.id);
                await refreshBrandData(brand.id);
              })
            }
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
          <GenerateWeek
            onGenerate={(prompt) =>
              run(async () => {
                await api.generateContent(brand.id, prompt);
                await refreshBrandData(brand.id);
              })
            }
          />
          <Composer
            accounts={accounts}
            onCreate={(input) =>
              run(async () => {
                await api.createContent({ ...input, brand_id: brand.id });
                await refreshBrandData(brand.id);
              })
            }
          />
          <AnalyticsPanel brandId={brand.id} />
          <InboxPanel brandId={brand.id} />
          <ContentList
            items={content}
            onPublish={(id) =>
              run(async () => {
                await api.publishNow(id);
                await refreshBrandData(brand.id);
              })
            }
            onApprove={(id) =>
              run(async () => {
                await api.approveContent(id);
                await refreshBrandData(brand.id);
              })
            }
            onRepurpose={(id) =>
              run(async () => {
                await api.repurposeContent(id);
                await refreshBrandData(brand.id);
              })
            }
          />
          <LeadGroups
            suggestions={groups}
            queue={groupQueue}
            onFind={() =>
              run(async () => {
                await api.generateGroupSuggestions(brand.id);
                await refreshBrandData(brand.id);
              })
            }
            onUpdate={(id, status) =>
              run(async () => {
                await api.updateGroupSuggestion(id, status);
                await refreshBrandData(brand.id);
              })
            }
            onQueue={(suggestionId, body) =>
              run(async () => {
                await api.queueGroupPost({
                  brand_id: brand.id,
                  group_suggestion_id: suggestionId,
                  body,
                });
                await refreshBrandData(brand.id);
              })
            }
          />
        </>
      )}
    </div>
  );
}

function CreateBrand({ onCreate }: { onCreate: (name: string) => void }) {
  const [name, setName] = useState("");
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-xl font-medium">Create your first brand</h2>
      <div className="flex gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Acme Coffee"
          className="flex-1 rounded-md border border-white/15 bg-transparent px-3 py-2"
        />
        <button
          onClick={() => name && onCreate(name)}
          className="rounded-md bg-white px-4 py-2 font-medium text-black"
        >
          Create
        </button>
      </div>
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

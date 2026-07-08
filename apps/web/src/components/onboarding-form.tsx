"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { OnboardingInput } from "@presence/shared";
import { api } from "@/lib/api-client";

const GOALS = [
  ["more_leads", "More leads"],
  ["brand_awareness", "Brand awareness"],
  ["more_sales", "More sales"],
  ["appointments", "Bookings / appointments"],
];
const FREQ = [
  ["rarely", "Rarely"],
  ["weekly", "Weekly"],
  ["few_per_week", "A few times a week"],
  ["daily", "Daily"],
];
const BUDGET = [
  ["under_100", "Under $100/mo"],
  ["100_500", "$100–$500/mo"],
  ["500_2000", "$500–$2,000/mo"],
  ["2000_plus", "$2,000+/mo"],
];

export function OnboardingForm({
  embedded = false,
  onDone,
}: {
  /** When embedded in the dashboard, drop the full-screen wrapper. */
  embedded?: boolean;
  /** Called after a successful submit instead of navigating. */
  onDone?: () => void | Promise<void>;
} = {}) {
  const router = useRouter();
  const [form, setForm] = useState<OnboardingInput>({
    business_name: "",
    website_url: "",
    industry: "",
    goal: "more_leads",
    platforms: ["facebook", "instagram"],
    posting_frequency: "few_per_week",
    monthly_budget: "100_500",
    biggest_challenge: "",
    target_audience: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [pitch, setPitch] = useState("");
  const [strategy, setStrategy] = useState<string | null>(null);
  const [drafting, setDrafting] = useState(false);

  async function draftStrategy() {
    if (!pitch) return;
    setError(null);
    setDrafting(true);
    try {
      const s = await api.conversationalOnboarding(pitch);
      setStrategy(s.summary);
      setForm((f) => ({ ...f, industry: s.industry, goal: s.suggested_goal }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDrafting(false);
    }
  }

  function set<K extends keyof OnboardingInput>(key: K, value: OnboardingInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }
  function togglePlatform(p: string) {
    setForm((f) => ({
      ...f,
      platforms: f.platforms.includes(p)
        ? f.platforms.filter((x) => x !== p)
        : [...f.platforms, p],
    }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.submitOnboarding(form);
      if (onDone) {
        await onDone();
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const field = "rounded-lg border border-white/15 bg-transparent px-3 py-2 text-sm";

  // NOTE: do not define the wrapper as a component inside render — a new
  // component identity each render remounts the whole form and drops input
  // focus on every keystroke (on mobile that makes the spacebar scroll the page
  // instead of typing a space). Build stable content and wrap it conditionally.
  const content = (
    <>
      <div>
        <h1 className="text-3xl font-bold">Tell us about your business</h1>
        <p className="mt-2 text-sm text-white/60">
          A minute now lets Presence read your website and tailor your audit,
          brand voice, and a week of content — the foundation of your free
          (organic) growth plan.
        </p>
      </div>

      <div className="card flex flex-col gap-2 p-4">
        <label className="text-sm text-white/70">
          Describe your business in a sentence
        </label>
        <textarea
          value={pitch}
          onChange={(e) => setPitch(e.target.value)}
          rows={2}
          placeholder="e.g. I run a CrossFit gym and want more local members"
          className="rounded-lg border border-white/15 bg-transparent px-3 py-2 text-sm"
        />
        <button
          type="button"
          disabled={drafting || !pitch}
          onClick={draftStrategy}
          className="btn-ghost w-fit rounded-lg px-3 py-1.5 text-sm disabled:opacity-50"
        >
          {drafting ? "Thinking…" : "✨ Draft my strategy"}
        </button>
        {strategy && <p className="text-sm text-white/70">{strategy}</p>}
      </div>

      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Business name
          <input
            required
            value={form.business_name}
            onChange={(e) => set("business_name", e.target.value)}
            className={field}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Website URL
          <input
            type="url"
            placeholder="https://yourbusiness.com"
            value={form.website_url ?? ""}
            onChange={(e) => set("website_url", e.target.value)}
            className={field}
          />
          <span className="text-xs text-white/40">
            We read your site to detect your niche and write on-brand content. No
            site yet? Leave blank — you can add it later.
          </span>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Industry
          <input
            placeholder="e.g. coffee shop, gym, auto dealer"
            value={form.industry ?? ""}
            onChange={(e) => set("industry", e.target.value)}
            className={field}
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Primary goal
          <select
            value={form.goal ?? ""}
            onChange={(e) => set("goal", e.target.value)}
            className={field}
          >
            {GOALS.map(([v, l]) => (
              <option key={v} value={v} className="bg-[#0e0e16]">
                {l}
              </option>
            ))}
          </select>
        </label>

        <div className="flex flex-col gap-1 text-sm">
          Platforms
          <div className="flex gap-4">
            {["facebook", "instagram"].map((p) => (
              <label key={p} className="flex items-center gap-2 capitalize">
                <input
                  type="checkbox"
                  checked={form.platforms.includes(p)}
                  onChange={() => togglePlatform(p)}
                />
                {p}
              </label>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <label className="flex flex-col gap-1 text-sm">
            Posting cadence
            <select
              value={form.posting_frequency ?? ""}
              onChange={(e) => set("posting_frequency", e.target.value)}
              className={field}
            >
              {FREQ.map(([v, l]) => (
                <option key={v} value={v} className="bg-[#0e0e16]">
                  {l}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Marketing budget
            <select
              value={form.monthly_budget ?? ""}
              onChange={(e) => set("monthly_budget", e.target.value)}
              className={field}
            >
              {BUDGET.map(([v, l]) => (
                <option key={v} value={v} className="bg-[#0e0e16]">
                  {l}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="flex flex-col gap-1 text-sm">
          Biggest marketing challenge
          <textarea
            rows={2}
            value={form.biggest_challenge ?? ""}
            onChange={(e) => set("biggest_challenge", e.target.value)}
            className={field}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Who are your customers?
          <textarea
            rows={2}
            value={form.target_audience ?? ""}
            onChange={(e) => set("target_audience", e.target.value)}
            className={field}
          />
        </label>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={loading || !form.business_name}
          className="btn-primary rounded-xl px-5 py-3 font-semibold disabled:opacity-50"
        >
          {loading ? "Setting up…" : "Create my workspace →"}
        </button>
      </form>
    </>
  );

  return embedded ? (
    <div className="flex flex-col gap-6">{content}</div>
  ) : (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center gap-6 px-6 py-12">
      {content}
    </main>
  );
}

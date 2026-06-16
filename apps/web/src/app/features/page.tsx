import Link from "next/link";
import { Footer, Nav } from "@/components/marketing";
import { Reveal } from "@/components/ui/reveal";
import {
  AdsVisual,
  AnalyticsVisual,
  AuditVisual,
  GroupsVisual,
  InboxVisual,
  PublishVisual,
  VideoVisual,
} from "@/components/marketing/visuals";

export const metadata = { title: "Features — Presence" };

const FEATURES = [
  ["AI Presence Audit", "Score any business from a URL, with an action plan and a seeded first week of content.", <AuditVisual key="a" />],
  ["Publish & schedule", "Manage Facebook Pages and Instagram from one portal; auto-publish on a visual calendar.", <PublishVisual key="p" />],
  ["AI video & reels", "Idea → script → UGC-style render → publish to FB, IG, and groups.", <VideoVisual key="v" />],
  ["Meta Ads Manager", "Launch campaigns with 10–20 creatives; AI tells you what to pause and scale.", <AdsVisual key="d" />],
  ["Analytics & reports", "Cross-account dashboard plus branded weekly/monthly reports and competitor tracking.", <AnalyticsVisual key="n" />],
  ["AI group matcher", "Niche-matched Facebook groups, buyer-intent ranked, with account-safe posting.", <GroupsVisual key="g" />],
  ["Inbox & leads", "Unified comments + DMs, automatic lead detection, AI-drafted replies.", <InboxVisual key="i" />],
] as const;

export default function FeaturesPage() {
  return (
    <div className="min-h-screen">
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold">One platform, your whole social engine</h1>
          <p className="mx-auto mt-4 max-w-2xl text-white/60">
            Audit, create, publish, advertise, analyze, and find leads — across
            Facebook and Instagram, tuned to your industry.
          </p>
        </div>

        <div className="mt-14 grid gap-6 md:grid-cols-2">
          {FEATURES.map(([title, body, visual], i) => (
            <Reveal key={title} delay={(i % 2) * 0.06}>
              <div className="card flex h-full flex-col gap-4 p-6">
                <div>
                  <h3 className="text-xl font-semibold">{title}</h3>
                  <p className="mt-2 text-sm text-white/60">{body}</p>
                </div>
                <div className="mt-auto">{visual}</div>
              </div>
            </Reveal>
          ))}
        </div>

        <div className="mt-16 text-center">
          <Link href="/signup" className="btn-primary inline-block rounded-xl px-8 py-4 text-lg font-semibold">
            Audit my business free
          </Link>
        </div>
      </main>
      <Footer />
    </div>
  );
}

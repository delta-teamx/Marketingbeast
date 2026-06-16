import Link from "next/link";
import type { ReactNode } from "react";
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

export function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/5 bg-[#07070b]/70 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-[#6d5efc] to-[#22d3ee] text-sm">
            P
          </span>
          Presence
        </Link>
        <nav className="hidden items-center gap-8 text-sm text-white/70 md:flex">
          <Link href="/features" className="hover:text-white">Features</Link>
          <a href="#how" className="hover:text-white">How it works</a>
          <Link href="/pricing" className="hover:text-white">Pricing</Link>
        </nav>
        <div className="flex items-center gap-3 text-sm">
          <Link href="/login" className="rounded-lg px-3 py-2 text-white/80 hover:text-white">
            Sign in
          </Link>
          <Link href="/signup" className="btn-primary rounded-lg px-4 py-2 font-medium">
            Get started
          </Link>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="hero-glow pointer-events-none absolute inset-0" />
      <div className="grid-fade pointer-events-none absolute inset-0 opacity-40" />
      <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-6 pb-20 pt-20 lg:grid-cols-2">
        <div>
          <Reveal>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/70">
              <span className="h-1.5 w-1.5 rounded-full bg-[#22d3ee]" />
              AI marketing employee for Facebook &amp; Instagram
            </span>
          </Reveal>
          <Reveal delay={0.05}>
            <h1 className="mt-6 text-5xl font-extrabold leading-[1.05] sm:text-6xl">
              Be everywhere.
              <br />
              <span className="gradient-text">Lift no finger.</span>
            </h1>
          </Reveal>
          <Reveal delay={0.1}>
            <p className="mt-6 max-w-xl text-lg text-white/70">
              Enter your business URL. Presence audits your social presence, then
              generates, schedules, and publishes content — even AI videos — across
              Facebook and Instagram, runs your ads, and finds new customers in
              groups. Built for owners and agencies.
            </p>
          </Reveal>
          <Reveal delay={0.15}>
            <div className="mt-9 flex flex-wrap items-center gap-4">
              <Link href="/signup" className="btn-primary rounded-xl px-7 py-3.5 font-semibold">
                Audit my business free
              </Link>
              <Link href="/features" className="btn-ghost rounded-xl px-7 py-3.5 font-medium">
                Explore features
              </Link>
            </div>
          </Reveal>
          <Reveal delay={0.2}>
            <p className="mt-4 text-xs text-white/40">
              No credit card · Official Meta API · Your accounts stay yours
            </p>
          </Reveal>
        </div>
        <Reveal delay={0.15} className="animate-float">
          <AuditVisual />
        </Reveal>
      </div>
      <LogoMarquee />
    </section>
  );
}

function LogoMarquee() {
  const items = [
    "Facebook Pages", "Instagram", "Meta Ads Manager", "Reels & Video",
    "Facebook Groups", "Messenger Inbox", "Analytics", "White-label",
  ];
  return (
    <div className="relative overflow-hidden border-y border-white/5 bg-white/[0.02] py-4">
      <div className="flex w-max animate-marquee gap-10 px-6 text-sm text-white/40">
        {[...items, ...items].map((t, i) => (
          <span key={i} className="whitespace-nowrap">◇ {t}</span>
        ))}
      </div>
    </div>
  );
}

const STATS = [
  ["80%", "of the work, automated"],
  ["1 URL", "to a running engine"],
  ["FB + IG", "publish, ads & inbox"],
  ["∞", "brands & clients"],
];

function Stats() {
  return (
    <section className="mx-auto grid max-w-6xl grid-cols-2 gap-6 px-6 py-14 md:grid-cols-4">
      {STATS.map(([big, small], i) => (
        <Reveal key={small} delay={i * 0.05}>
          <div className="text-center">
            <div className="gradient-text text-3xl font-bold">{big}</div>
            <div className="mt-1 text-sm text-white/55">{small}</div>
          </div>
        </Reveal>
      ))}
    </section>
  );
}

function FeatureRow({
  eyebrow,
  title,
  body,
  bullets,
  visual,
  reverse,
}: {
  eyebrow: string;
  title: string;
  body: string;
  bullets: string[];
  visual: ReactNode;
  reverse?: boolean;
}) {
  return (
    <div className="mx-auto grid max-w-6xl items-center gap-10 px-6 py-14 lg:grid-cols-2">
      <Reveal className={reverse ? "lg:order-2" : ""}>
        <div className="gradient-text text-sm font-semibold uppercase tracking-wider">
          {eyebrow}
        </div>
        <h3 className="mt-2 text-3xl font-bold">{title}</h3>
        <p className="mt-3 text-white/60">{body}</p>
        <ul className="mt-4 flex flex-col gap-2 text-sm text-white/70">
          {bullets.map((b) => (
            <li key={b} className="flex items-center gap-2">
              <span className="text-[#22d3ee]">✓</span> {b}
            </li>
          ))}
        </ul>
      </Reveal>
      <Reveal delay={0.1} className={reverse ? "lg:order-1" : ""}>
        {visual}
      </Reveal>
    </div>
  );
}

function Features() {
  return (
    <section id="features" className="border-t border-white/5">
      <div className="mx-auto max-w-6xl px-6 pt-16 text-center">
        <Reveal>
          <h2 className="text-4xl font-bold">Everything your social marketing needs</h2>
          <p className="mx-auto mt-4 max-w-2xl text-white/60">
            One platform replaces the audit, the content team, the video editor, the
            ad buyer, and the reporting deck — tuned to your industry.
          </p>
        </Reveal>
      </div>

      <FeatureRow
        eyebrow="Presence Audit"
        title="Audit any business in minutes"
        body="Drop a website URL and get a scored report — profile, consistency, content quality, and gaps vs. your category — plus a ready-to-run first week of content."
        bullets={["Letter-grade score", "Action plan & strategy brief", "Seeds your content calendar"]}
        visual={<AuditVisual />}
      />
      <FeatureRow
        reverse
        eyebrow="Publish & schedule"
        title="Manage your pages from one portal"
        body="Connect Facebook Pages and Instagram via the official API, design posts, and publish or schedule them on a visual calendar — never log into Meta again."
        bullets={["Drag-and-drop calendar", "Auto-publish via Graph API", "Approve once, runs itself"]}
        visual={<PublishVisual />}
      />
      <FeatureRow
        eyebrow="AI video & reels"
        title="Turn an idea into a video — and post it"
        body="Describe a product or drop a link; Presence writes the script, renders a UGC-style reel, and publishes it straight to Facebook, Instagram, and even your groups."
        bullets={["Script → storyboard → render", "UGC-style that converts", "Publish to FB / IG / Groups"]}
        visual={<VideoVisual />}
      />
      <FeatureRow
        reverse
        eyebrow="Meta Ads Manager"
        title="Run your ads — and find the winners"
        body="Launch campaigns from your dashboard with 10–20 auto-generated creatives, then let the AI tell you in plain language which to pause and which to scale."
        bullets={["Campaigns without the Ads Manager maze", "10–20 creative variations", "Pause/scale recommendations"]}
        visual={<AdsVisual />}
      />
      <FeatureRow
        eyebrow="Analytics & reports"
        title="See everything in one dashboard"
        body="Reach, engagement, follower growth and your top posts — with automated weekly and monthly branded reports you (or your agency) can white-label."
        bullets={["Live cross-account dashboard", "Branded weekly / monthly PDFs", "Competitor tracking"]}
        visual={<AnalyticsVisual />}
      />
      <FeatureRow
        reverse
        eyebrow="AI group matcher"
        title="Find high-intent groups in your niche"
        body="Our AI reads your niche and suggests the Facebook groups most likely to bring leads — with a relevance score and a paced, account-safe way to post."
        bullets={["Niche-matched group suggestions", "Buyer-intent ranking", "Account-safe, you stay in control"]}
        visual={<GroupsVisual />}
      />
      <FeatureRow
        eyebrow="Inbox & leads"
        title="Never miss a buyer again"
        body="Comments and DMs from Facebook and Instagram land in one inbox; the AI flags real buyers, scores them, and drafts replies for you to send."
        bullets={["Unified comments + DMs", "Automatic lead detection", "AI-drafted, you-confirmed replies"]}
        visual={<InboxVisual />}
      />
    </section>
  );
}

const STEPS = [
  ["Tell us about your business", "Drop your website and answer a few quick questions. We learn your niche, voice and goals."],
  ["Get your audit + plan", "A scored report and a ready-to-run first week of content, generated for you."],
  ["Go on autopilot", "Connect Facebook & Instagram, approve once, and Presence publishes, advertises, reports and finds leads."],
];

function HowItWorks() {
  return (
    <section id="how" className="border-y border-white/5 bg-white/[0.02]">
      <div className="mx-auto max-w-6xl px-6 py-20">
        <Reveal>
          <h2 className="text-4xl font-bold">From URL to autopilot in minutes</h2>
        </Reveal>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {STEPS.map(([title, body], i) => (
            <Reveal key={title} delay={i * 0.08}>
              <div className="card h-full p-6">
                <div className="gradient-text text-sm font-bold">STEP {i + 1}</div>
                <h3 className="mt-2 text-lg font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-white/60">{body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

const AUDIENCES = [
  ["Small business owners", "Want it run for them. Presence is the marketing hire you don’t have to manage."],
  ["Agencies", "Manage many clients, approvals and reports in one place — white-label it as your own."],
  ["Niche verticals", "Pre-tuned voice and content for your industry, from auto and gyms to restaurants and real estate."],
];

function WhoFor() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20">
      <Reveal>
        <h2 className="text-4xl font-bold">Built for the way you work</h2>
      </Reveal>
      <div className="mt-12 grid gap-6 md:grid-cols-3">
        {AUDIENCES.map(([title, body], i) => (
          <Reveal key={title} delay={i * 0.08}>
            <div className="card h-full p-6">
              <h3 className="text-lg font-semibold">{title}</h3>
              <p className="mt-2 text-sm text-white/60">{body}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

function Trust() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-20">
      <Reveal>
        <div className="card grid gap-8 p-8 md:grid-cols-2">
          <div>
            <h3 className="text-2xl font-bold">Safe by design</h3>
            <p className="mt-3 text-sm text-white/60">
              Publishing, insights, ads and your inbox run on Meta’s official APIs —
              fully compliant. We encrypt your tokens and never store passwords.
            </p>
          </div>
          <div>
            <h3 className="text-2xl font-bold">You stay in control</h3>
            <p className="mt-3 text-sm text-white/60">
              Optional group posting runs in your own browser, paced to protect your
              account — assisted and confirmed by you, never a silent firehose.
            </p>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

export interface Plan {
  name: string;
  price: string;
  tag: string;
  feats: string[];
  highlight?: boolean;
}

export const PLANS: Plan[] = [
  {
    name: "Starter",
    price: "$0",
    tag: "Audit + first week of content",
    feats: ["1 brand", "AI presence audit", "Content generation", "Manual publishing"],
  },
  {
    name: "Growth",
    price: "$49",
    tag: "For a business on autopilot",
    feats: ["Up to 3 brands", "Schedule & auto-publish", "Ads + AI video", "Analytics & reports"],
    highlight: true,
  },
  {
    name: "Agency",
    price: "Custom",
    tag: "Manage many clients",
    feats: ["Unlimited brands", "Roles & approvals", "White-label & domains", "Priority support"],
  },
];

export function PricingCards() {
  return (
    <div className="grid gap-6 md:grid-cols-3">
      {PLANS.map((plan, i) => (
        <Reveal key={plan.name} delay={i * 0.06}>
          <div className={`card flex h-full flex-col p-6 ${plan.highlight ? "ring-1 ring-[#6d5efc]" : ""}`}>
            {plan.highlight && (
              <span className="mb-3 w-fit rounded-full bg-[#6d5efc]/20 px-2 py-0.5 text-xs text-[#c7d2fe]">
                Most popular
              </span>
            )}
            <h3 className="text-lg font-semibold">{plan.name}</h3>
            <div className="mt-2 flex items-baseline gap-1">
              <span className="text-4xl font-bold">{plan.price}</span>
              {plan.price.startsWith("$") && plan.price !== "$0" && (
                <span className="text-sm text-white/50">/mo</span>
              )}
            </div>
            <p className="mt-1 text-sm text-white/55">{plan.tag}</p>
            <ul className="mt-5 flex flex-1 flex-col gap-2 text-sm text-white/70">
              {plan.feats.map((f) => (
                <li key={f} className="flex items-center gap-2">
                  <span className="text-[#22d3ee]">✓</span> {f}
                </li>
              ))}
            </ul>
            <Link
              href="/signup"
              className={`mt-6 rounded-xl px-4 py-2.5 text-center text-sm font-semibold ${
                plan.highlight ? "btn-primary" : "btn-ghost"
              }`}
            >
              {plan.name === "Agency" ? "Talk to us" : "Start free"}
            </Link>
          </div>
        </Reveal>
      ))}
    </div>
  );
}

function Pricing() {
  return (
    <section id="pricing" className="border-y border-white/5 bg-white/[0.02]">
      <div className="mx-auto max-w-6xl px-6 py-20">
        <Reveal>
          <h2 className="text-4xl font-bold">Simple pricing that scales</h2>
          <p className="mt-3 text-white/60">Start free. Upgrade when it’s running your accounts.</p>
        </Reveal>
        <div className="mt-12">
          <PricingCards />
        </div>
      </div>
    </section>
  );
}

function FinalCta() {
  return (
    <section className="mx-auto max-w-4xl px-6 py-24 text-center">
      <Reveal>
        <h2 className="text-4xl font-bold sm:text-5xl">Your next customer is one post away.</h2>
        <p className="mx-auto mt-5 max-w-xl text-white/60">
          Let Presence audit your business and run your social media — so you can run
          your business.
        </p>
        <Link href="/signup" className="btn-primary mt-8 inline-block rounded-xl px-8 py-4 text-lg font-semibold">
          Audit my business free
        </Link>
      </Reveal>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-white/5">
      <div className="mx-auto grid max-w-6xl gap-8 px-6 py-12 md:grid-cols-4">
        <div>
          <div className="flex items-center gap-2 font-semibold">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-[#6d5efc] to-[#22d3ee] text-sm">
              P
            </span>
            Presence
          </div>
          <p className="mt-3 text-sm text-white/40">Your AI marketing employee for Facebook &amp; Instagram.</p>
        </div>
        <FooterCol title="Product" links={[["Features", "/features"], ["Pricing", "/pricing"], ["Sign in", "/login"], ["Sign up", "/signup"]]} />
        <FooterCol title="Legal" links={[["Privacy", "/privacy"], ["Terms", "/terms"], ["Data deletion", "/data-deletion"]]} />
        <FooterCol title="Company" links={[["How it works", "/#how"], ["Audit my business", "/signup"]]} />
      </div>
      <div className="border-t border-white/5 py-6 text-center text-xs text-white/30">
        © {new Date().getFullYear()} Presence. All rights reserved.
      </div>
    </footer>
  );
}

function FooterCol({ title, links }: { title: string; links: [string, string][] }) {
  return (
    <div>
      <div className="text-sm font-medium text-white/70">{title}</div>
      <ul className="mt-3 flex flex-col gap-2 text-sm text-white/40">
        {links.map(([label, href]) => (
          <li key={label}>
            <Link href={href} className="hover:text-white/80">{label}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Landing() {
  return (
    <div className="min-h-screen">
      <Nav />
      <Hero />
      <Stats />
      <Features />
      <HowItWorks />
      <WhoFor />
      <Trust />
      <Pricing />
      <FinalCta />
      <Footer />
    </div>
  );
}

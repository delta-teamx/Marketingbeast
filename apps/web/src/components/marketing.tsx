import Link from "next/link";

function Nav() {
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
          <a href="#features" className="hover:text-white">Features</a>
          <a href="#how" className="hover:text-white">How it works</a>
          <a href="#who" className="hover:text-white">Who it’s for</a>
          <a href="#pricing" className="hover:text-white">Pricing</a>
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
      <div className="relative mx-auto max-w-4xl px-6 pb-24 pt-20 text-center">
        <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/70">
          <span className="h-1.5 w-1.5 rounded-full bg-[#22d3ee]" />
          AI marketing employee for Facebook &amp; Instagram
        </span>
        <h1 className="mt-6 text-5xl font-extrabold leading-[1.05] sm:text-6xl">
          Be everywhere.
          <br />
          <span className="gradient-text">Lift no finger.</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-white/70">
          Enter your business URL. Presence audits your social presence, then
          generates, schedules, publishes, and reports on content across Facebook
          and Instagram — and finds new customers in groups. Built for owners and
          agencies running many accounts.
        </p>
        <div className="mt-9 flex flex-wrap items-center justify-center gap-4">
          <Link href="/signup" className="btn-primary rounded-xl px-7 py-3.5 font-semibold">
            Audit my business free
          </Link>
          <a href="#how" className="btn-ghost rounded-xl px-7 py-3.5 font-medium">
            See how it works
          </a>
        </div>
        <p className="mt-4 text-xs text-white/40">
          No credit card · Official Meta API · Your accounts stay yours
        </p>
      </div>
    </section>
  );
}

const STATS = [
  ["80%", "of the work, automated"],
  ["1 URL", "to a running content engine"],
  ["FB + IG", "publishing, insights & inbox"],
  ["∞", "brands & clients per workspace"],
];

function Stats() {
  return (
    <section className="border-y border-white/5 bg-white/[0.02]">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-6 px-6 py-10 md:grid-cols-4">
        {STATS.map(([big, small]) => (
          <div key={small} className="text-center">
            <div className="gradient-text text-3xl font-bold">{big}</div>
            <div className="mt-1 text-sm text-white/55">{small}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

const FEATURES = [
  ["AI Presence Audit", "Enter a URL and get a scored report — profile, consistency, content, gaps — plus an action plan in minutes."],
  ["Content engine", "One idea becomes a week of on-brand posts, captions, hashtags and reels — in your voice, ready to approve."],
  ["Schedule & auto-publish", "A visual calendar and a reliable queue publish to Facebook Pages and Instagram via the official API."],
  ["Group lead finder", "We find high-intent Facebook groups for your niche and help you post — paced and safe, in your own browser."],
  ["Unified analytics", "Reach, engagement and growth in one dashboard, with automated weekly and monthly branded reports."],
  ["Built for agencies", "Manage every client in one place, with roles, approvals and white-label branding."],
];

function Features() {
  return (
    <section id="features" className="mx-auto max-w-6xl px-6 py-24">
      <div className="max-w-2xl">
        <h2 className="text-4xl font-bold">Everything your social marketing needs</h2>
        <p className="mt-4 text-white/60">
          One platform replaces the audit, the content team, the scheduler and the
          reporting deck — tuned to your industry.
        </p>
      </div>
      <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map(([title, body]) => (
          <div key={title} className="card p-6">
            <div className="mb-4 grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-[#6d5efc]/30 to-[#22d3ee]/20 text-[#c7d2fe]">
              ✦
            </div>
            <h3 className="text-lg font-semibold">{title}</h3>
            <p className="mt-2 text-sm text-white/60">{body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

const STEPS = [
  ["Tell us about your business", "Drop your website and answer a few quick questions. We learn your niche, voice and goals."],
  ["Get your audit + plan", "A scored report and a ready-to-run first week of content, generated for you."],
  ["Connect & go on autopilot", "Link Facebook & Instagram, approve once, and Presence publishes, reports and finds leads."],
];

function HowItWorks() {
  return (
    <section id="how" className="border-y border-white/5 bg-white/[0.02]">
      <div className="mx-auto max-w-6xl px-6 py-24">
        <h2 className="text-4xl font-bold">From URL to autopilot in minutes</h2>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {STEPS.map(([title, body], i) => (
            <div key={title} className="card p-6">
              <div className="gradient-text text-sm font-bold">STEP {i + 1}</div>
              <h3 className="mt-2 text-lg font-semibold">{title}</h3>
              <p className="mt-2 text-sm text-white/60">{body}</p>
            </div>
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
    <section id="who" className="mx-auto max-w-6xl px-6 py-24">
      <h2 className="text-4xl font-bold">Built for the way you work</h2>
      <div className="mt-12 grid gap-6 md:grid-cols-3">
        {AUDIENCES.map(([title, body]) => (
          <div key={title} className="card p-6">
            <h3 className="text-lg font-semibold">{title}</h3>
            <p className="mt-2 text-sm text-white/60">{body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Trust() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-24">
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
    </section>
  );
}

interface Plan {
  name: string;
  price: string;
  tag: string;
  feats: string[];
}

const PLANS: Plan[] = [
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
    feats: ["Up to 3 brands", "Schedule & auto-publish", "Analytics & reports", "Group lead finder"],
  },
  {
    name: "Agency",
    price: "Custom",
    tag: "Manage many clients",
    feats: ["Unlimited brands", "Roles & approvals", "White-label & domains", "Priority support"],
  },
];

function Pricing() {
  return (
    <section id="pricing" className="border-y border-white/5 bg-white/[0.02]">
      <div className="mx-auto max-w-6xl px-6 py-24">
        <h2 className="text-4xl font-bold">Simple pricing that scales</h2>
        <p className="mt-3 text-white/60">Start free. Upgrade when it’s running your accounts.</p>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {PLANS.map((plan, i) => (
            <div
              key={plan.name}
              className={`card flex flex-col p-6 ${i === 1 ? "ring-1 ring-[#6d5efc]" : ""}`}
            >
              {i === 1 && (
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
                  i === 1 ? "btn-primary" : "btn-ghost"
                }`}
              >
                {i === 2 ? "Talk to us" : "Start free"}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FinalCta() {
  return (
    <section className="mx-auto max-w-4xl px-6 py-24 text-center">
      <h2 className="text-4xl font-bold sm:text-5xl">
        Your next customer is one post away.
      </h2>
      <p className="mx-auto mt-5 max-w-xl text-white/60">
        Let Presence audit your business and run your social media — so you can run
        your business.
      </p>
      <Link
        href="/signup"
        className="btn-primary mt-8 inline-block rounded-xl px-8 py-4 text-lg font-semibold"
      >
        Audit my business free
      </Link>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-white/5">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 py-8 text-sm text-white/40 md:flex-row">
        <span>© {new Date().getFullYear()} Presence. All rights reserved.</span>
        <div className="flex gap-6">
          <a href="#features" className="hover:text-white/70">Features</a>
          <a href="#pricing" className="hover:text-white/70">Pricing</a>
          <Link href="/login" className="hover:text-white/70">Sign in</Link>
        </div>
      </div>
    </footer>
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

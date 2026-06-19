import { Footer, Nav, PricingCards } from "@/components/marketing";

export const metadata = { title: "Pricing — Presence" };

const FAQ = [
  ["Do I need my own Facebook API key?", "No. You just click “Connect Facebook” and authorize Presence — we handle the official Meta API for you. You never paste a key."],
  ["Can agencies manage multiple clients?", "Yes. The Agency plan gives unlimited brands, team roles, client approvals, and white-label reports and branding."],
  ["What are credits?", "AI video renders use credits so generation cost is fair and predictable. Each plan includes a monthly allowance; you can top up anytime."],
  ["Is group posting safe?", "Group posting runs in your own browser with built-in human-pacing safeguards, and you confirm each post. It’s optional and used at your own risk."],
];

export default function PricingPage() {
  return (
    <div className="min-h-screen">
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold">Pricing that scales with you</h1>
          <p className="mx-auto mt-4 max-w-xl text-white/60">
            Start free with an audit and your first week of content. Upgrade when
            Presence is running your accounts.
          </p>
        </div>
        <div className="mt-14">
          <PricingCards />
        </div>

        <div className="mx-auto mt-20 max-w-3xl">
          <h2 className="text-2xl font-bold">Frequently asked</h2>
          <div className="mt-6 flex flex-col gap-4">
            {FAQ.map(([q, a]) => (
              <div key={q} className="card p-5">
                <div className="font-medium">{q}</div>
                <p className="mt-2 text-sm text-white/60">{a}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

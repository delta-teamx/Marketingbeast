import Link from "next/link";
import type { ReactNode } from "react";

const POINTS = [
  "URL → scored audit in minutes",
  "Auto-publish to Facebook & Instagram",
  "AI video, ads, analytics & inbox",
  "Find leads in niche Facebook groups",
];

/** Split-screen auth layout: brand panel + form. */
export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Brand panel */}
      <div className="relative hidden overflow-hidden border-r border-white/5 lg:block">
        <div className="hero-glow pointer-events-none absolute inset-0" />
        <div className="grid-fade pointer-events-none absolute inset-0 opacity-30" />
        <div className="relative flex h-full flex-col justify-between p-12">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-[#6d5efc] to-[#22d3ee] text-sm">
              P
            </span>
            Presence
          </Link>
          <div>
            <h2 className="text-4xl font-bold leading-tight">
              Be everywhere.
              <br />
              <span className="gradient-text">Lift no finger.</span>
            </h2>
            <ul className="mt-8 flex flex-col gap-3 text-sm text-white/70">
              {POINTS.map((p) => (
                <li key={p} className="flex items-center gap-2">
                  <span className="text-[#22d3ee]">✓</span> {p}
                </li>
              ))}
            </ul>
          </div>
          <p className="text-xs text-white/30">
            Official Meta API · Your accounts stay yours
          </p>
        </div>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <Link
            href="/"
            className="mb-8 flex items-center gap-2 font-semibold lg:hidden"
          >
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-[#6d5efc] to-[#22d3ee] text-sm">
              P
            </span>
            Presence
          </Link>
          {children}
        </div>
      </div>
    </div>
  );
}

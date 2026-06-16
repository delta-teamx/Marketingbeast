// Lightweight, CSS-animated "product" mocks used to visualize each capability
// on the marketing site. Pure presentational — no data, no client hooks.

export function AuditVisual() {
  const sections = [
    ["Profile", 92],
    ["Consistency", 64],
    ["Content", 81],
    ["Engagement", 58],
  ] as const;
  return (
    <div className="glass p-5">
      <div className="flex items-center gap-4">
        <div
          className="grid h-20 w-20 place-items-center rounded-full text-2xl font-bold text-white"
          style={{ background: "conic-gradient(#6d5efc 0 78%, rgba(255,255,255,.08) 78% 100%)" }}
        >
          <span className="grid h-16 w-16 place-items-center rounded-full bg-[#0e0e16]">A−</span>
        </div>
        <div>
          <div className="text-sm text-white/50">Presence score</div>
          <div className="text-2xl font-semibold">78/100</div>
        </div>
      </div>
      <div className="mt-4 flex flex-col gap-2">
        {sections.map(([label, v], i) => (
          <div key={label} className="flex items-center gap-3 text-xs">
            <span className="w-24 text-white/60">{label}</span>
            <div className="h-2 flex-1 overflow-hidden rounded bg-white/10">
              <div
                className="h-full rounded bg-gradient-to-r from-[#6d5efc] to-[#22d3ee]"
                style={{ width: `${v}%`, animation: `growbar 1s ${i * 0.12}s both` }}
              />
            </div>
            <span className="w-8 text-right text-white/40">{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function PublishVisual() {
  const filled = new Set([1, 3, 4, 8, 11, 13, 16, 19]);
  return (
    <div className="glass p-5">
      <div className="mb-3 flex items-center justify-between text-xs text-white/50">
        <span>Content calendar</span>
        <span className="flex gap-1">
          <span className="rounded bg-[#1877F2]/30 px-2 py-0.5 text-[#9dc0ff]">FB</span>
          <span className="rounded bg-[#E1306C]/30 px-2 py-0.5 text-[#ffa6c9]">IG</span>
        </span>
      </div>
      <div className="grid grid-cols-7 gap-1.5">
        {Array.from({ length: 21 }).map((_, i) => (
          <div
            key={i}
            className={`aspect-square rounded-md ${
              filled.has(i)
                ? "bg-gradient-to-br from-[#6d5efc]/70 to-[#22d3ee]/50"
                : "bg-white/5"
            }`}
            style={filled.has(i) ? { animation: `growbar .6s ${i * 0.03}s both` } : undefined}
          />
        ))}
      </div>
      <div className="mt-3 text-xs text-emerald-400">✓ Scheduled &amp; auto-publishing</div>
    </div>
  );
}

export function VideoVisual() {
  return (
    <div className="glass flex items-center gap-4 p-5">
      <div className="relative grid h-28 w-20 shrink-0 place-items-center rounded-xl bg-gradient-to-b from-[#1a1a2e] to-[#0e0e16]">
        <span className="pulse-ring grid h-10 w-10 place-items-center rounded-full bg-white text-black">
          ▶
        </span>
        <span className="absolute bottom-1 rounded bg-black/50 px-1 text-[10px] text-white/70">
          0:18
        </span>
      </div>
      <div className="flex flex-col gap-2 text-xs">
        <div className="text-white/50">AI reel — UGC style</div>
        {["Hook", "Show product", "Reaction", "CTA → link"].map((s, i) => (
          <div key={s} className="flex items-center gap-2" style={{ animation: `growbar .6s ${i * 0.1}s both` }}>
            <span className="h-1.5 w-1.5 rounded-full bg-[#22d3ee]" /> {s}
          </div>
        ))}
        <div className="mt-1 text-emerald-400">Ready → publish to FB / IG / Reels</div>
      </div>
    </div>
  );
}

export function AdsVisual() {
  const creatives = [
    ["Winner — scale", 4.2, true],
    ["Variation B", 2.1, false],
    ["Variation C", 0.8, false],
  ] as const;
  return (
    <div className="glass p-5">
      <div className="mb-3 text-xs text-white/50">Meta Ads — 12 creatives, find the winner</div>
      <div className="flex flex-col gap-2">
        {creatives.map(([label, ctr, win], i) => (
          <div key={label} className="flex items-center gap-3 text-xs">
            <span className={`w-28 ${win ? "text-emerald-400" : "text-white/60"}`}>{label}</span>
            <div className="h-2 flex-1 overflow-hidden rounded bg-white/10">
              <div
                className={`h-full rounded ${win ? "bg-emerald-400" : "bg-white/40"}`}
                style={{ width: `${(ctr / 4.5) * 100}%`, animation: `growbar 1s ${i * 0.12}s both` }}
              />
            </div>
            <span className="w-12 text-right text-white/50">{ctr}% CTR</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AnalyticsVisual() {
  return (
    <div className="glass p-5">
      <div className="mb-2 flex gap-2 text-xs">
        <span className="rounded bg-white/10 px-2 py-1">Followers <b>4,182</b></span>
        <span className="rounded bg-white/10 px-2 py-1">Reach <b>61k</b></span>
        <span className="rounded bg-white/10 px-2 py-1">Eng. <b>3.4%</b></span>
      </div>
      <svg viewBox="0 0 300 110" className="h-28 w-full">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6d5efc" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#6d5efc" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polyline
          points="0,90 40,80 80,84 120,60 160,64 200,40 240,30 300,14"
          fill="none"
          stroke="#22d3ee"
          strokeWidth="2.5"
        />
        <polygon
          points="0,90 40,80 80,84 120,60 160,64 200,40 240,30 300,14 300,110 0,110"
          fill="url(#g)"
        />
      </svg>
    </div>
  );
}

export function GroupsVisual() {
  const groups = [
    ["Local Coffee Lovers", 92],
    ["City Foodies & Deals", 85],
    ["Small Biz Owners", 71],
  ] as const;
  return (
    <div className="glass p-5">
      <div className="mb-3 text-xs text-white/50">AI group matches for your niche</div>
      <div className="flex flex-col gap-2">
        {groups.map(([name, score], i) => (
          <div
            key={name}
            className="flex items-center justify-between rounded-lg border border-white/10 px-3 py-2 text-xs"
            style={{ animation: `growbar .6s ${i * 0.1}s both` }}
          >
            <span>{name}</span>
            <span className="rounded-full bg-[#22d3ee]/20 px-2 py-0.5 text-[#a5f3fc]">
              {score}% match
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function InboxVisual() {
  return (
    <div className="glass flex flex-col gap-2 p-5 text-xs">
      <div className="mb-1 text-white/50">Unified inbox — leads detected</div>
      <div className="flex items-center gap-2 self-start rounded-lg bg-white/10 px-3 py-2">
        Hi! How much is it? 👀
        <span className="rounded-full bg-[#22d3ee]/20 px-2 py-0.5 text-[10px] text-[#a5f3fc]">
          Lead · 80
        </span>
      </div>
      <div className="self-end rounded-lg bg-[#6d5efc]/30 px-3 py-2">
        ✨ Thanks! Happy to help — here are the details…
      </div>
    </div>
  );
}

// Minimal inline SVG icons for the marketing feature rows. Stroke-based so they
// inherit currentColor.

type IconName =
  | "audit"
  | "publish"
  | "video"
  | "ads"
  | "analytics"
  | "groups"
  | "inbox";

const PATHS: Record<IconName, string> = {
  audit: "M3 3v18h18 M7 14l3-3 3 2 4-5",
  publish: "M3 5h18v16H3z M3 9h18 M8 3v4 M16 3v4 M8 14h3",
  video: "M4 5h16v14H4z M10 9l5 3-5 3z",
  ads: "M3 11l14-6v14L3 13z M3 11v2 M17 8a4 4 0 0 1 0 8",
  analytics: "M4 19V5 M4 19h16 M8 17v-5 M12 17V9 M16 17v-8",
  groups: "M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M2 20a7 7 0 0 1 14 0 M17 11a3 3 0 1 0-1-5.8 M16 20a7 7 0 0 0-3-5.7",
  inbox: "M21 12a8 8 0 1 1-3.2-6.4 M21 5v5h-5",
};

export function FeatureIcon({ name }: { name: IconName }) {
  return (
    <span className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-[#6d5efc]/30 to-[#22d3ee]/20 text-[#c7d2fe]">
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d={PATHS[name]} />
      </svg>
    </span>
  );
}

export type { IconName };

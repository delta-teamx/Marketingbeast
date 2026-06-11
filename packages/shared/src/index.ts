// Shared TypeScript types — the API contract between web and the FastAPI backend.
// Mirror app/schemas in apps/api. Keep these in sync as the API grows.

export type OrgRole = "owner" | "admin" | "member";

export interface Membership {
  org_id: string;
  role: OrgRole;
}

export interface Me {
  id: string;
  email: string | null;
  memberships: Membership[];
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_personal: boolean;
}

export interface Brand {
  id: string;
  org_id: string;
  name: string;
  website_url: string | null;
  industry_vertical: string | null;
}

export type SocialProvider = "facebook_page" | "instagram";

export interface SocialAccount {
  id: string;
  brand_id: string;
  provider: SocialProvider;
  external_id: string | null;
  display_name: string | null;
  status: string;
}

export type ContentStatus =
  | "draft"
  | "scheduled"
  | "publishing"
  | "published"
  | "failed";

export interface ContentTarget {
  id: string;
  social_account_id: string;
  status: "pending" | "published" | "failed";
  external_post_id: string | null;
  permalink: string | null;
  error: string | null;
}

export interface ContentItem {
  id: string;
  brand_id: string;
  content_type: "post" | "reel" | "story";
  status: ContentStatus;
  body: string;
  media_urls: string[] | null;
  scheduled_time: string | null;
  published_at: string | null;
  approved: boolean;
  hashtags: string[] | null;
  suggested_time: string | null;
  targets: ContentTarget[];
}

// --- Flagship audit ---

export interface AuditSection {
  key: string;
  label: string;
  score: number;
  notes: string;
}

export interface AuditPlanItem {
  day: string;
  idea: string;
  caption: string;
  hashtags: string[];
}

export interface AuditReport {
  id: string;
  brand_id: string;
  overall_score: number;
  overall_grade: string;
  sections: AuditSection[];
  findings: string[];
  recommendations: string[];
  strategy_brief: string;
  content_plan: AuditPlanItem[];
  created_at: string;
}

// --- Facebook group lead finder ---

export interface NicheProfile {
  category: string;
  summary: string;
  keywords: string[];
}

export type SuggestionStatus = "suggested" | "tracked" | "dismissed";

export interface GroupSuggestion {
  id: string;
  brand_id: string;
  name: string;
  search_keyword: string;
  estimated_size: string | null;
  relevance_score: number;
  lead_quality_score: number;
  rationale: string | null;
  suggested_post_angle: string | null;
  status: SuggestionStatus;
}

export type GroupTaskStatus = "queued" | "claimed" | "posted" | "skipped";

export interface GroupPostTask {
  id: string;
  brand_id: string;
  group_suggestion_id: string;
  body: string;
  media_urls: string[] | null;
  status: GroupTaskStatus;
  external_ref: string | null;
}

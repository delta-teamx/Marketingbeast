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

// --- AI media ---

export type MediaJobStatus = "queued" | "rendering" | "ready" | "failed";

export interface MediaJob {
  id: string;
  brand_id: string;
  provider: string;
  status: MediaJobStatus;
  prompt: string;
  script: string;
  storyboard_json: { scene?: string; shot?: string }[];
  asset_url: string | null;
  cost_credits: number;
  error: string | null;
}

export interface MediaAsset {
  id: string;
  brand_id: string;
  kind: string;
  url: string;
  source: string;
  provider: string | null;
}

export interface Credits {
  org_id: string;
  credit_balance: number;
}

// --- Ads ---

export type CampaignStatus = "draft" | "active" | "paused";
export type CreativeStatus = "active" | "paused";

export interface AdAccount {
  id: string;
  brand_id: string;
  external_id: string;
  name: string | null;
  status: string;
}

export interface AdMetrics {
  impressions?: number;
  clicks?: number;
  spend?: number;
  conversions?: number;
  ctr?: number;
}

export interface AdCreative {
  id: string;
  variation_index: number;
  headline: string;
  primary_text: string;
  status: CreativeStatus;
  metrics_json: AdMetrics;
}

export interface AdCampaign {
  id: string;
  brand_id: string;
  ad_account_id: string;
  name: string;
  objective: string;
  status: CampaignStatus;
  daily_budget: number;
  metrics_json: AdMetrics;
}

export interface AdCampaignDetail extends AdCampaign {
  creatives: AdCreative[];
}

export interface AdRecommendations {
  recommendations: { creative_id: string; action: "scale" | "pause"; reason: string }[];
  summary: string;
}

// --- Unified inbox ---

export type ConversationType = "comment" | "dm";
export type ConversationStatus = "open" | "replied" | "hidden";

export interface InboxMessage {
  id: string;
  is_inbound: boolean;
  text: string;
  sent_at: string | null;
}

export interface Conversation {
  id: string;
  brand_id: string;
  conv_type: ConversationType;
  participant_name: string | null;
  status: ConversationStatus;
  is_lead: boolean;
  lead_score: number;
  last_message_at: string | null;
}

export interface ConversationDetail extends Conversation {
  messages: InboxMessage[];
}

// --- Analytics ---

export interface DashboardData {
  followers: number;
  follower_growth: number;
  total_reach: number;
  total_engagement: number;
  engagement_rate: number;
  time_series: { date: string; followers: number; reach: number; engagement: number }[];
  top_posts: { id: string; body: string; engagement: number }[];
  per_account: {
    social_account_id: string;
    display_name: string | null;
    provider: string | null;
    followers: number;
    reach: number;
    engagement: number;
  }[];
}

export type ReportPeriod = "weekly" | "monthly";

export interface Report {
  id: string;
  brand_id: string;
  period: ReportPeriod;
  starts_on: string;
  ends_on: string;
  metrics_json: Record<string, number>;
  summary: string;
}

export interface Competitor {
  id: string;
  brand_id: string;
  name: string;
  handle: string | null;
  platform: string | null;
  followers: number;
  posting_frequency: string | null;
  engagement_rate: number;
}

export interface CompetitorComparison {
  you: { followers: number };
  competitors: {
    name: string;
    followers: number;
    follower_gap: number;
    engagement_rate: number;
    posting_frequency: string | null;
  }[];
  summary: string;
}

// --- Onboarding ---

export interface OnboardingInput {
  business_name: string;
  website_url?: string | null;
  industry?: string | null;
  goal?: string | null;
  platforms: string[];
  posting_frequency?: string | null;
  monthly_budget?: string | null;
  biggest_challenge?: string | null;
  target_audience?: string | null;
}

export interface OnboardingResult {
  brand: Brand;
  profile: {
    id: string;
    brand_id: string;
    goal: string | null;
    platforms: string[] | null;
    posting_frequency: string | null;
    monthly_budget: string | null;
    biggest_challenge: string | null;
    target_audience: string | null;
  };
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

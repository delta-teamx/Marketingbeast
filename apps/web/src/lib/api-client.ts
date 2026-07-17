"use client";

import type {
  AdAccount,
  AdCampaign,
  AdCampaignDetail,
  AdRecommendations,
  AuditReport,
  Brand,
  CampaignStatus,
  Competitor,
  Credits,
  Invite,
  Member,
  MediaAsset,
  MediaJob,
  OrgSettings,
  WhiteLabel,
  CompetitorComparison,
  Conversation,
  ConversationDetail,
  ContentItem,
  DashboardData,
  GroupPostTask,
  GroupSuggestion,
  Me,
  NicheProfile,
  OnboardingInput,
  OnboardingResult,
  Organization,
  Report,
  ReportPeriod,
  SocialAccount,
} from "@presence/shared";
import type { SupabaseClient } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";

// Demo mode runs with no Supabase project configured, so we must never
// construct a Supabase client (it throws on missing env vars).
const DEMO = process.env.NEXT_PUBLIC_DEMO === "1";

// Lazily created in the browser so the client is never constructed during SSR.
let _supabase: SupabaseClient | undefined;
function sb(): SupabaseClient | null {
  if (DEMO) return null;
  return (_supabase ??= createClient());
}

/** Turn an error response into a short, user-facing message (raw detail → console). */
function friendlyError(status: number, raw: string): string {
  // FastAPI returns {"detail": "..."} for handled 4xx — those are meaningful to
  // the user (e.g. "Need 10 credits", "Brand limit reached"), so surface them.
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.detail === "string") return parsed.detail;
  } catch {
    // Not JSON (e.g. an HTML 502 from a cold-starting host) — fall through.
  }
  if (status === 401) return "Your session expired. Please sign in again.";
  if (status === 403) return "You don't have access to do that.";
  if (status >= 500)
    return "The server hit a problem. It may be waking up — please try again in a moment.";
  return `Something went wrong (${status}). Please try again.`;
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let resp: Response;
  try {
    resp = await apiFetch(sb(), path, init);
  } catch (e) {
    // Network failure / DNS / CORS / connection refused — never show the raw error.
    console.error(`API request to ${path} failed to reach the server:`, e);
    throw new Error(
      "Couldn't reach the server. Please check your connection and try again.",
    );
  }
  if (!resp.ok) {
    const raw = await resp.text();
    console.error(`API ${resp.status} ${path}: ${raw}`);
    throw new Error(friendlyError(resp.status, raw));
  }
  return (await resp.json()) as T;
}

export const api = {
  config: () => call<{ ads_enabled: boolean; media_enabled: boolean }>("/api/config"),
  me: () => call<Me>("/api/auth/me"),
  conversationalOnboarding: (message: string) =>
    call<import("@presence/shared").ConversationalStrategy>(
      "/api/onboarding/conversational",
      { method: "POST", body: JSON.stringify({ message }) },
    ),
  submitOnboarding: (input: OnboardingInput) =>
    call<OnboardingResult>("/api/onboarding", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  getOnboarding: () => call<OnboardingResult | null>("/api/onboarding"),
  listOrgs: () => call<Organization[]>("/api/organizations"),
  createOrg: (name: string) =>
    call<Organization>("/api/organizations", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  // --- Agency / white-label ---
  orgSettings: (orgId: string) =>
    call<OrgSettings>(`/api/organizations/${orgId}/settings`),
  changePlan: (orgId: string, plan: OrgSettings["plan"]) =>
    call<OrgSettings>(`/api/organizations/${orgId}/plan`, {
      method: "POST",
      body: JSON.stringify({ plan }),
    }),
  billingCheckout: (orgId: string, plan: "growth" | "agency") =>
    call<{ url: string; completed: boolean; plan: string; credit_balance: number }>(
      "/api/billing/checkout",
      { method: "POST", body: JSON.stringify({ org_id: orgId, plan }) },
    ),
  updateWhiteLabel: (orgId: string, wl: WhiteLabel) =>
    call<OrgSettings>(`/api/organizations/${orgId}/white-label`, {
      method: "PUT",
      body: JSON.stringify(wl),
    }),
  listMembers: (orgId: string) =>
    call<Member[]>(`/api/organizations/${orgId}/members`),
  createInvite: (orgId: string, email: string, role: Member["role"]) =>
    call<Invite>(`/api/organizations/${orgId}/invites`, {
      method: "POST",
      body: JSON.stringify({ email, role }),
    }),
  listInvites: (orgId: string) =>
    call<Invite[]>(`/api/organizations/${orgId}/invites`),
  myInvites: () => call<Invite[]>("/api/invites"),
  acceptInvite: (inviteId: string) =>
    call<Member>(`/api/invites/${inviteId}/accept`, { method: "POST" }),
  listBrands: (orgId: string) =>
    call<Brand[]>(`/api/brands?org_id=${orgId}`),
  createBrand: (orgId: string, name: string) =>
    call<Brand>("/api/brands", {
      method: "POST",
      body: JSON.stringify({ org_id: orgId, name }),
    }),
  listSocialAccounts: (brandId: string) =>
    call<SocialAccount[]>(`/api/social-accounts?brand_id=${brandId}`),
  startOAuth: (brandId: string) =>
    call<{ authorize_url: string }>(
      `/api/integrations/meta/oauth/start?brand_id=${brandId}`,
    ),
  listContent: (brandId: string) =>
    call<ContentItem[]>(`/api/content?brand_id=${brandId}`),
  createContent: (input: {
    brand_id: string;
    body: string;
    target_account_ids: string[];
    scheduled_time?: string | null;
  }) =>
    call<ContentItem>("/api/content", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  publishNow: (id: string) =>
    call<ContentItem>(`/api/content/${id}/publish`, { method: "POST" }),

  // --- Content engine ---
  generateContent: (brandId: string, prompt: string, count = 7) =>
    call<ContentItem[]>("/api/content/generate", {
      method: "POST",
      body: JSON.stringify({ brand_id: brandId, prompt, count }),
    }),
  approveContent: (id: string) =>
    call<ContentItem>(`/api/content/${id}/approve`, { method: "POST" }),
  repurposeContent: (id: string) =>
    call<ContentItem[]>(`/api/content/${id}/repurpose`, { method: "POST" }),

  // --- AI media ---
  getCredits: (brandId: string) =>
    call<Credits>(`/api/brands/${brandId}/credits`),
  topupCredits: (brandId: string, amount: number) =>
    call<Credits>(`/api/brands/${brandId}/credits/topup`, {
      method: "POST",
      body: JSON.stringify({ amount }),
    }),
  generateVideo: (brandId: string, note: string, productUrl?: string) =>
    call<MediaJob>(`/api/brands/${brandId}/videos/generate`, {
      method: "POST",
      body: JSON.stringify({ note, product_url: productUrl ?? null }),
    }),
  listMediaJobs: (brandId: string) =>
    call<MediaJob[]>(`/api/brands/${brandId}/media-jobs`),
  pollMediaJob: (id: string) =>
    call<MediaJob>(`/api/media-jobs/${id}/poll`, { method: "POST" }),
  listMediaAssets: (brandId: string) =>
    call<MediaAsset[]>(`/api/brands/${brandId}/media-assets`),
  publishReel: (
    assetId: string,
    input: { body: string; target_account_ids: string[]; scheduled_time?: string | null },
  ) =>
    call<ContentItem>(`/api/media-assets/${assetId}/publish`, {
      method: "POST",
      body: JSON.stringify(input),
    }),

  // --- Ads ---
  connectAdAccount: (brandId: string) =>
    call<AdAccount>(`/api/brands/${brandId}/ad-accounts/connect-mock`, { method: "POST" }),
  listAdAccounts: (brandId: string) =>
    call<AdAccount[]>(`/api/brands/${brandId}/ad-accounts`),
  createCampaign: (
    brandId: string,
    input: {
      ad_account_id: string;
      name: string;
      objective: string;
      daily_budget: number;
      concept: string;
      n_variations: number;
    },
  ) =>
    call<AdCampaignDetail>(`/api/brands/${brandId}/campaigns`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  listCampaigns: (brandId: string) =>
    call<AdCampaign[]>(`/api/brands/${brandId}/campaigns`),
  syncCampaign: (id: string) =>
    call<AdCampaignDetail>(`/api/campaigns/${id}/sync`, { method: "POST" }),
  campaignRecommendations: (id: string) =>
    call<AdRecommendations>(`/api/campaigns/${id}/recommendations`),
  setCampaignStatus: (id: string, status: CampaignStatus) =>
    call<AdCampaignDetail>(`/api/campaigns/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  // --- Unified inbox ---
  syncInbox: (brandId: string) =>
    call<Conversation[]>(`/api/brands/${brandId}/inbox/sync`, { method: "POST" }),
  listInbox: (brandId: string, leadsOnly = false) =>
    call<Conversation[]>(`/api/brands/${brandId}/inbox?leads_only=${leadsOnly}`),
  getConversation: (id: string) =>
    call<ConversationDetail>(`/api/conversations/${id}`),
  draftReply: (id: string) =>
    call<{ text: string }>(`/api/conversations/${id}/draft-reply`, { method: "POST" }),
  sendReply: (id: string, text: string) =>
    call<ConversationDetail>(`/api/conversations/${id}/reply`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  hideConversation: (id: string) =>
    call<ConversationDetail>(`/api/conversations/${id}/hide`, { method: "POST" }),

  // --- Analytics ---
  syncInsights: (brandId: string) =>
    call<DashboardData>(`/api/brands/${brandId}/insights/sync`, { method: "POST" }),
  getAnalytics: (brandId: string) =>
    call<DashboardData>(`/api/brands/${brandId}/analytics`),
  generateReport: (brandId: string, period: ReportPeriod) =>
    call<Report>(`/api/brands/${brandId}/reports/generate`, {
      method: "POST",
      body: JSON.stringify({ period }),
    }),
  listReports: (brandId: string) =>
    call<Report[]>(`/api/brands/${brandId}/reports`),
  addCompetitor: (
    brandId: string,
    input: { name: string; followers: number; engagement_rate: number },
  ) =>
    call<Competitor>(`/api/brands/${brandId}/competitors`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  compareCompetitors: (brandId: string) =>
    call<CompetitorComparison>(`/api/brands/${brandId}/competitors/compare`),

  // --- Flagship audit ---
  runAudit: (brandId: string) =>
    call<AuditReport>(`/api/brands/${brandId}/audit/run`, { method: "POST" }),
  getAudit: (brandId: string) =>
    call<AuditReport | null>(`/api/brands/${brandId}/audit`),
  seedFirstWeek: (brandId: string) =>
    call<ContentItem[]>(`/api/brands/${brandId}/audit/seed`, { method: "POST" }),

  // --- Facebook group lead finder ---
  detectNiche: (brandId: string) =>
    call<NicheProfile>(`/api/brands/${brandId}/niche/detect`, { method: "POST" }),
  generateGroupSuggestions: (brandId: string) =>
    call<GroupSuggestion[]>("/api/group-suggestions/generate", {
      method: "POST",
      body: JSON.stringify({ brand_id: brandId }),
    }),
  listGroupSuggestions: (brandId: string) =>
    call<GroupSuggestion[]>(`/api/group-suggestions?brand_id=${brandId}`),
  updateGroupSuggestion: (id: string, status: GroupSuggestion["status"]) =>
    call<GroupSuggestion>(`/api/group-suggestions/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  queueGroupPost: (input: {
    brand_id: string;
    group_suggestion_id: string;
    body: string;
  }) =>
    call<GroupPostTask>("/api/automation/group-queue", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  listGroupQueue: (brandId: string) =>
    call<GroupPostTask[]>(`/api/automation/group-queue?brand_id=${brandId}`),
};

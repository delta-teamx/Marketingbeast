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

// Lazily created in the browser so the client is never constructed during SSR.
let _supabase: SupabaseClient | undefined;
function sb(): SupabaseClient {
  return (_supabase ??= createClient());
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await apiFetch(sb(), path, init);
  if (!resp.ok) {
    const detail = await resp.text();
    throw new Error(`API ${resp.status}: ${detail}`);
  }
  return (await resp.json()) as T;
}

export const api = {
  me: () => call<Me>("/api/auth/me"),
  submitOnboarding: (input: OnboardingInput) =>
    call<OnboardingResult>("/api/onboarding", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  getOnboarding: () => call<OnboardingResult | null>("/api/onboarding"),
  listOrgs: () => call<Organization[]>("/api/organizations"),
  listBrands: (orgId: string) =>
    call<Brand[]>(`/api/brands?org_id=${orgId}`),
  createBrand: (orgId: string, name: string) =>
    call<Brand>("/api/brands", {
      method: "POST",
      body: JSON.stringify({ org_id: orgId, name }),
    }),
  listSocialAccounts: (brandId: string) =>
    call<SocialAccount[]>(`/api/social-accounts?brand_id=${brandId}`),
  connectMock: (brandId: string) =>
    call<SocialAccount[]>("/api/integrations/meta/connect-mock", {
      method: "POST",
      body: JSON.stringify({ brand_id: brandId }),
    }),
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

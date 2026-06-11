"use client";

import type {
  Brand,
  ContentItem,
  GroupPostTask,
  GroupSuggestion,
  Me,
  NicheProfile,
  Organization,
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

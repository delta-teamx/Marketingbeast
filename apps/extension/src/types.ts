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

export interface GroupSuggestion {
  id: string;
  search_keyword: string;
  name: string;
}

export interface Settings {
  apiBaseUrl: string;
  accessToken: string; // the user's Supabase access token (pasted from the web app)
  brandId: string;
  consentAccepted: boolean;
  wakingStartHour: number;
  wakingEndHour: number;
}

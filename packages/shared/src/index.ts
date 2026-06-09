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

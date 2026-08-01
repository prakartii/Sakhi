// Mirrors backend/app/schemas/*.py response shapes. Only the fields the
// frontend actually reads are declared — extra backend fields are ignored
// by TypeScript's structural typing, so this stays additive as more pages
// wire up more endpoints.

export type BusinessStage =
  | "idea"
  | "early"
  | "growing"
  | "established"
  | null;

export interface BusinessProfile {
  id: string;
  user_id: string;
  business_name: string;
  business_category: string | null;
  industry: string | null;
  registration_type: string;
  city: string | null;
  state: string | null;
  country: string;
  logo_url: string | null;
  is_primary: boolean;
  status: string;
  owner_name: string | null;
  business_description: string | null;
  target_audience: string | null;
  products_or_services: string | null;
  business_stage: BusinessStage;
  website_url: string | null;
  instagram_url: string | null;
  facebook_url: string | null;
  linkedin_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface BusinessProfileListResponse {
  items: BusinessProfile[];
  total: number;
  limit: number;
  offset: number;
}

export interface BusinessProfileOnboardingStatus {
  business_profile_id: string;
  is_complete: boolean;
  completion_percentage: number;
  completed_fields: string[];
  missing_fields: string[];
}

export interface InventorySummary {
  business_profile_id: string;
  total_products: number;
  total_stock_value: number;
  low_stock_count: number;
  out_of_stock_count: number;
}

export interface NotificationItem {
  id: string;
  user_id: string;
  business_profile_id: string | null;
  notification_type: string;
  title: string;
  body: string | null;
  action_url: string | null;
  priority: "low" | "normal" | "high" | "urgent";
  channel: string;
  is_read: boolean;
  status: "read" | "unread";
  created_at: string;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ScheduledPostItem {
  id: string;
  business_profile_id: string;
  content_calendar_id: string;
  social_connection_id: string;
  scheduled_time: string;
  publishing_status: string;
  retry_count: number;
  published_url: string | null;
}

export interface ScheduledPostListResponse {
  items: ScheduledPostItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface AITopAction {
  action: string;
  why: string;
}

export interface AISummary {
  narrative: string;
  highlights: string[];
  top_actions: AITopAction[];
}

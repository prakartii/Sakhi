// Mirrors backend/app/schemas/*.py response shapes. Only the fields the
// frontend actually reads are declared — extra backend fields are ignored
// by TypeScript's structural typing, so this stays additive as more pages
// wire up more endpoints.

export type BusinessStage = "idea" | "early" | "growing" | "established" | null;

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

export interface BrandAsset {
  id: string;
  business_profile_id: string;
  brand_name: string;
  tagline: string | null;
  brand_story: string | null;
  mission: string | null;
  vision: string | null;
  primary_color: string | null;
  secondary_color: string | null;
  typography: string | null;
  logo_url: string | null;
  favicon_url: string | null;
  brand_voice: string | null;
  packaging_notes: string | null;
  status: "draft" | "active" | "archived";
  created_at: string;
  updated_at: string;
}

export interface BrandAssetListResponse {
  items: BrandAsset[];
  total: number;
  limit: number;
  offset: number;
}

export interface InventoryItem {
  id: string;
  business_profile_id: string;
  item_name: string;
  sku: string | null;
  category: string | null;
  unit: string;
  reorder_level: number;
  unit_cost: number | null;
  selling_price: number | null;
  image_url: string | null;
  supplier_id: string | null;
  is_active: boolean;
  current_quantity: number;
  created_at: string;
  updated_at: string;
}

export interface InventoryListResponse {
  items: InventoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface Transaction {
  id: string;
  business_profile_id: string;
  transaction_type: "income" | "expense";
  category: string | null;
  amount: number;
  currency: string;
  payment_method: string;
  counterparty_name: string | null;
  counterparty_contact: string | null;
  transaction_date: string;
  description: string | null;
  receipt_url: string | null;
  is_recurring: boolean;
  recurring_frequency: string | null;
  status: string;
  source: string;
  supplier_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  limit: number;
  offset: number;
}

export interface Website {
  id: string;
  business_profile_id: string;
  website_name: string;
  deployment_url: string | null;
  github_repository: string | null;
  template: string | null;
  status: string;
  seo_title: string | null;
  seo_description: string | null;
  custom_domain: string | null;
  favicon: string | null;
  published: boolean;
  created_at: string;
  updated_at: string;
}

export interface WebsiteListResponse {
  items: Website[];
  total: number;
  limit: number;
  offset: number;
}

export interface WebsiteGenerateHero {
  headline: string;
  subhead: string;
  cta: string;
}

export interface WebsiteGenerateSection {
  type: string;
  heading: string;
  body: string;
}

export interface WebsiteGenerateProduct {
  name: string;
  description: string;
  price: string | null;
}

export interface WebsiteGenerateFAQ {
  q: string;
  a: string;
}

export interface WebsiteGenerateResponse {
  website: Website;
  hero: WebsiteGenerateHero;
  sections: WebsiteGenerateSection[];
  about: string;
  products: WebsiteGenerateProduct[];
  contact: string;
  faq: WebsiteGenerateFAQ[];
  seo_keywords: string[];
}

export interface BusinessMemory {
  id: string;
  business_profile_id: string;
  source_voice_log_id: string | null;
  memory_type: "fact" | "milestone" | "goal" | "challenge" | "preference" | "note" | "decision";
  title: string | null;
  content: string;
  source: "voice" | "manual" | "ai_inferred" | "conversation" | "import";
  importance_score: number;
  is_archived: boolean;
  occurred_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BusinessMemoryListResponse {
  items: BusinessMemory[];
  total: number;
  limit: number;
  offset: number;
}

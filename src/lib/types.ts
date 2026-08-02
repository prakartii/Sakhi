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

export interface InventoryForecast {
  has_sufficient_data: boolean;
  daily_run_rate: number;
  days_of_stock_remaining: number | null;
  projected_stockout_date: string | null;
  reorder_by_date: string | null;
  confidence_score: number;
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

export interface WebsiteContent {
  pages: {
    landing: { hero: WebsiteGenerateHero; sections: WebsiteGenerateSection[] };
    about: { body: string };
    products: WebsiteGenerateProduct[];
    contact: { body: string };
    faq: WebsiteGenerateFAQ[];
  };
  seo: { title: string; description: string; keywords: string[] };
}

export interface WebsiteImages {
  hero_url?: string | null;
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
  preview_slug: string | null;
  content: WebsiteContent | null;
  images: WebsiteImages | null;
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

export interface WebsiteChatMessage {
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface WebsiteChatHistoryResponse {
  messages: WebsiteChatMessage[];
}

export interface WebsiteChatResponse {
  website: Website;
  reply: string;
  hero: WebsiteGenerateHero;
  sections: WebsiteGenerateSection[];
  about: string;
  products: WebsiteGenerateProduct[];
  contact: string;
  faq: WebsiteGenerateFAQ[];
  seo_keywords: string[];
  images: WebsiteImages;
  preview_path: string | null;
}

export interface PublicWebsiteBrand {
  primary_color: string | null;
  secondary_color: string | null;
  typography: string | null;
}

export interface PublicWebsiteResponse {
  website_name: string;
  content: WebsiteContent;
  images: WebsiteImages;
  brand: PublicWebsiteBrand | null;
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

export interface MemorySearchResult {
  business_memory_id: string;
  title: string | null;
  content: string;
  similarity: number;
}

export interface MemorySearchResponse {
  query: string;
  results: MemorySearchResult[];
}

export interface MemoryInsightsResponse {
  why: string;
  basis: string;
  total: number;
  top_type: string | null;
  avg_importance: number | null;
}

export interface RunRatePoint {
  period_start: string;
  value: number;
}

export interface GrowthForecast {
  has_sufficient_data: boolean;
  historical: RunRatePoint[];
  projected: RunRatePoint[];
  moving_average: number | null;
  trend_per_period: number | null;
  confidence_score: number | null;
  why: string | null;
  basis: string | null;
}

export interface StockSignal {
  inventory_id: string;
  item_name: string;
  days_remaining: number;
  current_quantity: number;
  unit: string;
}

export interface MemorySignal {
  business_memory_id: string;
  title: string | null;
  content: string;
}

export interface NoticedSummary {
  stock_signals: StockSignal[];
  revenue_trend_per_week: number | null;
  revenue_declining: boolean;
  memory_signals: MemorySignal[];
  connected_why: string | null;
  connected_basis: string | null;
}

export interface AdvisorChatMessage {
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface AdvisorChatHistoryResponse {
  messages: AdvisorChatMessage[];
}

export interface AdvisorChatResponse {
  answer: string;
  used_services: string[];
  sources: string[];
}

export interface SchemeMatch {
  scheme_id: string;
  scheme_name: string;
  scheme_code: string | null;
  description: string | null;
  issuing_authority: string | null;
  scheme_level: "central" | "state" | "district";
  benefits: string | null;
  application_url: string | null;
  category: string | null;
  match_score: number;
  is_eligible: boolean;
  why: string;
  basis: string;
}

export interface SchemeMatchListResponse {
  items: SchemeMatch[];
  total: number;
}

export interface MentorMatch {
  mentor_id: string;
  full_name: string;
  bio: string | null;
  expertise_areas: string[];
  industry_focus: string | null;
  years_experience: number | null;
  avatar_url: string | null;
  availability_status: "available" | "busy" | "unavailable";
  match_score: number;
  is_eligible: boolean;
  why: string;
  basis: string;
}

export interface MentorMatchListResponse {
  items: MentorMatch[];
  total: number;
}

export type ContentType = "post" | "story" | "reel" | "carousel" | "video";
export type SocialPlatform = "instagram" | "linkedin" | "facebook" | "pinterest";
export type ContentStatus = "draft" | "scheduled" | "published" | "failed" | "cancelled";
export type CampaignFocus =
  "general" | "festival" | "product_launch" | "promotional_offer" | "bundle_idea";

export interface ContentCalendarItem {
  id: string;
  business_profile_id: string;
  title: string;
  content_type: ContentType;
  platform: SocialPlatform;
  social_connection_id: string | null;
  caption: string | null;
  hashtags: string[] | null;
  image_prompt: string | null;
  generated_image_url: string | null;
  generated_video_url: string | null;
  call_to_action: string | null;
  scheduled_datetime: string | null;
  status: ContentStatus;
  ai_generated: boolean;
  created_at: string;
  updated_at: string;
}

export interface ContentCalendarItemListResponse {
  items: ContentCalendarItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ContentCalendarGenerateResponse {
  items: ContentCalendarItem[];
}

// -- Marketing Studio --------------------------------------------------

export interface ContentMetrics {
  views: number | null;
  likes: number | null;
  comments: number | null;
  shares: number | null;
  saves: number | null;
}

export interface RatedFeedback {
  rating: string;
  feedback: string;
}

export interface AudienceSentiment {
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
  summary: string;
}

export interface ContentAnalysis {
  virality_score: number;
  virality_reasoning: string;
  product_detection: string[];
  comment_themes: string[];
  comment_summary: string;
  audience_sentiment: AudienceSentiment;
  hook_analysis: RatedFeedback;
  cta_analysis: RatedFeedback;
  caption_analysis: RatedFeedback;
  thumbnail_analysis: RatedFeedback | null;
  recommendations: string[];
  ai_captions: string[];
  next_reel_ideas: string[];
  performance_summary: string;
}

export interface ReelBrief {
  concept: string;
  hook: string;
  script_beats: string[];
  shot_list: string[];
  caption: string;
  hashtags: string[];
  cta: string;
  image_url: string | null;
  video_url: string | null;
}

export type MarketingAnalysisSourceType = "manual" | "screenshot" | "video_frame" | "link";

export interface MarketingAnalysis {
  id: string;
  business_profile_id: string;
  social_connection_id: string | null;
  source_type: MarketingAnalysisSourceType;
  source_url: string | null;
  caption: string | null;
  hashtags: string[];
  comments_sample: string[];
  metrics: ContentMetrics;
  engagement_rate: number | null;
  analysis: ContentAnalysis | null;
  reel_brief: ReelBrief | null;
  created_at: string;
  updated_at: string;
}

export interface MarketingAnalysisListResponse {
  items: MarketingAnalysis[];
  total: number;
  limit: number;
  offset: number;
}

// -- Social connections --------------------------------------------------

export type SocialConnectionStatus = "connected" | "expired" | "disconnected" | "error";

export interface SocialMediaConnection {
  id: string;
  business_profile_id: string;
  platform: SocialPlatform;
  account_name: string | null;
  account_id: string | null;
  profile_url: string | null;
  token_expiry: string | null;
  connection_status: SocialConnectionStatus;
  last_sync: string | null;
  created_at: string;
  updated_at: string;
}

export interface SocialMediaConnectionListResponse {
  items: SocialMediaConnection[];
  total: number;
  limit: number;
  offset: number;
}

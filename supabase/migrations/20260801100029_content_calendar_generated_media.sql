-- =====================================================================
-- Migration 29: Content Calendar generated media
-- =====================================================================
-- Adds storage for AI-generated visuals on a content_calendar_items row,
-- on top of migration 23's image_prompt (text only, no actual image).
--
--   - generated_image_url: a Nano Banana (Gemini 2.5 Flash Image) result.
--     Stored as-is — for this provider that's a data: URL (inline base64),
--     since nothing in this app persists images to object storage (see
--     app.ai.image.gemini_provider); for other providers it may be a
--     real hosted URL. Either way the column just holds whatever the
--     provider returned, ready to drop straight into an <img src>.
--   - generated_video_url: a fal.ai result — always a real hosted URL,
--     since fal.ai hosts its own outputs.
-- Both nullable: most items never get past the AI-generated caption/
-- hashtags stage, and image/video generation is a separate, explicit,
-- real-money-costing action a caller opts into per item.
-- =====================================================================

alter table public.content_calendar_items
  add column if not exists generated_image_url text,
  add column if not exists generated_video_url text;

comment on column public.content_calendar_items.generated_image_url is
  'AI-generated image for this post (app.ai.image, Nano Banana) — a data: URL for Gemini, a hosted URL for other providers. Null until generated.';
comment on column public.content_calendar_items.generated_video_url is
  'AI-generated video for this post (app.ai.video, fal.ai) — a hosted URL. Null until generated; each generation is a real, billed API call.';

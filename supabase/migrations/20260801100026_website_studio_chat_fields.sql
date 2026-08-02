-- =====================================================================
-- Migration 26: Website Studio chat fields
-- =====================================================================
-- Adds what Website Studio's chat-driven curation flow needs on top of
-- migration 21's websites/website_versions tables:
--   - content jsonb: the full generated WebsiteSpec (pages + seo), so a
--     public preview can render a site without regenerating it. Migration
--     21 deliberately left this out ("storage only... no generation");
--     the chat flow is what now needs a site's content to survive between
--     turns and page visits, not just the metadata.
--   - images jsonb: preview image URLs (app.ai.image), kept separate from
--     `content` because they come from a different AI service than the
--     one that produces the page copy.
--   - preview_slug: a url-safe public identifier, distinct from
--     custom_domain (a real-world domain the business may not have) and
--     from id (not meant to be a public-facing URL segment).
-- website_versions gets the same content/images columns so its existing
-- "every write is snapshotted" invariant still covers the full state, not
-- just metadata (see app.services.website._SNAPSHOT_FIELDS).
-- =====================================================================

alter table public.websites
  add column if not exists content jsonb,
  add column if not exists images jsonb,
  add column if not exists preview_slug varchar(80);

create unique index if not exists uq_websites_preview_slug
  on public.websites (preview_slug)
  where preview_slug is not null;

comment on column public.websites.content is
  'Full generated WebsiteSpec (pages + seo) from app.ai.website, kept in sync by the chat curation flow. Null until a site has been generated at least once.';
comment on column public.websites.images is
  'Preview image URLs from app.ai.image (hero + per-product), keyed by app.schemas.website_generation''s own shape. Null until images have been generated.';
comment on column public.websites.preview_slug is
  'URL-safe public identifier for GET /public/websites/{slug} and the frontend''s public preview route. Assigned once at first chat turn, never reused across businesses.';

alter table public.website_versions
  add column if not exists content jsonb,
  add column if not exists images jsonb;

comment on column public.website_versions.content is
  'Snapshot of websites.content at the time this version was recorded.';
comment on column public.website_versions.images is
  'Snapshot of websites.images at the time this version was recorded.';

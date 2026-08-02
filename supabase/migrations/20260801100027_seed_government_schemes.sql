-- =====================================================================
-- Migration 27: Seed government_schemes with real central MSME schemes
-- =====================================================================
-- government_schemes is reference/catalog data by design (migration 13:
-- "a GLOBAL catalog... populated independently of any one user"), and
-- has stayed empty since that migration — app.ai.rules.evaluate_criteria()
-- has nothing to match against without it. Seeds five real, well-known
-- central government schemes relevant to Indian women micro-entrepreneurs
-- (the same ones the original Schemes page mock referenced).
--
-- eligibility_criteria follows app.ai.rules.Criterion's shape
-- ({"criteria": [{field, operator, value, weight, required, label}, ...]})
-- — see app/services/scheme_match.py, which evaluates these against a
-- business's own profile facts. Only objectively-derivable facts
-- (registration type, Udyam registration status, business age) are
-- encoded — business_profiles has no gender field to check (Sakhi's
-- whole user base is women entrepreneurs by construction, so "women-led"
-- is never a discriminating fact here). This is a good-faith estimate
-- for demo/informational purposes, not an authoritative eligibility
-- determination — the "estimated match" framing carries through to the
-- API and frontend copy.
-- =====================================================================

insert into public.government_schemes
  (scheme_name, scheme_code, description, issuing_authority, scheme_level,
   eligibility_criteria, benefits, application_url, category,
   min_business_age_months, target_gender, is_active)
values
  (
    'PM Vishwakarma',
    'PM-VISHWAKARMA',
    'Support scheme for traditional artisans and craftspeople across 18 trades, offering a toolkit incentive and collateral-free credit.',
    'Ministry of Micro, Small and Medium Enterprises',
    'central',
    '{"criteria": [
      {"field": "registration_type", "operator": "in", "value": ["unregistered", "sole_proprietorship", "partnership"], "weight": 1, "required": true, "label": "Registration type is eligible for PM Vishwakarma"},
      {"field": "has_udyam_registration", "operator": "eq", "value": true, "weight": 1, "required": false, "label": "Udyam registration on file (streamlines the application)"}
    ]}'::jsonb,
    'Rs 15,000 toolkit incentive, plus collateral-free credit up to Rs 3,00,000 at a concessional rate.',
    'https://pmvishwakarma.gov.in',
    'craft & artisan',
    null,
    'women',
    true
  ),
  (
    'Mudra Yojana — Kishore',
    'MUDRA-KISHORE',
    'Working-capital loan band under Pradhan Mantri MUDRA Yojana for micro-enterprises with some operating history.',
    'Small Industries Development Bank of India (SIDBI)',
    'central',
    '{"criteria": [
      {"field": "registration_type", "operator": "in", "value": ["unregistered", "sole_proprietorship", "partnership", "llp"], "weight": 1, "required": true, "label": "Registration type is eligible for Mudra"}
    ]}'::jsonb,
    'Rs 50,000 to Rs 5,00,000 collateral-free working-capital loan.',
    'https://www.mudra.org.in',
    'micro-finance',
    6,
    'women',
    true
  ),
  (
    'Udyam Registration Benefits',
    'UDYAM-BENEFITS',
    'Registration-linked benefits for micro, small and medium enterprises registered on the Udyam portal.',
    'Ministry of Micro, Small and Medium Enterprises',
    'central',
    '{"criteria": [
      {"field": "has_udyam_registration", "operator": "eq", "value": true, "weight": 1, "required": true, "label": "Business is Udyam-registered"},
      {"field": "registration_type", "operator": "not_in", "value": ["public_limited"], "weight": 1, "required": false, "label": "Registration type is typical of an MSME"}
    ]}'::jsonb,
    'Subsidised credit, priority-sector lending, and access to government tenders reserved for MSMEs.',
    'https://udyamregistration.gov.in',
    'msme registration',
    null,
    'women',
    true
  ),
  (
    'Stand-Up India',
    'STANDUP-INDIA',
    'Bank loans for greenfield enterprises set up by women and SC/ST entrepreneurs.',
    'Department of Financial Services',
    'central',
    '{"criteria": [
      {"field": "registration_type", "operator": "in", "value": ["sole_proprietorship", "partnership", "private_limited", "llp"], "weight": 1, "required": false, "label": "Registration type matches Stand-Up India''s typical band"},
      {"field": "business_age_months", "operator": "lte", "value": 60, "weight": 1, "required": false, "label": "This is a newer (greenfield) enterprise"}
    ]}'::jsonb,
    'Bank loans between Rs 10,00,000 and Rs 1,00,00,000 for a new enterprise.',
    'https://www.standupmitra.in',
    'bank loan',
    null,
    'women',
    true
  ),
  (
    'CGTMSE Credit Guarantee',
    'CGTMSE',
    'Credit guarantee cover so banks can lend to MSMEs without asking for collateral.',
    'Credit Guarantee Fund Trust for Micro and Small Enterprises',
    'central',
    '{"criteria": [
      {"field": "has_udyam_registration", "operator": "eq", "value": true, "weight": 1, "required": true, "label": "Business is Udyam-registered"},
      {"field": "registration_type", "operator": "not_in", "value": ["public_limited"], "weight": 1, "required": false, "label": "Registration type is typical of an MSME"}
    ]}'::jsonb,
    'Collateral-free credit guarantee cover for loans up to Rs 2,00,00,000.',
    'https://www.cgtmse.in',
    'credit guarantee',
    null,
    'women',
    true
  )
on conflict (scheme_code) do nothing;

-- StudentFlow — Migration 003: SEO columns
-- Adds slug, view tracking, and featured flag to the offers table.
-- Run after 002_uber_grade.sql.
-- Idempotent: all statements use IF NOT EXISTS guards.
-- ---------------------------------------------------------------------------

BEGIN;

-- ---- offers: SEO slug + analytics counters --------------------------------

-- Slug: human-readable URL-safe identifier for /offres/{slug} pages.
-- Populated by the application layer (seo.slug.offer_slug) on insert/upsert.
-- NULL until backfilled; the API falls back to UUID when slug is absent.
ALTER TABLE offers ADD COLUMN IF NOT EXISTS slug text;
CREATE UNIQUE INDEX IF NOT EXISTS idx_offers_slug ON offers (slug) WHERE slug IS NOT NULL;

-- view_count: incremented when the SEO page for this offer is served.
-- Used to surface "popular" offers (secondary ranking signal in matching).
ALTER TABLE offers ADD COLUMN IF NOT EXISTS view_count integer NOT NULL DEFAULT 0;

-- is_featured: manually flagged premium / sponsored offers.
-- Featured offers get a small ranking boost in the matcher and appear first
-- on city landing pages.
ALTER TABLE offers ADD COLUMN IF NOT EXISTS is_featured boolean NOT NULL DEFAULT false;
CREATE INDEX IF NOT EXISTS idx_offers_featured ON offers (is_featured) WHERE is_featured = true;

-- ---- students: SEO origin tracking ----------------------------------------

-- utm_source / utm_medium track which SEO page the student came from.
-- Helps measure which city/skill pages convert best.
ALTER TABLE students ADD COLUMN IF NOT EXISTS utm_source text DEFAULT '';
ALTER TABLE students ADD COLUMN IF NOT EXISTS utm_medium text DEFAULT '';
ALTER TABLE students ADD COLUMN IF NOT EXISTS utm_campaign text DEFAULT '';

-- ---- Materialised city index (optional, for large datasets) ----------------
-- Pre-aggregate city → offer count to avoid a full table scan on /emplois.
-- A simple table updated by a trigger or periodic job.

CREATE TABLE IF NOT EXISTS city_offer_counts (
    city        text PRIMARY KEY,
    offer_count integer NOT NULL DEFAULT 0,
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- Trigger to maintain city_offer_counts on offer upsert.
CREATE OR REPLACE FUNCTION refresh_city_count()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.city IS NOT NULL AND NEW.city != '' THEN
        INSERT INTO city_offer_counts (city, offer_count, updated_at)
        VALUES (NEW.city, 1, now())
        ON CONFLICT (city) DO UPDATE
            SET offer_count = city_offer_counts.offer_count + 1,
                updated_at = now();
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_offers_city_count ON offers;
CREATE TRIGGER trg_offers_city_count
    AFTER INSERT OR UPDATE OF city ON offers
    FOR EACH ROW EXECUTE FUNCTION refresh_city_count();

COMMIT;

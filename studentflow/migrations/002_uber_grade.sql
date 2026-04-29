-- StudentFlow — Migration 002: Uber-grade columns
-- Run this AFTER the initial schema.sql has been applied.
-- Idempotent: every statement uses IF NOT EXISTS / IF EXISTS guards.
-- ---------------------------------------------------------------------------

BEGIN;

-- ---- offers: geo + employer contact ----------------------------------------
ALTER TABLE offers ADD COLUMN IF NOT EXISTS contact_email text DEFAULT '';
ALTER TABLE offers ADD COLUMN IF NOT EXISTS latitude double precision;
ALTER TABLE offers ADD COLUMN IF NOT EXISTS longitude double precision;

CREATE INDEX IF NOT EXISTS idx_offers_geo
    ON offers (latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- ---- students: geo ---------------------------------------------------------
ALTER TABLE students ADD COLUMN IF NOT EXISTS latitude double precision;
ALTER TABLE students ADD COLUMN IF NOT EXISTS longitude double precision;

CREATE INDEX IF NOT EXISTS idx_students_geo
    ON students (latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- ---- matches: accept/decline lifecycle + distance --------------------------
ALTER TABLE matches ADD COLUMN IF NOT EXISTS token text;
ALTER TABLE matches ADD COLUMN IF NOT EXISTS state text NOT NULL DEFAULT 'pending';
ALTER TABLE matches ADD COLUMN IF NOT EXISTS distance_km double precision;
ALTER TABLE matches ADD COLUMN IF NOT EXISTS accepted_at timestamptz;
ALTER TABLE matches ADD COLUMN IF NOT EXISTS declined_at timestamptz;

-- Backfill tokens for any existing matches that predate this migration.
-- Each gets a unique random token so accept links work retroactively.
UPDATE matches
   SET token = encode(gen_random_bytes(18), 'base64')
 WHERE token IS NULL;

-- Now make token NOT NULL + unique for future inserts.
ALTER TABLE matches ALTER COLUMN token SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_matches_token ON matches (token);

-- Fast lookup for accept/decline: state filtering + student inbox.
CREATE INDEX IF NOT EXISTS idx_matches_state ON matches (state);

COMMIT;

-- Migration 003 — Salary fields on offers + min_hourly_salary on students,
-- plus an expiration timestamp on offers so the MatcherAgent can stop pushing
-- notifications for offers that are no longer hiring.
--
-- Apply only to projects that already have schema 002. Fresh installs get
-- everything from schema.sql directly. Idempotent: safe to re-run.

alter table offers
    add column if not exists salary_min    double precision,
    add column if not exists salary_max    double precision,
    add column if not exists salary_period text,
    add column if not exists expires_at    timestamptz;

create index if not exists idx_offers_expires_at on offers (expires_at)
    where expires_at is not null;

alter table students
    add column if not exists min_hourly_salary double precision;

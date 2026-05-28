"""Tests for the SEO module: slugs, schema.org, sitemap, routes."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from studentflow.api import app
from studentflow.models import ContractType, Offer, Source
from studentflow.seo.pages import render_city_index, render_city_page, render_offer_page
from studentflow.seo.schema_org import build_job_posting_schema, schema_to_script_tag
from studentflow.seo.sitemap import SitemapGenerator
from studentflow.seo.slug import city_slug, offer_slug, skill_slug, slugify

client = TestClient(app)


# ---- slug ----


def test_slugify_basic():
    assert slugify("Serveur H/F - Paris") == "serveur-hf-paris"


def test_slugify_accents():
    assert slugify("Réceptionniste à Nîmes") == "receptionniste-a-nimes"


def test_slugify_max_len():
    long = "a" * 200
    assert len(slugify(long, max_len=80)) <= 80


def test_offer_slug_unique_suffix(make_offer):
    o = make_offer()
    slug = offer_slug(o)
    short_id = str(o.id).replace("-", "")[:8]
    assert slug.endswith(short_id)


def test_city_slug():
    assert city_slug("Saint-Étienne") == "saint-etienne"


def test_skill_slug():
    assert skill_slug("Community Management") == "community-management"


# ---- schema.org ----


def test_build_job_posting_schema_required_fields(make_offer):
    o = make_offer(contract=ContractType.INTERNSHIP, city="Lyon")
    schema = build_job_posting_schema(o, page_url="https://test.fr/offres/slug")
    assert schema["@context"] == "https://schema.org"
    assert schema["@type"] == "JobPosting"
    assert schema["employmentType"] == "INTERN"
    assert "datePosted" in schema
    assert "validThrough" in schema


def test_build_job_posting_schema_remote(make_offer):
    o = make_offer(remote=True)
    schema = build_job_posting_schema(o, page_url="https://test.fr/o/s")
    assert schema.get("jobLocationType") == "TELECOMMUTE"
    assert "applicantLocationRequirements" in schema


def test_schema_to_script_tag(make_offer):
    o = make_offer()
    schema = build_job_posting_schema(o, page_url="https://test.fr/o/s")
    tag = schema_to_script_tag(schema)
    assert 'type="application/ld+json"' in tag
    assert "JobPosting" in tag


# ---- sitemap ----


def test_sitemap_contains_home():
    gen = SitemapGenerator("https://example.com")
    entries = gen.build_entries([], [], [])
    xml = gen.generate(entries)
    assert "https://example.com/" in xml


def test_sitemap_contains_city(make_offer):
    gen = SitemapGenerator("https://example.com")
    entries = gen.build_entries([], ["paris"], [])
    xml = gen.generate(entries)
    assert "/emplois/paris" in xml


def test_sitemap_contains_offer():
    gen = SitemapGenerator("https://example.com")
    entries = gen.build_entries([("my-offer-slug-abc12345", datetime.utcnow())], [], [])
    xml = gen.generate(entries)
    assert "/offres/my-offer-slug-abc12345" in xml


def test_sitemap_valid_xml():
    from xml.etree import ElementTree as ET
    gen = SitemapGenerator("https://example.com")
    entries = gen.build_entries([], ["lyon"], ["python"])
    xml = gen.generate(entries)
    root = ET.fromstring(xml)
    assert root.tag.endswith("urlset")


# ---- HTTP routes ----


def test_robots_txt():
    resp = client.get("/robots.txt")
    assert resp.status_code == 200
    assert "User-agent" in resp.text
    assert "/sitemap.xml" in resp.text


def test_sitemap_xml_returns_xml():
    resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    assert "urlset" in resp.text


def test_emplois_index():
    resp = client.get("/emplois")
    assert resp.status_code == 200
    assert "StudentFlow" in resp.text


def test_emplois_city_page():
    resp = client.get("/emplois/paris")
    assert resp.status_code == 200
    assert "paris" in resp.text.lower()


def test_offer_page_404_unknown_slug():
    resp = client.get("/offres/unknown-slug-zzzzzzzz")
    assert resp.status_code == 404


# ---- enhanced matching freshness ----


def test_freshness_recent_offer(make_offer):
    from studentflow.matching import _score_freshness
    o = make_offer(scraped_at=datetime.now(tz=timezone.utc))
    score, reason = _score_freshness(o)
    assert score == 1.0
    assert "récente" in reason


def test_freshness_old_offer(make_offer):
    from datetime import timedelta
    from studentflow.matching import _score_freshness
    old_dt = datetime.now(tz=timezone.utc) - timedelta(days=45)
    o = make_offer(scraped_at=old_dt)
    score, reason = _score_freshness(o)
    assert score == 0.0


def test_quality_complete_offer(make_offer):
    from studentflow.matching import _score_quality
    o = make_offer(
        description="Belle mission",
        skills=["python"],
        hours_per_week=20,
        company="ACME",
        city="Paris",
    )
    score, _ = _score_quality(o)
    assert score == 1.0


def test_quality_incomplete_offer(make_offer):
    from studentflow.matching import _score_quality
    o = make_offer(description="", skills=[], hours_per_week=None, company="", city="")
    score, _ = _score_quality(o)
    assert score < 0.5


# ---- fixtures ----


@pytest.fixture
def make_offer():
    def _factory(**kwargs):
        defaults = dict(
            source=Source.STUDENTJOB,
            source_id="test-001",
            title="Serveur H/F",
            company="Restaurant Le Zinc",
            city="Paris",
            contract=ContractType.PART_TIME,
            description="Service en salle",
            skills=["restauration"],
            hours_per_week=15,
            scraped_at=datetime.now(tz=timezone.utc),
        )
        defaults.update(kwargs)
        return Offer(**defaults)
    return _factory

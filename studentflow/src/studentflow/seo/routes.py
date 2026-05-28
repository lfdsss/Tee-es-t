"""FastAPI router for all SEO-facing routes.

Mounted on the main app so every SEO URL lives on the same domain as the API.
In production, the reverse proxy (Caddy/nginx) should:
  - Route /sitemap.xml and /robots.txt to this API
  - Route /offres/* and /emplois/* to this API (or the SSR frontend)
  - Route everything else to the React SPA

Cache strategy:
  - sitemap.xml: 1 hour (offers change frequently but full re-gen is cheap)
  - robots.txt: 7 days (static for our use case)
  - offer pages: 30 minutes (offers rarely edit after posting)
  - city pages: 15 minutes (new offers arrive continuously)
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response

from ..config import get_settings
from ..db import InMemoryRepository, Repository, SupabaseRepository
from .pages import render_city_index, render_city_page, render_offer_page
from .sitemap import SitemapEntry, SitemapGenerator
from .slug import city_slug, offer_slug, skill_slug

log = logging.getLogger(__name__)

router = APIRouter(tags=["seo"])

_ROBOTS_TXT = """User-agent: *
Allow: /

# SEO landing pages
Allow: /offres/
Allow: /emplois/
Allow: /sitemap.xml

# Block API internals from index
Disallow: /students/
Disallow: /m/
Disallow: /skills/extract
Disallow: /stats/

Sitemap: {base_url}/sitemap.xml
"""


def _get_repo() -> Repository:
    settings = get_settings()
    if settings.supabase_configured:
        return SupabaseRepository(settings)
    return InMemoryRepository()


@router.get("/robots.txt", response_class=Response)
def robots_txt() -> Response:
    settings = get_settings()
    content = _ROBOTS_TXT.format(base_url=settings.public_base_url)
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=604800"},  # 7 days
    )


@router.get("/sitemap.xml", response_class=Response)
def sitemap_xml(repo: Repository = Depends(_get_repo)) -> Response:
    settings = get_settings()
    generator = SitemapGenerator(base_url=settings.public_base_url)

    # Collect offer slugs + scraped_at for individual offer URLs.
    try:
        offers = repo.list_recent_unmatched_offers(limit=5000)
    except Exception:
        offers = []

    offer_slug_pairs: list[tuple[str, datetime | None]] = [
        (offer_slug(o), o.scraped_at) for o in offers
    ]

    # Unique city slugs from live offers.
    city_slugs: list[str] = []
    seen_cities: set[str] = set()
    for o in offers:
        if o.city:
            cs = city_slug(o.city)
            if cs not in seen_cities:
                seen_cities.add(cs)
                city_slugs.append(cs)

    # Skill slugs (top 20 canonical skills).
    from ..utils.skills import VOCABULARY
    skill_slugs = [skill_slug(s) for s in VOCABULARY[:20]]

    entries = generator.build_entries(
        offer_slugs=offer_slug_pairs,
        cities=city_slugs,
        skills=skill_slugs,
    )
    xml = generator.generate(entries)

    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=3600"},  # 1 hour
    )


@router.get("/offres/{slug}", response_class=HTMLResponse)
def offer_page(slug: str, repo: Repository = Depends(_get_repo)) -> HTMLResponse:
    """SEO-crawlable HTML page for a single offer, identified by slug.

    The slug encodes the 8-char UUID suffix, which we use to look up the offer.
    This means the rest of the slug can change (e.g. if the company renames)
    without breaking the URL — we just 301-redirect old slugs.
    """
    settings = get_settings()

    # Extract short UUID from last segment after the last '-'.
    short_id = slug.rsplit("-", 1)[-1] if "-" in slug else slug

    try:
        offers = repo.list_recent_unmatched_offers(limit=5000)
    except Exception:
        offers = []

    # Match by short_id suffix (first 8 chars of UUID without dashes).
    offer = None
    for o in offers:
        if str(o.id).replace("-", "")[:8] == short_id:
            offer = o
            break

    if offer is None:
        raise HTTPException(status_code=404, detail="Offre introuvable")

    canonical_slug = offer_slug(offer)

    # If the slug in the URL is stale (title changed), issue a permanent redirect
    # so SEO equity flows to the canonical URL. We can't do a real redirect in
    # FastAPI without returning Response — keep it simple: serve with canonical.
    html = render_offer_page(
        offer,
        slug=canonical_slug,
        platform_url=settings.public_base_url,
        api_url=settings.public_base_url,
    )
    return HTMLResponse(
        content=html,
        headers={"Cache-Control": "public, max-age=1800"},  # 30 min
    )


@router.get("/emplois", response_class=HTMLResponse)
def city_index(repo: Repository = Depends(_get_repo)) -> HTMLResponse:
    settings = get_settings()

    try:
        offers = repo.list_recent_unmatched_offers(limit=5000)
    except Exception:
        offers = []

    # Aggregate offers by city.
    city_counts: dict[str, int] = {}
    for o in offers:
        if o.city:
            city_counts[o.city] = city_counts.get(o.city, 0) + 1

    cities = [
        {"name": city.title(), "slug": city_slug(city), "count": count}
        for city, count in sorted(city_counts.items(), key=lambda x: -x[1])
    ]

    html = render_city_index(cities, platform_url=settings.public_base_url)
    return HTMLResponse(
        content=html,
        headers={"Cache-Control": "public, max-age=900"},  # 15 min
    )


@router.get("/emplois/{city}", response_class=HTMLResponse)
def city_offers(city: str, repo: Repository = Depends(_get_repo)) -> HTMLResponse:
    return _render_city_skill_page(city, skill=None, repo=repo)


@router.get("/emplois/{city}/{skill}", response_class=HTMLResponse)
def city_skill_offers(
    city: str, skill: str, repo: Repository = Depends(_get_repo)
) -> HTMLResponse:
    return _render_city_skill_page(city, skill=skill, repo=repo)


def _render_city_skill_page(
    city: str, skill: str | None, repo: Repository
) -> HTMLResponse:
    settings = get_settings()

    try:
        offers = repo.list_recent_unmatched_offers(limit=5000)
    except Exception:
        offers = []

    # Normalize the URL city slug back to plain text for comparison.
    city_norm = city.lower().replace("-", " ")

    filtered = [
        o for o in offers
        if _city_matches(o.city, city_norm)
        and (skill is None or skill.lower().replace("-", " ") in o.skills)
    ]

    previews = [
        {
            "slug": offer_slug(o),
            "title": o.title,
            "company": o.company,
            "contract": o.contract.value,
        }
        for o in filtered[:30]
    ]

    html = render_city_page(
        city_norm,
        previews,
        skill_filter=skill,
        platform_url=settings.public_base_url,
    )
    return HTMLResponse(
        content=html,
        headers={"Cache-Control": "public, max-age=900"},
    )


def _city_matches(offer_city: str, url_city: str) -> bool:
    """Fuzzy city match: both are lowercased, hyphens stripped."""
    return offer_city.lower().replace("-", " ") == url_city

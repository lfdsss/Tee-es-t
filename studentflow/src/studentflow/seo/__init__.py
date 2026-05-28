"""SEO engine for StudentFlow.

Handles:
- URL slug generation for offers
- JobPosting schema.org JSON-LD (Google Jobs integration)
- Dynamic XML sitemap
- Programmatic landing pages (city × skill × contract)
- robots.txt
- HTML meta tags + Open Graph
"""

from .schema_org import build_job_posting_schema
from .sitemap import SitemapGenerator
from .slug import offer_slug, slugify

__all__ = [
    "SitemapGenerator",
    "build_job_posting_schema",
    "offer_slug",
    "slugify",
]

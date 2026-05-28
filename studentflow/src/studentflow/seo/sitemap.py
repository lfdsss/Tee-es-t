"""Dynamic XML sitemap generator.

A sitemap tells search engines which URLs exist, how important they are, and
how often they change. For a job platform the key insight is:

  - City/skill landing pages (priority 0.8) change when new offers arrive.
  - Individual offer pages (priority 0.6) change quickly → daily changefreq.
  - Home page (priority 1.0) is the most important.

We generate the sitemap on demand (via GET /sitemap.xml) rather than writing
a file, so it always reflects live DB state. The API response includes
Cache-Control: max-age=3600 so Googlebot caches it and we don't hit the DB
on every ping.

Format: Sitemap Protocol 0.9 (https://www.sitemaps.org/protocol.html)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


@dataclass
class SitemapEntry:
    loc: str
    lastmod: str | None = None
    changefreq: str = "weekly"
    priority: float = 0.5


class SitemapGenerator:
    """Build a sitemap XML string from a list of entries."""

    def __init__(self, base_url: str) -> None:
        # Strip trailing slash once.
        self.base_url = base_url.rstrip("/")

    def generate(self, entries: Iterable[SitemapEntry]) -> str:
        lines: list[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        for e in entries:
            lines.append("  <url>")
            lines.append(f"    <loc>{self._escape(e.loc)}</loc>")
            if e.lastmod:
                lines.append(f"    <lastmod>{e.lastmod}</lastmod>")
            lines.append(f"    <changefreq>{e.changefreq}</changefreq>")
            lines.append(f"    <priority>{e.priority:.1f}</priority>")
            lines.append("  </url>")
        lines.append("</urlset>")
        return "\n".join(lines)

    def build_entries(
        self,
        offer_slugs: list[tuple[str, datetime | None]],
        cities: list[str],
        skills: list[str],
    ) -> list[SitemapEntry]:
        """Build the full entry list for StudentFlow.

        Args:
            offer_slugs: list of (slug, scraped_at) tuples for individual offers.
            cities: unique city slugs with active offers.
            skills: canonical skill slugs.
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        entries: list[SitemapEntry] = []

        # Home page
        entries.append(
            SitemapEntry(
                loc=self.base_url + "/",
                lastmod=today,
                changefreq="daily",
                priority=1.0,
            )
        )

        # Static informational pages
        for path in ["/comment-ca-marche", "/pour-les-entreprises", "/a-propos"]:
            entries.append(
                SitemapEntry(
                    loc=self.base_url + path,
                    changefreq="monthly",
                    priority=0.5,
                )
            )

        # City landing pages (high priority — programmatic SEO goldmine)
        entries.append(
            SitemapEntry(
                loc=self.base_url + "/emplois",
                lastmod=today,
                changefreq="daily",
                priority=0.9,
            )
        )
        for city in cities:
            entries.append(
                SitemapEntry(
                    loc=f"{self.base_url}/emplois/{city}",
                    lastmod=today,
                    changefreq="daily",
                    priority=0.8,
                )
            )
            # City × skill pages (long-tail — highest volume SEO traffic)
            for skill in skills[:20]:  # top 20 skills per city
                entries.append(
                    SitemapEntry(
                        loc=f"{self.base_url}/emplois/{city}/{skill}",
                        lastmod=today,
                        changefreq="weekly",
                        priority=0.7,
                    )
                )

        # Individual offer pages
        for slug, scraped_at in offer_slugs:
            lastmod = scraped_at.strftime("%Y-%m-%d") if scraped_at else today
            entries.append(
                SitemapEntry(
                    loc=f"{self.base_url}/offres/{slug}",
                    lastmod=lastmod,
                    changefreq="daily",
                    priority=0.6,
                )
            )

        return entries

    @staticmethod
    def _escape(url: str) -> str:
        return (
            url.replace("&", "&amp;")
            .replace("'", "&apos;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

"""JobTeaser scraper — NOT YET IMPLEMENTED.

JobTeaser (Career Center partner for many schools) requires authenticated
access per school. Typical flow: OAuth via the school's portal. Out of
scope for the MVP; leave as a stub.
"""

from __future__ import annotations

import logging

from ..models import Offer, Source
from .base import BaseScraper

log = logging.getLogger(__name__)


class JobTeaserScraper(BaseScraper):
    source = Source.JOBTEASER

    async def fetch(self) -> list[Offer]:
        log.info("JobTeaserScraper: not implemented, returning empty batch")
        return []

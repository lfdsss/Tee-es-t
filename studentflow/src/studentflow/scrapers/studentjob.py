"""StudentJob scraper — NOT YET IMPLEMENTED.

Target: https://www.studentjob.fr/ — no public API, HTML scraping required.
Start from the listing page and paginate.
"""

from __future__ import annotations

import logging

from ..models import Offer, Source
from .base import BaseScraper

log = logging.getLogger(__name__)


class StudentJobScraper(BaseScraper):
    source = Source.STUDENTJOB

    async def fetch(self) -> list[Offer]:
        log.info("StudentJobScraper: not implemented, returning empty batch")
        return []

"""Abstract base scraper class."""
from __future__ import annotations

import datetime
import logging
from abc import ABC, abstractmethod

from playwright.async_api import Page

from lp_radar.filters import is_fund_related
from lp_radar.models import Announcement

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all site scrapers.

    Subclasses must define:
        name: str         - Korean name (e.g. "한국벤처캐피탈협회")
        short_name: str   - Abbreviation (e.g. "KVCA")
        base_url: str     - Target URL to scrape

    Subclasses must implement:
        extract_announcements(page) -> list[Announcement]
    """

    name: str
    short_name: str
    base_url: str

    async def run(self, page: Page, cutoff_date: datetime.date) -> list[Announcement]:
        """Main entry point: navigate, wait, extract, filter by date."""
        await self.navigate(page)
        await self.wait_for_content(page)
        raw = await self.extract_announcements(page)

        # Mark fund-related
        for ann in raw:
            ann.is_fund_related = is_fund_related(ann.title)

        # Filter by cutoff date
        filtered = []
        for ann in raw:
            if ann.date is None:
                # Include announcements with unparseable dates
                filtered.append(ann)
            elif ann.date >= cutoff_date:
                filtered.append(ann)

        return filtered

    async def navigate(self, page: Page) -> None:
        """Navigate to the target page. Override for multi-step navigation."""
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=30_000)

    async def wait_for_content(self, page: Page) -> None:
        """Wait for page content to be ready. Override for JS-heavy sites."""
        try:
            await page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            # networkidle can sometimes timeout; continue with what we have
            logger.debug(f"{self.short_name}: networkidle timeout, proceeding anyway")

    @abstractmethod
    async def extract_announcements(self, page: Page) -> list[Announcement]:
        """Extract announcements from the page. Must be implemented per site."""
        ...

    def make_announcement(
        self, title: str, date: datetime.date | None, url: str
    ) -> Announcement:
        """Helper to create an Announcement with source fields pre-filled."""
        return Announcement(
            source=self.name,
            source_short=self.short_name,
            title=title,
            date=date,
            url=url,
        )

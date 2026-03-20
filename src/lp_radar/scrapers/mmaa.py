"""군인공제회 (MMAA) scraper."""
from __future__ import annotations

from playwright.async_api import Page

from lp_radar.base_scraper import BaseScraper
from lp_radar.models import Announcement
from lp_radar.registry import register
from lp_radar.utils import make_absolute_url, parse_korean_date


@register
class MmaaScraper(BaseScraper):
    name = "군인공제회"
    short_name = "MMAA"
    base_url = "https://www.mmaa.or.kr/web/contents/notice.do"

    async def wait_for_content(self, page: Page) -> None:
        try:
            await page.wait_for_selector("table, .board_list, .notice-list", timeout=15_000)
        except Exception:
            await page.wait_for_timeout(5000)

    async def extract_announcements(self, page: Page) -> list[Announcement]:
        results: list[Announcement] = []

        rows = await page.query_selector_all("table tbody tr")
        if not rows:
            rows = await page.query_selector_all(".board_list li, .notice-list li")

        for row in rows:
            try:
                link = await row.query_selector("a")
                if not link:
                    continue

                title = (await link.inner_text()).strip()
                if not title or len(title) < 2:
                    continue

                href = await link.get_attribute("href")
                url = make_absolute_url(self.base_url, href) if href else self.base_url

                date = None
                tds = await row.query_selector_all("td, span, .date")
                for td in tds:
                    text = (await td.inner_text()).strip()
                    parsed = parse_korean_date(text)
                    if parsed:
                        date = parsed
                        break

                results.append(self.make_announcement(title, date, url))
            except Exception:
                continue

        return results

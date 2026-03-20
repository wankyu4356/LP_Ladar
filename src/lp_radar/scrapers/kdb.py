"""산업은행 (KDB) scraper."""
from __future__ import annotations

from playwright.async_api import Page

from lp_radar.base_scraper import BaseScraper
from lp_radar.models import Announcement
from lp_radar.registry import register
from lp_radar.utils import make_absolute_url, parse_korean_date


@register
class KdbScraper(BaseScraper):
    name = "산업은행"
    short_name = "KDB"
    base_url = "https://www.kdb.co.kr/CHBIPR23N00.act?_mnuId=IHIHIR0087"

    async def wait_for_content(self, page: Page) -> None:
        try:
            await page.wait_for_selector("table, .board_list, .listTable", timeout=15_000)
        except Exception:
            await page.wait_for_timeout(5000)

    async def extract_announcements(self, page: Page) -> list[Announcement]:
        results: list[Announcement] = []

        rows = await page.query_selector_all("table tbody tr")
        if not rows:
            rows = await page.query_selector_all("table tr")

        for row in rows:
            try:
                link = await row.query_selector("a")
                if not link:
                    continue

                title = (await link.inner_text()).strip()
                if not title or len(title) < 2:
                    continue

                href = await link.get_attribute("href")
                onclick = await link.get_attribute("onclick")

                url = self.base_url
                if href and href not in ("#", "javascript:void(0)", "javascript:;"):
                    url = make_absolute_url(self.base_url, href)

                date = None
                tds = await row.query_selector_all("td")
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

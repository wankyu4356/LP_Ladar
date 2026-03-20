"""한국벤처투자 (KVIC) scraper."""
from __future__ import annotations

from playwright.async_api import Page

from lp_radar.base_scraper import BaseScraper
from lp_radar.models import Announcement
from lp_radar.registry import register
from lp_radar.utils import make_absolute_url, parse_korean_date


@register
class KvicScraper(BaseScraper):
    name = "한국벤처투자"
    short_name = "KVIC"
    base_url = "https://www.kvic.or.kr/notice/notice1_1"

    async def wait_for_content(self, page: Page) -> None:
        await page.wait_for_selector("table, .board-list, .notice-list, .bbs_list", timeout=15_000)

    async def extract_announcements(self, page: Page) -> list[Announcement]:
        results: list[Announcement] = []

        rows = await page.query_selector_all("table tbody tr")
        if not rows:
            rows = await page.query_selector_all(".board-list li, .notice-list li")

        for row in rows:
            try:
                link = await row.query_selector("a")
                if not link:
                    continue

                title = (await link.inner_text()).strip()
                if not title:
                    continue

                href = await link.get_attribute("href")
                url = make_absolute_url(self.base_url, href) if href else self.base_url

                # Find date
                date = None
                date_el = await row.query_selector(".date, .td_date, td:last-child")
                if date_el:
                    date_text = (await date_el.inner_text()).strip()
                    date = parse_korean_date(date_text)

                if not date:
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

"""총회연금재단 scraper."""
from __future__ import annotations

from playwright.async_api import Page

from lp_radar.base_scraper import BaseScraper
from lp_radar.models import Announcement
from lp_radar.registry import register
from lp_radar.utils import make_absolute_url, parse_korean_date


@register
class PensionScraper(BaseScraper):
    name = "총회연금재단"
    short_name = "PENSION"
    base_url = "https://www.pension.or.kr/modu/s_board/list.asp?board_seq=1&lef=05&sublef=undefined"

    async def wait_for_content(self, page: Page) -> None:
        try:
            await page.wait_for_selector("table, .board_list, .bbs_list", timeout=15_000)
        except Exception:
            await page.wait_for_timeout(3000)

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
                url = make_absolute_url(self.base_url, href) if href else self.base_url

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

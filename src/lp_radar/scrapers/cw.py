"""건설근로자공제회 scraper."""
from __future__ import annotations

from playwright.async_api import Page

from lp_radar.base_scraper import BaseScraper
from lp_radar.models import Announcement
from lp_radar.registry import register
from lp_radar.utils import make_absolute_url, parse_korean_date


@register
class CwScraper(BaseScraper):
    name = "건설근로자공제회"
    short_name = "CW"
    base_url = "https://cw.or.kr/cid/board/board.do?boardConfigNo=3&memberLevel=3&termNo=3"

    async def navigate(self, page: Page) -> None:
        # This site may redirect; handle gracefully
        try:
            await page.goto(self.base_url, wait_until="domcontentloaded", timeout=30_000)
        except Exception:
            # May redirect to different URL
            await page.wait_for_timeout(3000)

    async def wait_for_content(self, page: Page) -> None:
        try:
            await page.wait_for_selector("table, .board_list, .boardList", timeout=15_000)
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

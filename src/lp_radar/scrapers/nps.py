"""국민연금 (NPS) scraper."""
from __future__ import annotations

from playwright.async_api import Page

from lp_radar.base_scraper import BaseScraper
from lp_radar.models import Announcement
from lp_radar.registry import register
from lp_radar.utils import make_absolute_url, parse_korean_date


@register
class NpsScraper(BaseScraper):
    name = "국민연금"
    short_name = "NPS"
    base_url = "https://fund.nps.or.kr/jsppage/fund/prs/prs_04.jsp"

    async def wait_for_content(self, page: Page) -> None:
        try:
            # NPS uses JSP with dynamic rendering
            await page.wait_for_selector("table, .board_list, #contents", timeout=15_000)
        except Exception:
            await page.wait_for_timeout(5000)

    async def extract_announcements(self, page: Page) -> list[Announcement]:
        results: list[Announcement] = []

        # Try various selectors for NPS board
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
                if href and href != "#" and href != "javascript:void(0)":
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

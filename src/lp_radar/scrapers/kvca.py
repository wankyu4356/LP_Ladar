"""한국벤처캐피탈협회 (KVCA) scraper."""
from __future__ import annotations

from playwright.async_api import Page

from lp_radar.base_scraper import BaseScraper
from lp_radar.models import Announcement
from lp_radar.registry import register
from lp_radar.utils import make_absolute_url, parse_korean_date


@register
class KvcaScraper(BaseScraper):
    name = "한국벤처캐피탈협회"
    short_name = "KVCA"
    base_url = "https://www.kvca.or.kr/Program/invest/list.html?a_gb=board&a_cd=8&a_item=0&sm=2_2_2"

    async def wait_for_content(self, page: Page) -> None:
        await page.wait_for_selector("table, .board_list, .bbs_list, .list_table", timeout=15_000)

    async def extract_announcements(self, page: Page) -> list[Announcement]:
        results: list[Announcement] = []

        # Try common Korean board table patterns
        rows = await page.query_selector_all("table tbody tr")
        if not rows:
            rows = await page.query_selector_all(".board_list tr, .bbs_list tr")

        for row in rows:
            try:
                # Find title link
                link = await row.query_selector("a")
                if not link:
                    continue

                title = (await link.inner_text()).strip()
                if not title:
                    continue

                href = await link.get_attribute("href")
                onclick = await link.get_attribute("onclick")

                # Build URL from href or onclick
                url = self.base_url
                if href and href != "#":
                    url = make_absolute_url(self.base_url, href)
                elif onclick:
                    # Extract URL or ID from onclick if present
                    url = self.base_url

                # Find date - usually in a td with date-like content
                tds = await row.query_selector_all("td")
                date = None
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

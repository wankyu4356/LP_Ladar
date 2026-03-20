"""Async orchestrator - runs all scrapers with concurrency control, retry, and screenshot capture."""
from __future__ import annotations

import asyncio
import datetime
import logging
from pathlib import Path

from playwright.async_api import async_playwright

from lp_radar.base_scraper import BaseScraper
from lp_radar.config import (
    LOCALE,
    MAX_CONCURRENT_TABS,
    MAX_RETRIES,
    RETRY_DELAY_SEC,
    SCREENSHOT_DIR,
    USER_AGENT,
    VIEWPORT,
)
from lp_radar.models import Announcement, ScrapeError

logger = logging.getLogger(__name__)


def _find_chromium() -> str | None:
    """Find a pre-installed Chromium executable."""
    import shutil

    # Check standard playwright cache locations
    cache_dir = Path.home() / ".cache" / "ms-playwright"
    if cache_dir.exists():
        # Look for chromium directories sorted by version (newest first)
        for pattern in ["chromium-*/chrome-linux/chrome", "chromium-*/chrome-linux64/chrome"]:
            from glob import glob
            matches = sorted(glob(str(cache_dir / pattern)), reverse=True)
            if matches:
                return matches[0]

    # Check system chromium
    for name in ["chromium-browser", "chromium", "google-chrome", "google-chrome-stable"]:
        path = shutil.which(name)
        if path:
            return path

    return None


async def run_all(
    scrapers: list[BaseScraper],
    cutoff_date: datetime.date,
    concurrency: int = MAX_CONCURRENT_TABS,
) -> tuple[list[Announcement], list[ScrapeError]]:
    """Run all scrapers concurrently and collect results."""
    all_announcements: list[Announcement] = []
    all_errors: list[ScrapeError] = []
    lock = asyncio.Lock()

    async with async_playwright() as pw:
        launch_kwargs: dict = {"headless": True}
        # Try to find pre-installed chromium if default fails
        chromium_path = _find_chromium()
        if chromium_path:
            launch_kwargs["executable_path"] = chromium_path
        browser = await pw.chromium.launch(**launch_kwargs)
        semaphore = asyncio.Semaphore(concurrency)

        async def run_one(scraper: BaseScraper) -> None:
            async with semaphore:
                results, error = await _run_with_retry(browser, scraper, cutoff_date)
                async with lock:
                    all_announcements.extend(results)
                    if error:
                        all_errors.append(error)

        tasks = [run_one(s) for s in scrapers]
        await asyncio.gather(*tasks)
        await browser.close()

    # Sort by date descending
    all_announcements.sort(key=lambda a: a.date or datetime.date.min, reverse=True)
    return all_announcements, all_errors


async def _run_with_retry(
    browser, scraper: BaseScraper, cutoff_date: datetime.date
) -> tuple[list[Announcement], ScrapeError | None]:
    """Run a scraper with retry logic and screenshot on final failure."""
    last_error: str = ""

    for attempt in range(1, MAX_RETRIES + 1):
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale=LOCALE,
            viewport=VIEWPORT,
        )
        page = await context.new_page()

        try:
            logger.info(f"[{scraper.short_name}] Attempt {attempt}/{MAX_RETRIES}")
            results = await scraper.run(page, cutoff_date)
            logger.info(f"[{scraper.short_name}] Found {len(results)} announcements")
            await context.close()
            return results, None

        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.warning(f"[{scraper.short_name}] Attempt {attempt} failed: {last_error}")

            # On final failure, capture screenshot
            if attempt == MAX_RETRIES:
                screenshot_path = await _capture_screenshot(page, scraper.short_name)
                await context.close()
                return [], ScrapeError(
                    source=scraper.name,
                    source_short=scraper.short_name,
                    url=scraper.base_url,
                    error_message=last_error,
                    screenshot_path=str(screenshot_path) if screenshot_path else None,
                )
            else:
                await context.close()
                await asyncio.sleep(RETRY_DELAY_SEC)

    # Should not reach here
    return [], None


async def _capture_screenshot(page, short_name: str) -> Path | None:
    """Capture a screenshot of the current page state."""
    try:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = SCREENSHOT_DIR / f"{short_name}_{timestamp}.png"
        await page.screenshot(path=str(path), full_page=True)
        logger.info(f"[{short_name}] Screenshot saved: {path}")
        return path
    except Exception as e:
        logger.warning(f"[{short_name}] Failed to capture screenshot: {e}")
        return None

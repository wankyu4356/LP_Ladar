"""Configuration constants."""
import os
from pathlib import Path

# Concurrency
MAX_CONCURRENT_TABS = 4

# Timeouts (ms)
PAGE_TIMEOUT = 30_000
NETWORK_IDLE_TIMEOUT = 15_000

# Retry
MAX_RETRIES = 3
RETRY_DELAY_SEC = 2

# Output
OUTPUT_DIR = Path(os.environ.get("LP_RADAR_OUTPUT_DIR", "."))
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"

# Browser
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
VIEWPORT = {"width": 1920, "height": 1080}
LOCALE = "ko-KR"

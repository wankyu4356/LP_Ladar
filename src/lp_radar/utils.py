"""Utility functions for date parsing and URL handling."""
from __future__ import annotations

import datetime
import re
from urllib.parse import urljoin


def parse_korean_date(text: str, reference_year: int | None = None) -> datetime.date | None:
    """Parse various Korean date formats into a datetime.date.

    Supported formats:
    - 2026.03.20 / 2026-03-20 / 2026/03/20
    - 2026년 03월 20일
    - 03.20 / 03-20 / 03/20 (year omitted → use reference_year)
    - 20260320 (compact)
    """
    if reference_year is None:
        reference_year = datetime.date.today().year

    text = text.strip()

    # Full date: 2026.03.20 or 2026-03-20 or 2026/03/20
    m = re.match(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", text)
    if m:
        return _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # Korean format: 2026년 03월 20일
    m = re.match(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if m:
        return _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # Compact: 20260320
    m = re.match(r"(\d{4})(\d{2})(\d{2})$", text)
    if m:
        return _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # Short date without year: 03.20 or 03-20 or 03/20
    m = re.match(r"(\d{1,2})[.\-/](\d{1,2})$", text)
    if m:
        return _safe_date(reference_year, int(m.group(1)), int(m.group(2)))

    return None


def _safe_date(year: int, month: int, day: int) -> datetime.date | None:
    """Create a date object, returning None if invalid."""
    try:
        return datetime.date(year, month, day)
    except ValueError:
        return None


def make_absolute_url(base: str, href: str | None) -> str:
    """Convert a relative URL to absolute."""
    if not href:
        return base
    if href.startswith(("http://", "https://")):
        return href
    return urljoin(base, href)

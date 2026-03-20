"""Announcement data model."""
from __future__ import annotations

import dataclasses
import datetime


@dataclasses.dataclass
class Announcement:
    """A single fund-related announcement scraped from an institutional site."""

    source: str  # e.g. "한국벤처캐피탈협회"
    source_short: str  # e.g. "KVCA"
    title: str
    date: datetime.date | None
    url: str
    is_fund_related: bool = False

    def to_dict(self) -> dict:
        return {
            "기관명": self.source,
            "약칭": self.source_short,
            "제목": self.title,
            "날짜": self.date.isoformat() if self.date else "",
            "URL": self.url,
            "펀드관련": "Y" if self.is_fund_related else "N",
        }


@dataclasses.dataclass
class ScrapeError:
    """Record of a failed scrape attempt."""

    source: str
    source_short: str
    url: str
    error_message: str
    screenshot_path: str | None = None

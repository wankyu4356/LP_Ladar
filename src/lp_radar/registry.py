"""Scraper registry for auto-discovery."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lp_radar.base_scraper import BaseScraper

_REGISTRY: dict[str, type[BaseScraper]] = {}


def register(cls: type[BaseScraper]) -> type[BaseScraper]:
    """Class decorator to register a scraper."""
    _REGISTRY[cls.short_name] = cls
    return cls


def get_all_scrapers() -> list[BaseScraper]:
    """Instantiate and return all registered scrapers."""
    return [cls() for cls in _REGISTRY.values()]


def get_scrapers_by_names(names: list[str]) -> list[BaseScraper]:
    """Get scrapers filtered by short names."""
    result = []
    for name in names:
        upper = name.upper()
        if upper in _REGISTRY:
            result.append(_REGISTRY[upper]())
        else:
            print(f"[WARNING] Unknown scraper: {name}")
    return result

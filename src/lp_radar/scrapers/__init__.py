"""Auto-import all scraper modules to trigger registration."""
from lp_radar.scrapers import (
    kvca,
    kvic,
    kofia,
    kgrowth,
    samsung_fund,
    kbiz,
    tp,
    kamco,
    kpasset,
    nps,
    koreaexim,
    cw,
    mmaa,
    pension,
    sema,
    kdb,
    ktcu,
    geps,
    poba,
    moel,
)

__all__ = [
    "kvca", "kvic", "kofia", "kgrowth", "samsung_fund", "kbiz",
    "tp", "kamco", "kpasset", "nps", "koreaexim", "cw", "mmaa",
    "pension", "sema", "kdb", "ktcu", "geps", "poba", "moel",
]

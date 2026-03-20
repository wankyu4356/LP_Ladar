"""Flask web UI for LP Radar."""
from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import threading
from pathlib import Path

from flask import Flask, jsonify, render_template, send_file

from lp_radar.config import OUTPUT_DIR
from lp_radar.models import Announcement, ScrapeError
from lp_radar.registry import get_all_scrapers
from lp_radar.report import generate_excel
from lp_radar.runner import run_all

# Ensure scrapers are registered
import lp_radar.scrapers  # noqa: F401

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))

# ─── Global state ────────────────────────────────────────────────────────────

_state = {
    "status": "idle",  # idle | running | completed
    "progress": 0,
    "logs": [],
    "announcements": [],
    "errors": [],
    "total_sites": 0,
    "excel_path": None,
    "timestamp": None,
}
_lock = threading.Lock()


def _update_state(**kwargs):
    with _lock:
        _state.update(kwargs)


def _add_log(msg: str):
    with _lock:
        _state["logs"].append(msg)
        # Keep last 200 lines
        if len(_state["logs"]) > 200:
            _state["logs"] = _state["logs"][-200:]


# ─── Background scraper runner ───────────────────────────────────────────────

class _LogCaptureHandler(logging.Handler):
    """Captures log records and pushes them to the web state."""

    def emit(self, record):
        msg = self.format(record)
        _add_log(msg)


def _run_scraper_background(days: int, concurrency: int):
    """Run the scraper in a background thread."""
    _update_state(
        status="running",
        progress=0,
        logs=[],
        announcements=[],
        errors=[],
    )

    # Capture logs
    handler = _LogCaptureHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
    root_logger = logging.getLogger("lp_radar")
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    try:
        _add_log(f"스크래핑 시작: {days}일, 동시 {concurrency}탭")

        scrapers = get_all_scrapers()
        _update_state(total_sites=len(scrapers))
        _add_log(f"{len(scrapers)}개 사이트 스캔 시작...")

        cutoff_date = datetime.date.today() - datetime.timedelta(days=days)

        # Track per-site progress via a wrapper
        completed_count = 0
        total = len(scrapers)
        original_run_all = run_all

        # Run async code in a new event loop
        loop = asyncio.new_event_loop()
        announcements, errors = loop.run_until_complete(
            _run_all_with_progress(scrapers, cutoff_date, concurrency, total)
        )
        loop.close()

        # Generate Excel
        today = datetime.date.today()
        excel_path = OUTPUT_DIR / f"lp_radar_{today.strftime('%Y%m%d')}.xlsx"
        generate_excel(announcements, errors, excel_path)

        _update_state(
            status="completed",
            progress=100,
            announcements=[_ann_to_dict(a) for a in announcements],
            errors=[_err_to_dict(e) for e in errors],
            excel_path=str(excel_path),
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        fund_count = sum(1 for a in announcements if a.is_fund_related)
        _add_log(f"완료! 총 {len(announcements)}건 (펀드관련: {fund_count}건), 에러: {len(errors)}건")

    except Exception as e:
        _add_log(f"오류 발생: {e}")
        _update_state(status="completed", progress=100)
    finally:
        root_logger.removeHandler(handler)


async def _run_all_with_progress(
    scrapers, cutoff_date, concurrency, total
):
    """Wrapper around run_all that updates progress."""
    from lp_radar.base_scraper import BaseScraper
    from lp_radar.runner import _run_with_retry

    from playwright.async_api import async_playwright
    from lp_radar.config import USER_AGENT, LOCALE, VIEWPORT
    from lp_radar.runner import _find_chromium

    all_announcements: list[Announcement] = []
    all_errors: list[ScrapeError] = []
    completed = 0
    lock = asyncio.Lock()

    async with async_playwright() as pw:
        launch_kwargs: dict = {"headless": True}
        chromium_path = _find_chromium()
        if chromium_path:
            launch_kwargs["executable_path"] = chromium_path
        browser = await pw.chromium.launch(**launch_kwargs)
        semaphore = asyncio.Semaphore(concurrency)

        async def run_one(scraper: BaseScraper) -> None:
            nonlocal completed
            async with semaphore:
                _add_log(f"[{scraper.short_name}] 스크래핑 시작...")
                results, error = await _run_with_retry(browser, scraper, cutoff_date)
                async with lock:
                    all_announcements.extend(results)
                    if error:
                        all_errors.append(error)
                    completed += 1
                    pct = int(completed / total * 100)
                    _update_state(progress=pct)

                if error:
                    _add_log(f"[{scraper.short_name}] 실패: {error.error_message[:80]}")
                else:
                    _add_log(f"[{scraper.short_name}] {len(results)}건 수집 완료")

        tasks = [run_one(s) for s in scrapers]
        await asyncio.gather(*tasks)
        await browser.close()

    all_announcements.sort(key=lambda a: a.date or datetime.date.min, reverse=True)
    return all_announcements, all_errors


def _ann_to_dict(a: Announcement) -> dict:
    return {
        "source": a.source,
        "source_short": a.source_short,
        "title": a.title,
        "date": a.date.isoformat() if a.date else None,
        "url": a.url,
        "is_fund_related": a.is_fund_related,
    }


def _err_to_dict(e: ScrapeError) -> dict:
    return {
        "source": e.source,
        "source_short": e.source_short,
        "url": e.url,
        "error_message": e.error_message,
        "screenshot_path": e.screenshot_path,
    }


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/run", methods=["POST"])
def api_run():
    from flask import request

    with _lock:
        if _state["status"] == "running":
            return jsonify({"status": "already_running"})

    data = request.get_json() or {}
    days = data.get("days", 10)
    concurrency = data.get("concurrency", 4)

    thread = threading.Thread(
        target=_run_scraper_background,
        args=(days, concurrency),
        daemon=True,
    )
    thread.start()

    return jsonify({"status": "started"})


@app.route("/api/status")
def api_status():
    with _lock:
        return jsonify({
            "status": _state["status"],
            "progress": _state["progress"],
            "logs": _state["logs"][-50:],  # Last 50 lines
            "has_results": len(_state["announcements"]) > 0 or len(_state["errors"]) > 0,
        })


@app.route("/api/results")
def api_results():
    with _lock:
        return jsonify({
            "announcements": _state["announcements"],
            "errors": _state["errors"],
            "total_sites": _state["total_sites"],
            "excel_path": _state["excel_path"],
            "timestamp": _state["timestamp"],
        })


@app.route("/api/download")
def api_download():
    with _lock:
        path = _state.get("excel_path")

    if not path or not Path(path).exists():
        return "No report available", 404

    return send_file(
        path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=Path(path).name,
    )


@app.route("/api/screenshot/<path:filepath>")
def api_screenshot(filepath):
    p = Path(filepath)
    if not p.exists():
        return "Screenshot not found", 404
    return send_file(str(p), mimetype="image/png")


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LP Radar Web UI")
    parser.add_argument("--host", default="0.0.0.0", help="Host (기본: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="포트 (기본: 5000)")
    parser.add_argument("--debug", action="store_true", help="디버그 모드")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    print(f"LP Radar Web UI: http://localhost:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()

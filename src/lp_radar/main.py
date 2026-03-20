"""CLI entry point for LP Radar."""
from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import sys
from pathlib import Path

from lp_radar.config import OUTPUT_DIR
from lp_radar.registry import get_all_scrapers, get_scrapers_by_names
from lp_radar.report import generate_excel
from lp_radar.runner import run_all

# Ensure scrapers are registered by importing the package
import lp_radar.scrapers  # noqa: F401


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LP Radar - 기관전용 사모펀드 출자 공고 모니터링"
    )
    parser.add_argument(
        "--days", type=int, default=10,
        help="조회 기간 (일, 기본: 10)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="출력 파일 경로 (기본: lp_radar_YYYYMMDD.xlsx)",
    )
    parser.add_argument(
        "--sites", nargs="*", default=None,
        help="특정 사이트만 실행 (약칭, 예: KVCA KOFIA)",
    )
    parser.add_argument(
        "--concurrency", type=int, default=4,
        help="동시 실행 탭 수 (기본: 4)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="상세 로그 출력",
    )
    args = parser.parse_args()

    # Logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # Date range
    today = datetime.date.today()
    cutoff_date = today - datetime.timedelta(days=args.days)

    # Scrapers
    if args.sites:
        scrapers = get_scrapers_by_names(args.sites)
        if not scrapers:
            print("지정된 사이트를 찾을 수 없습니다.")
            sys.exit(1)
    else:
        scrapers = get_all_scrapers()

    print(f"LP Radar - {len(scrapers)}개 사이트 스캔 시작")
    print(f"조회 기간: {cutoff_date} ~ {today} ({args.days}일)")
    print("-" * 60)

    # Run
    announcements, errors = asyncio.run(
        run_all(scrapers, cutoff_date, concurrency=args.concurrency)
    )

    # Console summary
    fund_count = sum(1 for a in announcements if a.is_fund_related)
    print("-" * 60)
    print(f"총 {len(announcements)}건 수집 (펀드관련: {fund_count}건)")

    if announcements:
        print()
        current_source = None
        for ann in announcements:
            if ann.source != current_source:
                current_source = ann.source
                print(f"\n[{ann.source} ({ann.source_short})]")
            marker = " ★" if ann.is_fund_related else ""
            date_str = ann.date.strftime("%m/%d") if ann.date else "??/??"
            print(f"  {date_str} {ann.title}{marker}")

    if errors:
        print(f"\n⚠ {len(errors)}개 사이트 스크래핑 실패:")
        for err in errors:
            print(f"  - {err.source} ({err.source_short}): {err.error_message}")
            if err.screenshot_path:
                print(f"    스크린샷: {err.screenshot_path}")

    # Excel output
    output_path = Path(args.output) if args.output else (
        OUTPUT_DIR / f"lp_radar_{today.strftime('%Y%m%d')}.xlsx"
    )
    generate_excel(announcements, errors, output_path)
    print(f"\n리포트 저장: {output_path}")


if __name__ == "__main__":
    main()

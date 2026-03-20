"""Fund-related keyword filtering."""
from __future__ import annotations

FUND_KEYWORDS: list[str] = [
    # 출자/위탁 관련
    "출자", "위탁운용", "운용사", "수탁",
    # GP 선정
    "GP 선정", "GP선정", "지피선정",
    # 펀드 유형
    "사모펀드", "사모 펀드", "블라인드펀드", "블라인드 펀드",
    "프로젝트펀드", "프로젝트 펀드",
    "벤처펀드", "벤처 펀드", "모태펀드", "모태 펀드",
    "성장펀드", "성장 펀드", "세컨더리", "Secondary",
    # 투자 유형
    "대체투자", "부동산투자", "인프라투자", "SOC",
    "PEF", "VC", "벤처캐피탈",
    # 자산운용
    "자산운용", "자산배분", "투자풀", "자금운용",
    "기금운용", "위탁", "투자일임",
    # 공고 유형
    "컨테스트", "선발", "선정 공고", "모집 공고",
    "출자사업", "출자 사업",
    # 기타
    "Pre-IPO", "IPO", "메자닌", "Mezzanine",
]


def is_fund_related(title: str) -> bool:
    """Check if the title contains any fund-related keywords."""
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in FUND_KEYWORDS)

#!/usr/bin/env bash
# ============================================================
#  LP Radar - 원클릭 설치 및 실행 (Linux / macOS)
# ============================================================
set -e

# ─── 색상 ──────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# ─── 설정 ──────────────────────────────────────────
REPO_URL="https://github.com/wankyu4356/LP_Ladar.git"
BRANCH="claude/fund-announcement-scraper-48f1r"
INSTALL_DIR="$HOME/LP_Ladar"
PORT=5000

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║       LP Radar - 원클릭 설치 및 실행        ║${NC}"
echo -e "${BOLD}║   기관전용 사모펀드 출자 공고 모니터링      ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ─── 1. Python 확인 ───────────────────────────────
echo -e "${BLUE}[1/6]${NC} Python 환경 확인..."

PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PY_VER=$("$cmd" --version 2>&1 | awk '{print $2}')
        PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}  [오류] Python 3.10+ 가 설치되어 있지 않습니다.${NC}"
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  설치 방법: brew install python@3.12"
    else
        echo "  설치 방법: sudo apt install python3 python3-venv python3-pip"
    fi
    exit 1
fi
echo -e "  ${GREEN}Python $PY_VER 확인됨${NC} ($PYTHON_CMD)"

# ─── 2. Git 확인 ──────────────────────────────────
echo -e "${BLUE}[2/6]${NC} Git 환경 확인..."

if ! command -v git &>/dev/null; then
    echo -e "${RED}  [오류] Git이 설치되어 있지 않습니다.${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  설치 방법: xcode-select --install"
    else
        echo "  설치 방법: sudo apt install git"
    fi
    exit 1
fi
echo -e "  ${GREEN}$(git --version) 확인됨${NC}"

# ─── 3. 레포 클론/업데이트 ─────────────────────────
echo -e "${BLUE}[3/6]${NC} 프로젝트 다운로드..."

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "  기존 프로젝트 발견 - 최신 버전으로 업데이트..."
    cd "$INSTALL_DIR"
    git fetch origin "$BRANCH" 2>/dev/null || true
    git checkout "$BRANCH" 2>/dev/null || true
    git pull origin "$BRANCH" 2>/dev/null || true
else
    if [ -d "$INSTALL_DIR" ]; then
        echo "  기존 폴더 제거 중..."
        rm -rf "$INSTALL_DIR"
    fi
    echo "  클론 중: $REPO_URL"
    git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
echo -e "  ${GREEN}프로젝트 준비 완료: $INSTALL_DIR${NC}"

# ─── 4. 가상환경 생성 ─────────────────────────────
echo -e "${BLUE}[4/6]${NC} Python 가상환경 설정..."

if [ ! -f "venv/bin/activate" ]; then
    echo "  가상환경 생성 중..."
    "$PYTHON_CMD" -m venv venv
fi

source venv/bin/activate
echo -e "  ${GREEN}가상환경 활성화됨${NC}"

# ─── 5. 의존성 설치 ───────────────────────────────
echo -e "${BLUE}[5/6]${NC} 패키지 설치 중 (첫 실행 시 2~3분 소요)..."

pip install --upgrade pip -q 2>/dev/null
pip install -e . -q 2>/dev/null || pip install -e .

echo "  Chromium 브라우저 설치 확인 중..."
python -m playwright install chromium 2>/dev/null || {
    echo "  Playwright 시스템 의존성 설치 중 (sudo 필요할 수 있음)..."
    if [[ "$OSTYPE" == "linux"* ]]; then
        python -m playwright install --with-deps chromium 2>/dev/null || python -m playwright install chromium
    else
        python -m playwright install chromium
    fi
}

echo -e "  ${GREEN}패키지 설치 완료${NC}"

# ─── 6. 웹 서버 실행 ──────────────────────────────
echo -e "${BLUE}[6/6]${NC} LP Radar 웹 서버 시작..."
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║                                              ║${NC}"
echo -e "${BOLD}║   ${GREEN}LP Radar 실행 중!${NC}${BOLD}                          ║${NC}"
echo -e "${BOLD}║                                              ║${NC}"
echo -e "${BOLD}║   브라우저에서 아래 주소로 접속하세요:       ║${NC}"
echo -e "${BOLD}║   ${YELLOW}http://localhost:${PORT}${NC}${BOLD}                     ║${NC}"
echo -e "${BOLD}║                                              ║${NC}"
echo -e "${BOLD}║   종료: Ctrl+C                               ║${NC}"
echo -e "${BOLD}║                                              ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""

# 브라우저 자동 열기
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://localhost:$PORT" 2>/dev/null &
elif command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:$PORT" 2>/dev/null &
fi

# 서버 실행
python -m lp_radar.web --port "$PORT"

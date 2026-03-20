@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

:: ============================================================
::  LP Radar - 원클릭 설치 및 실행
:: ============================================================

title LP Radar - Setup ^& Run

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║       LP Radar - 원클릭 설치 및 실행        ║
echo  ║   기관전용 사모펀드 출자 공고 모니터링      ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: ─── 설정 ─────────────────────────────────────────
set "REPO_URL=https://github.com/wankyu4356/LP_Ladar.git"
set "BRANCH=claude/fund-announcement-scraper-48f1r"
set "INSTALL_DIR=%USERPROFILE%\LP_Ladar"
set "PORT=5000"

:: ─── 1. Python 확인 ──────────────────────────────
echo [1/6] Python 환경 확인...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [오류] Python이 설치되어 있지 않습니다.
    echo  https://www.python.org/downloads/ 에서 Python 3.10+ 설치 후 다시 실행하세요.
    echo  설치 시 "Add Python to PATH" 체크를 반드시 해주세요.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo  Python %PY_VER% 확인됨

:: Python 버전 체크 (3.10+)
for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)
if %PY_MAJOR% LSS 3 (
    echo  [오류] Python 3.10 이상이 필요합니다. 현재: %PY_VER%
    pause
    exit /b 1
)
if %PY_MAJOR%==3 if %PY_MINOR% LSS 10 (
    echo  [오류] Python 3.10 이상이 필요합니다. 현재: %PY_VER%
    pause
    exit /b 1
)

:: ─── 2. Git 확인 ─────────────────────────────────
echo [2/6] Git 환경 확인...
git --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [오류] Git이 설치되어 있지 않습니다.
    echo  https://git-scm.com/download/win 에서 설치 후 다시 실행하세요.
    echo.
    pause
    exit /b 1
)

for /f "tokens=3 delims= " %%v in ('git --version 2^>^&1') do echo  Git %%v 확인됨

:: ─── 3. 레포 클론/업데이트 ────────────────────────
echo [3/6] 프로젝트 다운로드...
if exist "%INSTALL_DIR%\.git" (
    echo  기존 프로젝트 발견 - 최신 버전으로 업데이트합니다...
    pushd "%INSTALL_DIR%"
    git fetch origin %BRANCH% >nul 2>&1
    git checkout %BRANCH% >nul 2>&1
    git pull origin %BRANCH% >nul 2>&1
    popd
) else (
    if exist "%INSTALL_DIR%" (
        echo  기존 폴더 제거 중...
        rmdir /s /q "%INSTALL_DIR%" >nul 2>&1
    )
    echo  클론 중: %REPO_URL%
    git clone -b %BRANCH% %REPO_URL% "%INSTALL_DIR%"
    if errorlevel 1 (
        echo  [오류] 레포 클론 실패. 네트워크 연결을 확인하세요.
        pause
        exit /b 1
    )
)
echo  프로젝트 준비 완료: %INSTALL_DIR%

:: ─── 4. 가상환경 생성 ────────────────────────────
echo [4/6] Python 가상환경 설정...
pushd "%INSTALL_DIR%"

if not exist "venv\Scripts\activate.bat" (
    echo  가상환경 생성 중...
    python -m venv venv
    if errorlevel 1 (
        echo  [오류] 가상환경 생성 실패.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
echo  가상환경 활성화됨

:: ─── 5. 의존성 설치 ──────────────────────────────
echo [5/6] 패키지 설치 중 (첫 실행 시 2~3분 소요)...
pip install --upgrade pip >nul 2>&1
pip install -e . >nul 2>&1
if errorlevel 1 (
    echo  pip install 재시도...
    pip install -e . 2>&1
)

:: Playwright 브라우저 설치
echo  Chromium 브라우저 설치 확인 중...
python -m playwright install chromium >nul 2>&1
if errorlevel 1 (
    echo  Playwright 브라우저 설치 중 (첫 실행 시 1~2분 소요)...
    python -m playwright install chromium 2>&1
)
echo  패키지 설치 완료

:: ─── 6. 웹 서버 실행 ─────────────────────────────
echo [6/6] LP Radar 웹 서버 시작...
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║                                              ║
echo  ║   LP Radar 실행 중!                          ║
echo  ║                                              ║
echo  ║   브라우저에서 아래 주소로 접속하세요:       ║
echo  ║   http://localhost:%PORT%                     ║
echo  ║                                              ║
echo  ║   종료: Ctrl+C 또는 이 창을 닫으세요        ║
echo  ║                                              ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: 브라우저 자동 열기
start http://localhost:%PORT%

:: 서버 실행
python -m lp_radar.web --port %PORT%

:: 종료 시
echo.
echo  LP Radar가 종료되었습니다.
pause

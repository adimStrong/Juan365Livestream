@echo off
echo ============================================================
echo           JUAN365 DASHBOARD - FIRST TIME SETUP
echo ============================================================
echo.

cd /d "%~dp0"

REM Check if config.py exists
if exist config.py (
    echo [OK] config.py already exists
) else (
    echo [!] config.py not found - creating from template...
    copy config.template.py config.py
    echo.
    echo ============================================================
    echo IMPORTANT: You need to edit config.py with your credentials!
    echo ============================================================
    echo.
    echo 1. Open config.py in a text editor
    echo 2. Replace PAGE_ID with your Facebook Page ID
    echo 3. Replace PAGE_TOKEN with your Page Access Token
    echo.
    echo Get your token from: https://developers.facebook.com/tools/explorer/
    echo.
    notepad config.py
    pause
    exit /b
)

REM Create data directory
if not exist data mkdir data
echo [OK] data/ directory ready

REM Create exports directory
if not exist exports mkdir exports
if not exist exports\backups mkdir exports\backups
echo [OK] exports/ directory ready

echo.
echo ============================================================
echo SETUP COMPLETE!
echo ============================================================
echo.
echo Next steps:
echo   1. Run REFRESH_DATA.bat to fetch API data
echo   2. Run UPDATE_CSV.bat to import your CSV exports
echo   3. Run START_STREAMLIT.bat to launch the dashboard
echo.
pause

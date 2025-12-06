@echo off
REM ============================================
REM Juan365 Livestream Auto-Update Script
REM ============================================
REM This script runs the full auto-update workflow:
REM 1. Fetch API data
REM 2. Download CSV from Meta Business Suite
REM 3. Merge CSV files
REM 4. Commit and push to GitHub
REM 5. Streamlit Cloud auto-deploys
REM ============================================

echo.
echo ============================================
echo  Juan365 Livestream Auto-Update
echo ============================================
echo.

cd /d C:\Users\us\Desktop\juan365_livestream_project

REM Run the auto-update script
python auto_update.py

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Update completed successfully!
) else (
    echo.
    echo Update completed with some errors. Check logs\auto_update.log
)

echo.
echo ============================================
echo Done!
echo ============================================

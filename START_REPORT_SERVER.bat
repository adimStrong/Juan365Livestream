@echo off
echo ============================================================
echo           JUAN365 REPORT LOCAL SERVER
echo ============================================================
echo.
echo Starting server at http://localhost:8080
echo.
cd /d "%~dp0\reports"
python serve_report.py
pause

@echo off
echo ============================================================
echo           JUAN365 REPORT UPDATE
echo ============================================================
echo.
echo This will regenerate the report using the latest CSV
echo from the exports/ folder.
echo.
echo Make sure you have placed your Meta Business Suite CSV export
echo in the exports/ folder.
echo.
pause

cd /d "%~dp0\reports"
echo.
echo [INFO] Generating report...
echo ============================================================
python generate_report.py

echo.
echo ============================================================
echo           DONE!
echo ============================================================
echo.
echo To view the report, run START_REPORT_SERVER.bat
echo Or open: reports\output\Juan365_Report_LATEST.html
echo.
pause

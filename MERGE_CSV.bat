@echo off
echo ============================================================
echo           JUAN365 CSV MERGE TOOL
echo ============================================================
echo.
cd /d "%~dp0"

echo This will merge all CSV files in the exports/ folder
echo into a single Juan365_MERGED_ALL.csv file.
echo.
echo Current CSV files in exports/:
dir exports\*.csv /b 2>nul
echo.

python merge_exports.py

echo.
echo ============================================================
echo MERGE COMPLETE!
echo ============================================================
echo.
echo Next steps:
echo   1. Run REFRESH_DATA.bat to update API data
echo   2. Refresh browser: http://localhost:8501
echo   3. (Optional) git push to update Streamlit Cloud
echo.
pause

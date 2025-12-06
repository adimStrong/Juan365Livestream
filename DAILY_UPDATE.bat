@echo off
REM ============================================
REM Juan365 DAILY UPDATE - Complete Workflow
REM ============================================
REM 1. Opens Meta Business Suite for CSV download
REM 2. Waits for you to download
REM 3. Merges CSVs from Downloads folder
REM 4. Fetches API data
REM 5. Pushes to GitHub
REM ============================================

echo.
echo ============================================
echo  JUAN365 DAILY UPDATE
echo ============================================
echo.

cd /d C:\Users\us\Desktop\juan365_livestream_project

echo STEP 1: Opening Meta Business Suite...
echo        Please download the CSV export.
echo.
python open_meta_export.py

echo.
echo ============================================
echo Press any key AFTER you have downloaded the CSV...
echo ============================================
pause

echo.
echo STEP 2: Merging CSV files from Downloads...
python merge_exports.py

echo.
echo STEP 3: Fetching API data...
python api_fetcher.py
python refresh_api_cache.py

echo.
echo STEP 4: Pushing to GitHub...
git add api_cache/ exports/
git commit -m "Daily update: %date%"
git push origin main

echo.
echo ============================================
echo  DONE! Streamlit Cloud will auto-deploy.
echo ============================================
echo.
pause

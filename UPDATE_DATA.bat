@echo off
echo ============================================================
echo           JUAN365 DATA UPDATE
echo ============================================================
echo.
echo Step 1: Merging all CSV exports...
echo.
cd /d "%~dp0"
python merge_exports.py
echo.
echo Step 2: Clearing cache...
rmdir /s /q __pycache__ 2>nul
rmdir /s /q .streamlit 2>nul
echo Cache cleared!
echo.
echo ============================================================
echo DATA UPDATE COMPLETE!
echo ============================================================
echo.
echo Refresh your browser at http://localhost:8501
echo Or run START_STREAMLIT.bat to start the dashboard
echo.
pause

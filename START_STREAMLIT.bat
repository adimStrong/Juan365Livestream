@echo off
echo ============================================================
echo           JUAN365 STREAMLIT DASHBOARD
echo ============================================================
echo.
echo Starting Streamlit at http://localhost:8501
echo.
cd /d "%~dp0"
streamlit run streamlit_app.py
pause

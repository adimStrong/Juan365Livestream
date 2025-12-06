@echo off
REM ============================================
REM First-Time Browser Session Setup
REM ============================================
REM This script opens a browser for you to log in
REM to Facebook/Meta Business Suite manually.
REM Your login session will be saved for automation.
REM ============================================
REM Run this ONCE before using AUTO_UPDATE.bat
REM ============================================

echo.
echo ============================================
echo  Juan365 Livestream - Browser Setup
echo ============================================
echo.
echo This will open a browser window.
echo.
echo INSTRUCTIONS:
echo   1. Log in to your Facebook account
echo   2. Navigate to Meta Business Suite
echo   3. Make sure you can see the Insights page
echo   4. CLOSE THE BROWSER when done
echo.
echo Your login session will be saved for automation.
echo.
echo Press any key to open the browser...
pause > nul

cd /d C:\Users\us\Desktop\juan365_livestream_project

echo.
echo Opening browser...
echo (Close the browser when you're done logging in)
echo.

python auto_download_csv.py --setup

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo SUCCESS! Browser session saved.
    echo ============================================
    echo.
    echo You can now use AUTO_UPDATE.bat for automated updates.
    echo.
    echo To test the CSV download:
    echo   python auto_download_csv.py --test
    echo.
) else (
    echo.
    echo ============================================
    echo Setup may have encountered issues.
    echo ============================================
    echo.
    echo If you closed the browser after logging in,
    echo the session should still be saved.
    echo.
    echo Try running AUTO_UPDATE.bat to test.
    echo.
)

pause

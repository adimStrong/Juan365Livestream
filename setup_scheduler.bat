@echo off
REM ============================================
REM Setup Windows Task Scheduler for Auto-Update
REM ============================================
REM This script creates a scheduled task that runs
REM the auto-update every 6 hours (12AM, 6AM, 12PM, 6PM)
REM ============================================
REM Run this script as Administrator!
REM ============================================

echo.
echo ============================================
echo  Setup Scheduled Task for Auto-Update
echo ============================================
echo.
echo This will create a Windows scheduled task that
echo runs the auto-update every 6 hours.
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ERROR: This script requires Administrator privileges.
    echo Please right-click and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Delete existing task if it exists
schtasks /delete /tn "Juan365 Livestream Auto Update" /f 2>nul

REM Create the scheduled task
REM Runs at 12:00 AM, 6:00 AM, 12:00 PM, 6:00 PM daily

echo.
echo Creating scheduled task...

schtasks /create ^
    /tn "Juan365 Livestream Auto Update" ^
    /tr "C:\Users\us\Desktop\juan365_livestream_project\AUTO_UPDATE.bat" ^
    /sc HOURLY ^
    /mo 6 ^
    /st 00:00 ^
    /ru "%USERNAME%" ^
    /rl HIGHEST ^
    /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo SUCCESS! Scheduled task created.
    echo ============================================
    echo.
    echo Task Name: Juan365 Livestream Auto Update
    echo Schedule: Every 6 hours (12AM, 6AM, 12PM, 6PM)
    echo Action: Run AUTO_UPDATE.bat
    echo.
    echo To view/modify the task:
    echo   1. Open Task Scheduler (taskschd.msc)
    echo   2. Look for "Juan365 Livestream Auto Update"
    echo.
    echo To run immediately:
    echo   schtasks /run /tn "Juan365 Livestream Auto Update"
    echo.
    echo To delete the task:
    echo   schtasks /delete /tn "Juan365 Livestream Auto Update" /f
    echo.
) else (
    echo.
    echo ============================================
    echo FAILED to create scheduled task.
    echo ============================================
    echo.
    echo Try running this script as Administrator.
    echo.
)

pause

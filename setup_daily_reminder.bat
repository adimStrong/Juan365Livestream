@echo off
REM Creates a daily Windows Task Scheduler task to remind you to download CSV
REM Runs at 9:00 AM every day

echo Creating scheduled task: Juan365 CSV Download Reminder
echo.

schtasks /create /tn "Juan365 CSV Download Reminder" /tr "C:\Users\us\Desktop\juan365_livestream_project\OPEN_META_EXPORT.bat" /sc daily /st 09:00 /f

echo.
echo Task created! It will run daily at 9:00 AM.
echo.
echo To change the time, run:
echo   schtasks /change /tn "Juan365 CSV Download Reminder" /st HH:MM
echo.
echo To delete the task:
echo   schtasks /delete /tn "Juan365 CSV Download Reminder" /f
echo.
pause

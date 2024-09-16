@echo off

:: Run both scripts simultaneously
start python syncDbAndSheet.py
start python flask_app/app.py

:: Wait for both scripts to finish
echo Waiting for scripts to finish...

:: Pause the command window to see the output
pause

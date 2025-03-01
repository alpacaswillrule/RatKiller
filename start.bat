@echo off
REM Start script for Rat Reporter application on Windows

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python to run this application.
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pip is not installed or not in PATH. Please install pip to run this application.
    pause
    exit /b 1
)

REM Create necessary directories if they don't exist
if not exist backend\data\photos mkdir backend\data\photos

REM Install required packages
echo Installing required packages...
pip install -r backend\requirements.txt

REM Start the application
echo Starting Rat Reporter application...
python run.py

pause

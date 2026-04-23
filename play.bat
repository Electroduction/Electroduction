@echo off
REM ECHOFRONTIER Launcher for Windows

echo ============================================
echo   ECHOFRONTIER - Enhanced Edition
echo ============================================
echo.
echo Checking dependencies...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo X Python not found! Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo - Python found

REM Check if dependencies are installed
python -c "import pygame; import numpy" >nul 2>&1
if errorlevel 1 (
    echo X Dependencies not installed!
    echo Installing requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo X Failed to install dependencies
        pause
        exit /b 1
    )
)

echo - All dependencies installed
echo.
echo Starting ECHOFRONTIER...
echo =========================================
echo.

REM Run the AAA integrated game
cd game
python main_aaa.py

echo.
echo Thanks for playing!
pause

@echo off
REM ECHOFRONTIER Launcher for Windows

echo =========================================
echo     ECHOFRONTIER - Sci-Fantasy RPG
echo =========================================
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

REM Check if pygame is installed
python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo X Pygame not installed!
    echo Installing pygame...
    pip install pygame
    if errorlevel 1 (
        echo X Failed to install pygame. Please run: pip install pygame
        pause
        exit /b 1
    )
)

echo - Pygame installed
echo.
echo Starting ECHOFRONTIER...
echo =========================================
echo.

REM Run the game
cd game
python main.py

echo.
echo Thanks for playing!
pause

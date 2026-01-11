#!/bin/bash

# ECHOFRONTIER Launcher
# Simple launcher script for the game

echo "========================================="
echo "    ECHOFRONTIER - Sci-Fantasy RPG      "
echo "========================================="
echo ""
echo "Checking dependencies..."

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null
then
    echo "❌ Python not found! Please install Python 3.8 or higher."
    exit 1
fi

# Try to use python3, fall back to python
if command -v python3 &> /dev/null
then
    PYTHON=python3
else
    PYTHON=python
fi

echo "✓ Python found: $($PYTHON --version)"

# Check if pygame is installed
$PYTHON -c "import pygame" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Pygame not installed!"
    echo "Installing pygame..."
    pip install pygame
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install pygame. Please run: pip install pygame"
        exit 1
    fi
fi

echo "✓ Pygame installed"
echo ""
echo "Starting ECHOFRONTIER..."
echo "========================================="
echo ""

# Run the game
cd game && $PYTHON main.py

echo ""
echo "Thanks for playing!"

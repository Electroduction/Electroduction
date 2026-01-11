#!/bin/bash

# ECHOFRONTIER Launcher
# Simple launcher script for the game

echo "============================================"
echo "  ECHOFRONTIER - Enhanced Edition  "
echo "============================================"
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
    echo "Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Check if numpy is installed
$PYTHON -c "import numpy" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Numpy not installed!"
    echo "Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

echo "✓ All dependencies installed"
echo ""
echo "Starting ECHOFRONTIER..."
echo "========================================="
echo ""

# Run the AAA integrated game
cd game && $PYTHON main_aaa.py

echo ""
echo "Thanks for playing!"

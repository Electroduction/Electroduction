#!/bin/bash

# Desktop Application Build Script
# Creates executable using PyInstaller

set -e

echo "🔨 Building Electroduction Desktop Application..."

# Install PyInstaller if not present
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    pip3 install pyinstaller --quiet
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist *.spec

# Build executable
echo "Building executable..."
pyinstaller --name="Electroduction Portfolio" \
    --onefile \
    --windowed \
    --icon=NONE \
    --add-data "requirements.txt:." \
    main.py

echo ""
echo "========================================="
echo "✅ Build Complete!"
echo "========================================="
echo ""
echo "Executable location: dist/Electroduction Portfolio"
echo ""
echo "To run the application:"
echo "  ./dist/Electroduction\\ Portfolio"
echo ""

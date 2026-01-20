#!/bin/bash

echo "🎓 Starting AI CertPro Platform..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt --quiet

# Create necessary directories
mkdir -p database
mkdir -p static/css
mkdir -p static/js
mkdir -p templates

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from database.db_manager import DatabaseManager; db = DatabaseManager(); db.initialize()"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting Flask server..."
echo "   Access the platform at: http://localhost:5000"
echo "   API documentation: http://localhost:5000/api"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
cd backend && python3 app.py

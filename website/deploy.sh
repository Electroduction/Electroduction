#!/bin/bash

# Electroduction Website Deployment Script
# This script automates the deployment process

set -e  # Exit on error

echo "🚀 Starting Electroduction Website Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

print_message "Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_message "Docker Compose is installed"

# Stop existing containers
print_message "Stopping existing containers..."
docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true

# Build and start containers
print_message "Building and starting containers..."
if docker-compose version &> /dev/null; then
    docker-compose up -d --build
else
    docker compose up -d --build
fi

# Wait for services to be ready
print_message "Waiting for services to start..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/api/health > /dev/null; then
    print_message "Backend is running on http://localhost:8000"
else
    print_warning "Backend health check failed. It may still be starting..."
fi

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null; then
    print_message "Frontend is running on http://localhost:3000"
else
    print_warning "Frontend may still be starting..."
fi

echo ""
echo "========================================="
echo "🎉 Deployment Complete!"
echo "========================================="
echo ""
echo "📝 Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📊 View logs:"
echo "   All services: docker-compose logs -f"
echo "   Frontend: docker-compose logs -f frontend"
echo "   Backend: docker-compose logs -f backend"
echo ""
echo "🛑 To stop the application:"
echo "   docker-compose down"
echo ""

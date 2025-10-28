#!/bin/bash

# Real-Time Task Queue - Docker Startup Script

echo "Starting Real-Time Task Queue..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

echo "Docker and Docker Compose found"
echo ""

# Stop any existing containers
echo "Cleaning up existing containers..."
docker-compose down

echo ""
echo "Building and starting services..."
docker-compose up --build

# Note: Press Ctrl+C to stop all services

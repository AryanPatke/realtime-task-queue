#!/bin/bash

# Real-Time Task Queue - Local Development Script (without Docker)

echo "Starting Real-Time Task Queue (Local Mode)..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.11+ and try again."
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    echo "Error: Redis is not running. Please start Redis with 'redis-server' and try again."
    exit 1
fi

echo "Python and Redis are available"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "Starting FastAPI application..."
python main.py &
API_PID=$!

sleep 3

echo "Starting workers..."
python worker.py &
WORKER_PID=$!

echo ""
echo "All services started"
echo "Dashboard: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $API_PID $WORKER_PID 2>/dev/null; echo '\nShutting down...'; exit 0" INT
wait

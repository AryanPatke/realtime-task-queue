# Setup Guide

## Prerequisites

- Python 3.11 or higher
- Redis 7 or higher
- Docker and Docker Compose (optional, for containerized deployment)

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Start all services
docker-compose up --build

# Access dashboard
open http://localhost:8000
```

### Option 2: Local Development

```bash
# Start Redis
redis-server

# Install dependencies
pip install -r requirements.txt

# Terminal 1: Start API
python main.py

# Terminal 2: Start workers
python worker.py
```

## Configuration

Create a `.env` file (optional):

```env
REDIS_HOST=localhost
REDIS_PORT=6379
APP_PORT=8000
WORKERS=4
MAX_RETRIES=3
```

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Create a task
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "task_type": "email", "priority": 5, "payload": {}}'
```

## Endpoints

- Dashboard: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Troubleshooting

**Port already in use:**
```bash
# Check what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

**Redis connection error:**
```bash
# Check Redis is running
redis-cli ping  # Should return PONG
```

**Docker issues:**
```bash
# Clean up and restart
docker-compose down
docker-compose up --build
```


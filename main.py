from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from pathlib import Path

from app.api import tasks, websocket
from app.core.redis_client import redis_client
from app.core.task_queue import task_queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await redis_client.connect()
    await task_queue.initialize()
    print("Application started successfully")
    print("Dashboard available at http://localhost:8000")
    
    yield
    
    # Shutdown
    await redis_client.disconnect()
    print("Application shutdown complete")


app = FastAPI(
    title="Real-Time Task Queue",
    description="A scalable task queue system with WebSocket monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(tasks.router)
app.include_router(websocket.router)

# Mount static files
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the dashboard HTML"""
    html_file = Path(__file__).parent / "templates" / "index.html"
    
    if html_file.exists():
        return html_file.read_text()
    else:
        return """
        <html>
            <head><title>Task Queue Dashboard</title></head>
            <body>
                <h1>Real-Time Task Queue Dashboard</h1>
                <p>Dashboard template not found. Please ensure templates/index.html exists.</p>
                <p>API Documentation: <a href="/docs">/docs</a></p>
            </body>
        </html>
        """


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "task-queue"
    }


if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )


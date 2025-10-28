"""
Worker process to handle task execution
Run this separately from the main FastAPI app
"""
import asyncio
from app.workers.task_worker import run_worker
from app.core.config import settings


async def main():
    """Run multiple workers"""
    print(f"Starting {settings.workers} workers...")
    
    workers = [
        asyncio.create_task(run_worker(i))
        for i in range(settings.workers)
    ]
    
    try:
        await asyncio.gather(*workers)
    except KeyboardInterrupt:
        print("\nShutting down workers...")
        for worker in workers:
            worker.cancel()


if __name__ == "__main__":
    asyncio.run(main())


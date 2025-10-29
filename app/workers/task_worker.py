import asyncio
import random
from datetime import datetime
from app.core.task_queue import task_queue
from app.core.redis_client import redis_client
from app.core.config import settings
from app.models.task import TaskStatus, TaskType
from app.api.websocket import broadcast_task_update


class TaskWorker:
    """Worker to process tasks from the queue"""
    
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.running = False
    
    async def start(self):
        """Start the worker"""
        print(f"Worker {self.worker_id} starting...")
        self.running = True
        
        # Initialize Redis and task queue
        await redis_client.connect()
        await task_queue.initialize()
        
        while self.running:
            try:
                # Get next task from queue
                task_id = await task_queue.get_next_task()
                
                if task_id:
                    await self.process_task(task_id)
                else:
                    # No tasks available, wait before checking again
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"Worker {self.worker_id} error: {str(e)}")
                await asyncio.sleep(5)
    
    async def process_task(self, task_id: str):
        """Process a single task"""
        try:
            # Update task status to processing
            task = await task_queue.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                started_at=datetime.utcnow()
            )
            
            if not task:
                print(f"Task {task_id} not found")
                return
            
            print(f"Worker {self.worker_id} processing task {task_id} ({task.task_type})")
            
            # Broadcast initial processing status
            await broadcast_task_update(task_id)
            
            # Simulate task processing based on task type
            await self.execute_task(task_id, task.task_type, task.payload)
            
            # Mark task as completed
            await task_queue.mark_task_completed(task_id)
            print(f"Worker {self.worker_id} completed task {task_id}")
            
            # Broadcast completion
            await broadcast_task_update(task_id)
            
        except Exception as e:
            error_msg = str(e)
            print(f"Worker {self.worker_id} failed task {task_id}: {error_msg}")
            
            # Check if we should retry
            task = await task_queue.get_task(task_id)
            if task and task.retry_count < settings.max_retries:
                # Requeue for retry
                await task_queue.requeue_task(task_id, task.priority)
                print(f"Task {task_id} requeued for retry (attempt {task.retry_count + 1})")
                await broadcast_task_update(task_id)
            else:
                # Mark as failed
                await task_queue.mark_task_failed(task_id, error_msg)
                await broadcast_task_update(task_id)
    
    async def execute_task(self, task_id: str, task_type: TaskType, payload: dict):
        """Execute the actual task logic"""
        
        # Simulate different task types with progress updates
        steps = 10
        
        for i in range(steps):
            # Simulating work here, we can add a real task execution here
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Update progress
            progress = int((i + 1) / steps * 100)
            await task_queue.update_task(task_id, progress=progress)
            
            # Broadcast progress update every few steps
            if i % 3 == 0 or i == steps - 1:
                await broadcast_task_update(task_id)
            
            # Simulate occasional failures for testing
            if random.random() < 0.05:  # 5% chance of failure
                raise Exception("Simulated task failure for testing")
        
        # Task type specific logic could go here
        if task_type == TaskType.EMAIL:
            print(f"Sending email to: {payload.get('recipient', 'unknown')}")
        elif task_type == TaskType.DATA_PROCESSING:
            print(f"Processing data: {payload.get('data_size', 0)} records")
        elif task_type == TaskType.FILE_CONVERSION:
            print(f"Converting file: {payload.get('filename', 'unknown')}")
        elif task_type == TaskType.API_CALL:
            print(f"Calling API: {payload.get('endpoint', 'unknown')}")
        elif task_type == TaskType.REPORT_GENERATION:
            print(f"Generating report: {payload.get('report_type', 'unknown')}")
    
    async def stop(self):
        """Stop the worker"""
        print(f"Worker {self.worker_id} stopping...")
        self.running = False
        await redis_client.disconnect()


async def run_worker(worker_id: int):
    """Run a worker instance"""
    worker = TaskWorker(worker_id)
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()
    except Exception as e:
        print(f"Worker {worker_id} crashed: {str(e)}")
        await worker.stop()


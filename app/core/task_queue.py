import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.core.redis_client import redis_client
from app.models.task import TaskStatus, TaskResponse, TaskCreate


class TaskQueue:
    """Task queue manager using Redis"""
    
    TASK_PREFIX = "task:"
    QUEUE_KEY = "task_queue"
    PROCESSING_SET = "processing_tasks"
    
    def __init__(self):
        self.redis = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = redis_client.get_client()
    
    async def create_task(self, task_data: TaskCreate) -> TaskResponse:
        """Create a new task and add to queue"""
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        task = {
            "task_id": task_id,
            "name": task_data.name,
            "task_type": task_data.task_type,
            "status": TaskStatus.PENDING,
            "payload": task_data.payload,
            "priority": task_data.priority,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None,
            "retry_count": 0,
            "progress": 0
        }
        
        # Store task in Redis
        await self.redis.set(
            f"{self.TASK_PREFIX}{task_id}",
            json.dumps(task)
        )
        
        # Add to priority queue (using sorted set with priority as score)
        await self.redis.zadd(
            self.QUEUE_KEY,
            {task_id: task_data.priority}
        )
        
        return TaskResponse(**task)
    
    async def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """Get task by ID"""
        task_data = await self.redis.get(f"{self.TASK_PREFIX}{task_id}")
        if not task_data:
            return None
        
        task_dict = json.loads(task_data)
        return TaskResponse(**task_dict)
    
    async def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        error: Optional[str] = None,
        progress: Optional[int] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ) -> Optional[TaskResponse]:
        """Update task status and details"""
        task_data = await self.redis.get(f"{self.TASK_PREFIX}{task_id}")
        if not task_data:
            return None
        
        task_dict = json.loads(task_data)
        
        if status:
            task_dict["status"] = status
        if error is not None:
            task_dict["error"] = error
        if progress is not None:
            task_dict["progress"] = progress
        if started_at:
            task_dict["started_at"] = started_at.isoformat()
        if completed_at:
            task_dict["completed_at"] = completed_at.isoformat()
        
        task_dict["updated_at"] = datetime.utcnow().isoformat()
        
        await self.redis.set(
            f"{self.TASK_PREFIX}{task_id}",
            json.dumps(task_dict)
        )
        
        return TaskResponse(**task_dict)
    
    async def get_next_task(self) -> Optional[str]:
        """Get next task from queue (highest priority)"""
        # Get task with highest priority (using ZPOPMAX for atomic operation)
        result = await self.redis.zpopmax(self.QUEUE_KEY, 1)
        
        if not result:
            return None
        
        task_id = result[0][0]
        
        # Add to processing set
        await self.redis.sadd(self.PROCESSING_SET, task_id)
        
        return task_id
    
    async def mark_task_completed(self, task_id: str):
        """Mark task as completed and remove from processing set"""
        await self.redis.srem(self.PROCESSING_SET, task_id)
        await self.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            progress=100
        )
    
    async def mark_task_failed(self, task_id: str, error: str):
        """Mark task as failed"""
        await self.redis.srem(self.PROCESSING_SET, task_id)
        await self.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error=error,
            completed_at=datetime.utcnow()
        )
    
    async def requeue_task(self, task_id: str, priority: int):
        """Requeue a task for retry"""
        await self.redis.srem(self.PROCESSING_SET, task_id)
        await self.redis.zadd(self.QUEUE_KEY, {task_id: priority})
        
        task_data = await self.redis.get(f"{self.TASK_PREFIX}{task_id}")
        if task_data:
            task_dict = json.loads(task_data)
            task_dict["retry_count"] = task_dict.get("retry_count", 0) + 1
            task_dict["status"] = TaskStatus.RETRYING
            task_dict["updated_at"] = datetime.utcnow().isoformat()
            
            await self.redis.set(
                f"{self.TASK_PREFIX}{task_id}",
                json.dumps(task_dict)
            )
    
    async def get_all_tasks(self, limit: int = 100) -> List[TaskResponse]:
        """Get all tasks"""
        tasks = []
        cursor = 0
        
        while True:
            cursor, keys = await self.redis.scan(
                cursor=cursor,
                match=f"{self.TASK_PREFIX}*",
                count=limit
            )
            
            for key in keys:
                task_data = await self.redis.get(key)
                if task_data:
                    task_dict = json.loads(task_data)
                    tasks.append(TaskResponse(**task_dict))
            
            if cursor == 0:
                break
            
            if len(tasks) >= limit:
                break
        
        return sorted(tasks, key=lambda x: x.created_at, reverse=True)[:limit]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        all_tasks = await self.get_all_tasks(limit=1000)
        
        stats = {
            "total_tasks": len(all_tasks),
            "pending": sum(1 for t in all_tasks if t.status == TaskStatus.PENDING),
            "processing": sum(1 for t in all_tasks if t.status == TaskStatus.PROCESSING),
            "completed": sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in all_tasks if t.status == TaskStatus.FAILED),
            "retrying": sum(1 for t in all_tasks if t.status == TaskStatus.RETRYING),
        }
        
        return stats


task_queue = TaskQueue()


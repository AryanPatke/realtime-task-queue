from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.task import TaskCreate, TaskResponse, TaskStats
from app.core.task_queue import task_queue


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate):
    """Create a new task"""
    try:
        new_task = await task_queue.create_task(task)
        return new_task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task by ID"""
    task = await task_queue.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return task


@router.get("/", response_model=List[TaskResponse])
async def get_all_tasks(limit: int = 100):
    """Get all tasks"""
    try:
        tasks = await task_queue.get_all_tasks(limit=limit)
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tasks: {str(e)}"
        )


@router.get("/stats/overview", response_model=TaskStats)
async def get_task_stats():
    """Get task statistics"""
    try:
        stats = await task_queue.get_stats()
        return TaskStats(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}"
        )


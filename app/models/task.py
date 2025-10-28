from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class TaskType(str, Enum):
    """Task type enumeration"""
    EMAIL = "email"
    DATA_PROCESSING = "data_processing"
    FILE_CONVERSION = "file_conversion"
    API_CALL = "api_call"
    REPORT_GENERATION = "report_generation"


class TaskCreate(BaseModel):
    """Task creation model"""
    name: str = Field(..., description="Task name")
    task_type: TaskType = Field(..., description="Type of task")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task payload data")
    priority: int = Field(default=5, ge=1, le=10, description="Task priority (1-10)")


class TaskResponse(BaseModel):
    """Task response model"""
    task_id: str
    name: str
    task_type: TaskType
    status: TaskStatus
    payload: Dict[str, Any]
    priority: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0
    progress: int = 0  # 0-100


class TaskUpdate(BaseModel):
    """Task update model"""
    status: Optional[TaskStatus] = None
    error: Optional[str] = None
    progress: Optional[int] = None


class TaskStats(BaseModel):
    """Task statistics model"""
    total_tasks: int
    pending: int
    processing: int
    completed: int
    failed: int
    retrying: int


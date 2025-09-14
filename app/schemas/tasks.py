from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskCreate(BaseModel):
    """Schema for creating a new task"""
    task_description: str
    original_input: str
    scheduled_time: datetime


class TaskResponse(BaseModel):
    """Schema for task response"""
    id: int
    user_id: str
    task_description: str
    original_input: str
    scheduled_time: datetime
    created_at: datetime
    is_completed: bool
    is_reminded: bool
    is_called: bool
    
    class Config:
        from_attributes = True


class TaskQuery(BaseModel):
    """Schema for task queries"""
    query: str


class TaskUpdate(BaseModel):
    """Schema for updating tasks"""
    task_description: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    is_completed: Optional[bool] = None
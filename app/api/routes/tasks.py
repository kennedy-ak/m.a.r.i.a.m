from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api.deps import get_database
from app.models.models import Task
from app.schemas.tasks import TaskResponse, TaskQuery
from app.services.openai_service import OpenAIService
from app.core.lifecycle import get_scheduler_service

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Initialize services
openai_service = OpenAIService()


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    user_id: str,
    completed: Optional[bool] = None,
    limit: Optional[int] = 50,
    db: Session = Depends(get_database)
):
    """Get tasks for a user"""
    query = db.query(Task).filter(Task.user_id == user_id)
    
    if completed is not None:
        query = query.filter(Task.is_completed == completed)
    
    tasks = query.order_by(Task.scheduled_time.desc()).limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, user_id: str, db: Session = Depends(get_database)):
    """Get a specific task"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == user_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.post("/create", response_model=TaskResponse)
async def create_task(
    user_id: str,
    user_input: str,
    db: Session = Depends(get_database),
    background_tasks: BackgroundTasks = None
):
    """Create a new task from natural language input"""
    try:
        # Parse the task using OpenAI
        parsed_task = await openai_service.parse_task(user_input)
        
        # Create new task
        new_task = Task(
            user_id=user_id,
            task_description=parsed_task["task_description"],
            original_input=user_input,
            scheduled_time=parsed_task["scheduled_time"]
        )
        
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        # Schedule reminders using scheduler service
        scheduler_service = get_scheduler_service()
        if scheduler_service:
            scheduler_service.schedule_task_reminders(new_task)
        
        return new_task
        
    except Exception as e:
        print(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")


@router.post("/query")
async def query_tasks(
    user_id: str,
    query: str,
    db: Session = Depends(get_database)
):
    """Query tasks using natural language"""
    try:
        # Get user's tasks
        tasks = db.query(Task).filter(
            Task.user_id == user_id,
            Task.is_completed == False,
            Task.scheduled_time > datetime.now()
        ).order_by(Task.scheduled_time).all()
        
        # Process query with OpenAI
        response = await openai_service.query_tasks(query, tasks)
        
        return {
            "query": query,
            "response": response,
            "task_count": len(tasks)
        }
        
    except Exception as e:
        print(f"Error querying tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to query tasks")


@router.put("/{task_id}/complete")
async def complete_task(
    task_id: int,
    user_id: str,
    db: Session = Depends(get_database)
):
    """Mark a task as completed"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == user_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.is_completed = True
    db.commit()
    
    # Cancel scheduled reminders
    scheduler_service = get_scheduler_service()
    if scheduler_service:
        scheduler_service.cancel_task_reminders(task_id)
    
    return {"message": "Task marked as completed", "task": task}


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    user_id: str,
    db: Session = Depends(get_database)
):
    """Delete a task"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == user_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    
    # Cancel scheduled reminders
    scheduler_service = get_scheduler_service()
    if scheduler_service:
        scheduler_service.cancel_task_reminders(task_id)
    
    return {"message": "Task deleted successfully"}
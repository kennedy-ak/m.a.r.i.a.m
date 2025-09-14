from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import asyncio
import os
from contextlib import asynccontextmanager

# Import our services
from models import Task, get_db, create_tables
from telegram_service import TelegramBot
from openai_service import OpenAIService
from mnotify_service import MnotifyService
from scheduler_service import TaskScheduler
from dotenv import load_dotenv

load_dotenv()

# Global variables for services
telegram_bot = None
scheduler_service = None


# Pydantic models for API
class TaskCreate(BaseModel):
    task_description: str
    original_input: str
    scheduled_time: datetime


class TaskResponse(BaseModel):
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
    query: str


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    global telegram_bot, scheduler_service
    
    print("🚀 Starting Personal Assistant Bot...")
    
    # Create database tables
    create_tables()
    print("✅ Database tables created")
    
    # Initialize services
    scheduler_service = TaskScheduler()
    print("✅ Task scheduler initialized")
    
    # Initialize and start Telegram bot
    telegram_bot = TelegramBot()
    
    # Start bot in background task
    bot_task = asyncio.create_task(telegram_bot.run())
    print("✅ Telegram bot started")
    
    yield
    
    # Cleanup
    print("🛑 Shutting down...")
    if telegram_bot:
        await telegram_bot.stop()
    if scheduler_service:
        scheduler_service.shutdown()
    
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass
    
    print("✅ Shutdown complete")


# Create FastAPI app with lifespan management
app = FastAPI(
    title="Personal Assistant Bot API",
    description="API for managing personal tasks with natural language processing",
    version="1.0.0",
    lifespan=lifespan
)

# Initialize services for API endpoints
openai_service = OpenAIService()
mnotify_service = MnotifyService()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Personal Assistant Bot API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "tasks": "/tasks",
            "create_task": "/tasks/create",
            "query_tasks": "/tasks/query"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    
    # Test service connections
    services_status = {
        "database": "connected",
        "openai": "unknown",
        "mnotify": "unknown",
        "telegram_bot": "running" if telegram_bot else "stopped",
        "scheduler": "running" if scheduler_service else "stopped"
    }
    
    # Test Mnotify connection
    try:
        mnotify_status = await mnotify_service.test_connection()
        services_status["mnotify"] = "connected" if mnotify_status else "disconnected"
    except Exception:
        services_status["mnotify"] = "error"
    
    # Test OpenAI (basic test)
    try:
        # Simple test parse
        test_result = await openai_service.parse_task("test task in 1 hour")
        services_status["openai"] = "connected" if test_result else "error"
    except Exception:
        services_status["openai"] = "error"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        services=services_status
    )


@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    user_id: str,
    completed: Optional[bool] = None,
    limit: Optional[int] = 50,
    db: Session = Depends(get_db)
):
    """Get tasks for a user"""
    query = db.query(Task).filter(Task.user_id == user_id)
    
    if completed is not None:
        query = query.filter(Task.is_completed == completed)
    
    tasks = query.order_by(Task.scheduled_time.desc()).limit(limit).all()
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, user_id: str, db: Session = Depends(get_db)):
    """Get a specific task"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == user_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@app.post("/tasks/create", response_model=TaskResponse)
async def create_task(
    user_id: str,
    user_input: str,
    db: Session = Depends(get_db),
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
        
        # Schedule reminders using global scheduler
        if scheduler_service:
            scheduler_service.schedule_task_reminders(new_task)
        
        return new_task
        
    except Exception as e:
        print(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")


@app.post("/tasks/query")
async def query_tasks(
    user_id: str,
    query: str,
    db: Session = Depends(get_db)
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


@app.put("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    user_id: str,
    db: Session = Depends(get_db)
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
    if scheduler_service:
        scheduler_service.cancel_task_reminders(task_id)
    
    return {"message": "Task marked as completed", "task": task}


@app.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    user_id: str,
    db: Session = Depends(get_db)
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
    if scheduler_service:
        scheduler_service.cancel_task_reminders(task_id)
    
    return {"message": "Task deleted successfully"}


@app.get("/scheduler/jobs")
async def get_scheduled_jobs():
    """Get information about scheduled jobs"""
    if not scheduler_service:
        return {"jobs": [], "message": "Scheduler not initialized"}
    
    jobs = scheduler_service.get_scheduled_jobs()
    job_info = []
    
    for job in jobs:
        job_info.append({
            "id": job.id,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "func_name": job.func.__name__ if job.func else None
        })
    
    return {
        "jobs": job_info,
        "total_jobs": len(jobs)
    }


@app.post("/test/sms")
async def test_sms(message: str = "Test message from Personal Assistant Bot"):
    """Test SMS functionality"""
    try:
        result = await mnotify_service.send_sms_reminder(message, datetime.now().strftime('%Y-%m-%d %H:%M'))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/test/call")
async def test_call(message: str = "Test call from Personal Assistant Bot"):
    """Test voice call functionality"""
    try:
        result = await mnotify_service.make_voice_call(message)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"🌐 Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
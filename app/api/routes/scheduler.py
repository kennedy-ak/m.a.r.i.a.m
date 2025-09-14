from fastapi import APIRouter
from app.core.lifecycle import get_scheduler_service

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/jobs")
async def get_scheduled_jobs():
    """Get information about scheduled jobs"""
    scheduler_service = get_scheduler_service()
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
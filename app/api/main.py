from fastapi import APIRouter
from app.api.routes import tasks, health, scheduler, test

api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router)
api_router.include_router(tasks.router)
api_router.include_router(scheduler.router)
api_router.include_router(test.router)
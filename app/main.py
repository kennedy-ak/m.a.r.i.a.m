from fastapi import FastAPI

from app.core.config import settings
from app.core.lifecycle import lifespan
from app.api.main import api_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.app_name,
        description=settings.description,
        version=settings.app_version,
        lifespan=lifespan,
        debug=settings.debug
    )
    
    # Include API router
    app.include_router(api_router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": settings.app_name,
            "status": "running",
            "version": settings.app_version,
            "environment": settings.environment,
            "endpoints": {
                "health": "/health",
                "tasks": "/tasks",
                "create_task": "/tasks/create",
                "query_tasks": "/tasks/query",
                "scheduler": "/scheduler",
                "test": "/test"
            }
        }
    
    return app


app = create_app()
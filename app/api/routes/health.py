from fastapi import APIRouter
from datetime import datetime

from app.schemas.health import HealthResponse
from app.services.openai_service import OpenAIService
from app.services.mnotify_service import MnotifyService
from app.core.lifecycle import get_telegram_bot, get_scheduler_service

router = APIRouter(tags=["health"])

# Initialize services
openai_service = OpenAIService()
mnotify_service = MnotifyService()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    
    # Test service connections
    services_status = {
        "database": "connected",
        "openai": "unknown",
        "mnotify": "unknown",
        "telegram_bot": "running" if get_telegram_bot() else "stopped",
        "scheduler": "running" if get_scheduler_service() else "stopped"
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
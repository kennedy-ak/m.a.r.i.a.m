from fastapi import APIRouter
from datetime import datetime

from app.services.mnotify_service import MnotifyService

router = APIRouter(prefix="/test", tags=["testing"])

# Initialize services
mnotify_service = MnotifyService()


@router.post("/sms")
async def test_sms(message: str = "Test message from Personal Assistant Bot"):
    """Test SMS functionality"""
    try:
        result = await mnotify_service.send_sms_reminder(message, datetime.now().strftime('%Y-%m-%d %H:%M'))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/call")
async def test_call():
    """Test voice call functionality using audio file"""
    try:
        result = await mnotify_service.make_voice_call()
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
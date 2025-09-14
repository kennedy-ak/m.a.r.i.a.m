"""
Test script to verify all imports work correctly
"""
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test all critical imports"""
    try:
        print("Testing core imports...")
        from app.core.config import settings
        print("[OK] Core config imported")
        
        print("Testing model imports...")
        from app.models.models import Task, get_db, create_tables
        print("[OK] Models imported")
        
        print("Testing service imports...")
        from app.services.openai_service import OpenAIService
        print("[OK] OpenAI service imported")
        
        from app.services.mnotify_service import MnotifyService
        print("[OK] Mnotify service imported")
        
        from app.services.telegram_service import TelegramBot
        print("[OK] Telegram service imported")
        
        from app.services.scheduler_service import TaskScheduler
        print("[OK] Scheduler service imported")
        
        print("Testing API imports...")
        from app.api.routes import tasks, health, scheduler, test
        print("[OK] API routes imported")
        
        from app.main import app
        print("[OK] FastAPI app imported")
        
        print("\n[SUCCESS] All imports successful!")
        
        # Test configuration
        print(f"\nConfiguration check:")
        print(f"App name: {settings.app_name}")
        print(f"Database URL: {settings.database_url[:20]}...")
        print(f"OpenAI key: {'[OK] Set' if settings.openai_api_key else '[ERROR] Missing'}")
        print(f"Telegram token: {'[OK] Set' if settings.telegram_bot_token else '[ERROR] Missing'}")
        print(f"Mnotify key: {'[OK] Set' if settings.mnotify_api_key else '[ERROR] Missing'}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
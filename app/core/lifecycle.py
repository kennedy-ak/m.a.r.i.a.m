import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.models.models import create_tables
from app.services.telegram_service import TelegramBot
from app.services.scheduler_service import TaskScheduler

# Global variables for services
telegram_bot = None
scheduler_service = None


def get_telegram_bot():
    """Get the global telegram bot instance"""
    return telegram_bot


def get_scheduler_service():
    """Get the global scheduler service instance"""
    return scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    global telegram_bot, scheduler_service
    
    print("Starting Personal Assistant Bot...")
    
    # Create database tables
    create_tables()
    print("[OK] Database tables created")
    
    # Initialize services
    scheduler_service = TaskScheduler()
    print("[OK] Task scheduler initialized")
    
    # Initialize and start Telegram bot
    telegram_bot = TelegramBot()
    
    # Start bot in background task
    bot_task = asyncio.create_task(telegram_bot.run())
    print("[OK] Telegram bot started")
    
    yield
    
    # Cleanup
    print("[INFO] Shutting down...")
    if telegram_bot:
        await telegram_bot.stop()
    if scheduler_service:
        scheduler_service.shutdown()
    
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass
    
    print("[OK] Shutdown complete")
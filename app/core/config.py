import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    app_name: str = "Personal Assistant Bot API"
    app_version: str = "1.0.0"
    description: str = "API for managing personal tasks with natural language processing"
    
    # Server Config
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", 8000))
    reload: bool = os.getenv("RELOAD", "true").lower() == "true"
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "")
    
    # External APIs
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Mnotify SMS Service
    mnotify_api_key: Optional[str] = os.getenv("MNOTIFY_API_KEY")
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    class Config:
        case_sensitive = False


settings = Settings()
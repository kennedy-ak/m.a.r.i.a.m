from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from app.core.config import settings

# Database configuration
DATABASE_URL = settings.database_url
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Task(Base):
    """
    Task model for storing user tasks
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # Telegram user ID
    task_description = Column(Text, nullable=False)
    original_input = Column(Text, nullable=False)  # Original user input
    scheduled_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_completed = Column(Boolean, default=False)
    is_reminded = Column(Boolean, default=False)  # SMS reminder sent
    is_called = Column(Boolean, default=False)    # Voice call made
    
    def __repr__(self):
        return f"<Task(id={self.id}, description='{self.task_description}', scheduled_time={self.scheduled_time})>"


# Create tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


# Database dependency for FastAPI
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
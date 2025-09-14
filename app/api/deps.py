from typing import Generator
from sqlalchemy.orm import Session
from app.models.models import get_db


def get_database() -> Generator[Session, None, None]:
    """Database dependency for FastAPI endpoints"""
    yield from get_db()
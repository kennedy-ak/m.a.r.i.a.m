from pydantic import BaseModel
from datetime import datetime
from typing import Dict


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    services: Dict[str, str]
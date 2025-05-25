from typing import Dict, Any
from pydantic import BaseModel
from datetime import datetime

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    context: Dict[str, Any] = {}

class TravelPlanRequest(BaseModel):
    destination: str
    start_date: datetime
    end_date: datetime
    preferences: Dict[str, Any]

class ShareResponse(BaseModel):
    share_url: str 
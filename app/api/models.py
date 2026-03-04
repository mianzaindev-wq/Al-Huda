"""
api/models.py
-------------
Pydantic request and response schemas for the Al-Huda API.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.core.config import MAX_MESSAGE_LENGTH


class UserProfile(BaseModel):
    """User display profile — name and optional avatar path."""

    name: str = Field(default="User", min_length=1, max_length=100)
    image_path: Optional[str] = None


class ChatRequest(BaseModel):
    """Payload for /chat and /chat-stream endpoints."""

    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    conversation_id: Optional[str] = None
    use_vector_search: bool = True

    @field_validator("message", mode="before")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v


class ChatResponse(BaseModel):
    """Standard response envelope for /chat."""

    reply: str
    timestamp: str
    conversation_id: str
    status: str = "success"
    sources_used: Optional[List[Dict]] = None
    context_chunks: Optional[int] = None
    web_extraction_performed: bool = False
    messages_in_chat: Optional[int] = None
    processing_time: Optional[float] = None

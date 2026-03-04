"""
api/routes/database.py
----------------------
Endpoints for inspecting and managing the Islamic knowledge base:
  POST   /rescan-database
  GET    /health
  GET    /stats
  DELETE /clear-conversation/{conversation_id}
  GET    /conversations
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import DATABASE_FOLDER, DOCX_AVAILABLE, MAX_CHAT_MESSAGES, MISTRAL_MODEL
from app.services.chat_memory import chat_memory
from app.services.document_processor import scan_database_folder
from app.services.rate_limiter import rate_limiter
from app.services.vector_db import vector_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@router.get("/health")
async def health_check():
    """Return a snapshot of the system's current health and configuration."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mistral_api": "connected",
        "mistral_model": MISTRAL_MODEL,
        "vector_db": vector_db.get_stats(),
        "chat_memory": chat_memory.get_stats(),
        "database_folder": DATABASE_FOLDER,
        "database_folder_exists": Path(DATABASE_FOLDER).exists(),
        "rate_limiter": {
            "requests_in_window": rate_limiter.request_count,
            "max_requests": rate_limiter.max_requests,
        },
        "features": {
            "pdf_support": True,
            "txt_support": True,
            "docx_support": DOCX_AVAILABLE,
            "web_scraping": True,
            "vector_search": True,
            "chat_memory": True,
            "rate_limiting": True,
            "async_processing": True,
        },
    }


# ---------------------------------------------------------------------------
# DataBase folder rescan
# ---------------------------------------------------------------------------

@router.post("/rescan-database")
async def rescan_database():
    """Re-index all supported files in the DataBase/ folder."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, scan_database_folder)
        return result
    except Exception as exc:
        logger.error(f"rescan_database error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# System statistics
# ---------------------------------------------------------------------------

@router.get("/stats")
async def get_stats():
    """Return aggregate statistics for the vector DB, chat memory, and rate limiter."""
    return {
        "vector_db": vector_db.get_stats(),
        "chat_memory": chat_memory.get_stats(),
        "database_folder": DATABASE_FOLDER,
        "database_folder_exists": Path(DATABASE_FOLDER).exists(),
        "supported_formats": ["PDF", "TXT", "DOCX"],
        "docx_support_available": DOCX_AVAILABLE,
        "max_messages_per_chat": MAX_CHAT_MESSAGES,
        "rate_limiter": {
            "max_requests_per_window": rate_limiter.max_requests,
            "window_seconds": rate_limiter.window,
            "current_requests": rate_limiter.request_count,
        },
    }


# ---------------------------------------------------------------------------
# Conversation management
# ---------------------------------------------------------------------------

@router.delete("/clear-conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Delete all messages in a specific conversation."""
    try:
        chat_memory.clear_conversation(conversation_id)
        return {
            "status": "success",
            "message": f"Conversation {conversation_id} cleared",
            "conversation_id": conversation_id,
        }
    except Exception as exc:
        logger.error(f"clear_conversation error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/conversations")
async def list_conversations():
    """List all active conversations with their metadata and message counts."""
    return {
        "conversations": [
            {
                "conversation_id": conv_id,
                "metadata": chat_memory.conversation_metadata.get(conv_id, {}),
                "message_count": len(chat_memory.conversations.get(conv_id, [])),
            }
            for conv_id in chat_memory.conversations
        ]
    }

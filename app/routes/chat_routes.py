from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ClearChatRequest,
    ClearChatResponse,
    ChatHistoryResponse,
    ChatMessageItem
)
from app.services.chat_service import ChatService
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

def get_chat_service():
    return ChatService()

def get_memory_service():
    return MemoryService()

@router.post("", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    RAG-powered chat endpoint with conversational memory.
    Answers product questions using retrieved knowledge base context.
    """
    try:
        response = chat_service.handle_chat(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chat response: {str(e)}")

@router.post("/clear", response_model=ClearChatResponse)
def clear_chat_history(
    request: ClearChatRequest,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Clears all conversation memory for a specified session ID.
    """
    try:
        deleted = memory_service.clear_session(request.session_id)
        return ClearChatResponse(
            session_id=request.session_id,
            message=f"Conversation history for session '{request.session_id}' cleared successfully ({deleted} messages removed)."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversation memory: {str(e)}")

@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
def get_chat_history(
    session_id: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Retrieves full conversation history for a given session ID.
    """
    try:
        history = memory_service.get_history(session_id=session_id, limit=100)
        messages = [
            ChatMessageItem(
                role=item["role"],
                content=item["content"],
                sources=item.get("sources", [])
            )
            for item in history
        ]
        return ChatHistoryResponse(
            session_id=session_id,
            total_messages=len(messages),
            messages=messages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")

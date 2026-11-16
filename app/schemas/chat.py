from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique conversation session identifier", min_length=1)
    question: str = Field(..., description="User query about the product", min_length=1)

class ChatResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    sources: List[str] = Field(default_factory=list, description="Source documents referenced")
    context_retrieved: Optional[bool] = Field(default=True, description="Whether knowledge context was retrieved")

class ClearChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique conversation session identifier to clear")

class ClearChatResponse(BaseModel):
    session_id: str
    message: str

class ChatMessageItem(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str
    timestamp: Optional[datetime] = None
    sources: Optional[List[str]] = None

class ChatHistoryResponse(BaseModel):
    session_id: str
    total_messages: int
    messages: List[ChatMessageItem]

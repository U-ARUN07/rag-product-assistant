import pytest
from pydantic import ValidationError
from app.routes.health_routes import health_check
from app.routes.chat_routes import (
    chat_endpoint,
    get_chat_history,
    clear_chat_history,
    get_chat_service,
    get_memory_service
)
from app.schemas.chat import ChatRequest, ClearChatRequest

def test_health_check_endpoint():
    data = health_check()
    assert isinstance(data, dict)
    assert data["status"] == "healthy"
    assert "version" in data
    assert "app_name" in data
    assert data["vector_store_initialized"] is True

def test_chat_endpoint_valid_request():
    req = ChatRequest(
        session_id="api_test_session_1",
        question="How does internship matching work?"
    )
    resp = chat_endpoint(req, chat_service=get_chat_service())
    assert resp.session_id == "api_test_session_1"
    assert "similarity" in resp.answer.lower() or "matching" in resp.answer.lower()
    assert isinstance(resp.sources, list)
    assert resp.context_retrieved is True

def test_chat_history_and_clear_endpoints():
    session_id = "api_test_session_history"
    chat_svc = get_chat_service()
    mem_svc = get_memory_service()

    # Send a message
    chat_endpoint(ChatRequest(session_id=session_id, question="How do I upload my resume?"), chat_service=chat_svc)

    # Retrieve history
    hist_resp = get_chat_history(session_id=session_id, memory_service=mem_svc)
    assert hist_resp.session_id == session_id
    assert hist_resp.total_messages >= 2

    # Clear history
    clear_resp = clear_chat_history(ClearChatRequest(session_id=session_id), memory_service=mem_svc)
    assert "cleared successfully" in clear_resp.message

    # Verify history is empty
    empty_resp = get_chat_history(session_id=session_id, memory_service=mem_svc)
    assert empty_resp.total_messages == 0

def test_chat_endpoint_validation():
    # Empty question raises ValidationError
    with pytest.raises(ValidationError):
        ChatRequest(session_id="test", question="")

    # Empty session_id raises ValidationError
    with pytest.raises(ValidationError):
        ChatRequest(session_id="", question="Valid question")

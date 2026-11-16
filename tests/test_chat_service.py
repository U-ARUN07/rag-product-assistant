import pytest
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService
from app.services.vector_store import get_vector_store

@pytest.fixture(scope="module", autouse=True)
def init_vector_store():
    # Ensure vector store is built before testing chat service
    get_vector_store().build_vector_database(force_rebuild=False)

def test_chat_service_product_overview():
    svc = ChatService()
    req = ChatRequest(
        session_id="test_chat_overview",
        question="What is this product and how does it work?"
    )
    resp = svc.handle_chat(req)

    assert resp.session_id == "test_chat_overview"
    assert "Internship Application Agent" in resp.answer
    assert resp.context_retrieved is True

def test_chat_service_follow_up_sequence():
    svc = ChatService()
    session_id = "test_chat_followup"

    # Turn 1
    req1 = ChatRequest(
        session_id=session_id,
        question="How does internship matching work?"
    )
    resp1 = svc.handle_chat(req1)
    assert "similarity" in resp1.answer.lower() or "matching" in resp1.answer.lower()

    # Turn 2: Follow-up question
    req2 = ChatRequest(
        session_id=session_id,
        question="What about the score?"
    )
    resp2 = svc.handle_chat(req2)
    assert "score" in resp2.answer.lower()
    assert "guarantee" in resp2.answer.lower() or "similarity" in resp2.answer.lower()

def test_chat_service_refuses_out_of_scope():
    svc = ChatService()
    req = ChatRequest(
        session_id="test_out_of_scope",
        question="Tell me the latest cricket score."
    )
    resp = svc.handle_chat(req)

    assert "Internship Application Agent" in resp.answer
    assert resp.context_retrieved is False
    assert len(resp.sources) == 0

def test_chat_service_handles_missing_unsupported_info():
    svc = ChatService()
    req = ChatRequest(
        session_id="test_missing_info",
        question="What is the pricing tier for enterprise corporate university recruitment licenses?"
    )
    resp = svc.handle_chat(req)
    assert "not available in the current product documentation" in resp.answer.lower()

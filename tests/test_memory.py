import pytest
from app.database.conversation_db import ConversationDB
from app.services.memory_service import MemoryService

def test_sqlite_memory_persistence_and_isolation(tmp_path):
    db_file = tmp_path / "test_memory.db"
    db = ConversationDB(db_path=str(db_file))
    memory = MemoryService(db=db)

    session_a = "session_alice"
    session_b = "session_bob"

    # Add messages to Session A
    memory.add_user_message(session_a, "How does internship matching work?")
    memory.add_assistant_message(session_a, "It uses semantic similarity.", sources=["internship_matching.md"])

    # Add messages to Session B
    memory.add_user_message(session_b, "How do I upload my resume?")
    memory.add_assistant_message(session_b, "Upload PDF or DOCX.", sources=["resume_upload.md"])

    # Check isolation
    history_a = memory.get_history(session_a)
    history_b = memory.get_history(session_b)

    assert len(history_a) == 2
    assert len(history_b) == 2
    assert history_a[0]["content"] == "How does internship matching work?"
    assert history_b[0]["content"] == "How do I upload my resume?"

def test_follow_up_query_contextualization(tmp_path):
    db_file = tmp_path / "test_followup.db"
    db = ConversationDB(db_path=str(db_file))
    memory = MemoryService(db=db)

    session = "session_followup_test"
    memory.add_user_message(session, "How does internship matching work?")
    memory.add_assistant_message(session, "The system compares candidate resume info with internship postings.")

    # User asks follow up: "What about the score?"
    rewritten = memory.contextualize_query(session, "What about the score?")
    assert "internship matching" in rewritten.lower() or "matching" in rewritten.lower()

def test_clearing_memory(tmp_path):
    db_file = tmp_path / "test_clear.db"
    db = ConversationDB(db_path=str(db_file))
    memory = MemoryService(db=db)

    session = "session_to_clear"
    memory.add_user_message(session, "Hello assistant")
    memory.add_assistant_message(session, "Hello user")

    assert len(memory.get_history(session)) == 2

    # Clear memory
    deleted = memory.clear_session(session)
    assert deleted == 2
    assert len(memory.get_history(session)) == 0

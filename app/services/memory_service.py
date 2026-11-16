import re
from typing import List, Dict, Any, Optional
from app.config import get_settings
from app.database.conversation_db import ConversationDB

class MemoryService:
    """
    Manages conversational memory across sessions:
    - Stores and retrieves interaction history from SQLite
    - Formats history for LLM prompts
    - Contextualizes follow-up questions (query rewriting)
    - Enforces sliding context window
    """

    def __init__(self, db: Optional[ConversationDB] = None):
        self.db = db or ConversationDB()
        self.settings = get_settings()

    def add_user_message(self, session_id: str, content: str):
        self.db.add_message(session_id=session_id, role="user", content=content)

    def add_assistant_message(self, session_id: str, content: str, sources: Optional[List[str]] = None):
        self.db.add_message(session_id=session_id, role="assistant", content=content, sources=sources)

    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        limit = limit or self.settings.MAX_HISTORY_MESSAGES
        return self.db.get_history(session_id=session_id, limit=limit)

    def format_history_for_prompt(self, session_id: str, limit: Optional[int] = None) -> str:
        """Formats the most recent conversation turns into a string for LLM prompt."""
        limit = limit or self.settings.MAX_HISTORY_MESSAGES
        history = self.get_history(session_id=session_id, limit=limit)
        if not history:
            return "No previous conversation history."

        lines = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def clear_session(self, session_id: str) -> int:
        """Clears memory for a specific session."""
        return self.db.clear_history(session_id=session_id)

    def contextualize_query(self, session_id: str, question: str) -> str:
        """
        Detects follow-up questions and rewrites them into standalone retrieval queries
        using conversation history context.
        """
        history = self.get_history(session_id=session_id, limit=self.settings.MAX_HISTORY_MESSAGES)
        if not history:
            return question

        q_lower = question.strip().lower()

        # Follow-up indicators
        pronoun_triggers = [
            "what about", "how about", "why", "and the", "what is the score",
            "what does that mean", "explain that", "explain step", "how do i do that",
            "can you explain", "what else", "tell me more", "how does it", "does it",
            "is it", "which one", "the score", "this feature", "that step", "it"
        ]

        is_short = len(q_lower.split()) <= 5
        has_trigger = any(q_lower.startswith(t) or f" {t} " in f" {q_lower} " for t in pronoun_triggers)

        if not (is_short or has_trigger):
            return question

        # Identify previous user topic and assistant topic from history
        recent_user_questions = [m["content"] for m in history if m["role"] == "user"]
        recent_assistant_replies = [m["content"] for m in history if m["role"] == "assistant"]

        last_user_q = recent_user_questions[-1] if recent_user_questions else ""
        last_asst_reply = recent_assistant_replies[-1] if recent_assistant_replies else ""

        # Extract dominant subject from last user question
        last_subject = ""
        known_topics = {
            "internship matching": ["matching", "internship matching", "match score", "similarity"],
            "resume upload": ["resume upload", "upload resume", "parsing", "resume", "extract"],
            "cover letter": ["cover letter", "letter generation", "tailored cover letter"],
            "interview preparation": ["interview", "interview prep", "questions", "star method"],
            "application tracking": ["tracking", "application tracker", "kanban", "status"],
            "product overview": ["product overview", "internship application agent", "features", "workflow"]
        }

        for topic, keywords in known_topics.items():
            if any(k in last_user_q.lower() for k in keywords) or any(k in last_asst_reply.lower() for k in keywords):
                last_subject = topic
                break

        if not last_subject and last_user_q:
            # Fallback: clean the last question to use as contextual prefix
            last_subject = re.sub(r'^(how|what|why|can you|explain|does|is|the)\s+', '', last_user_q, flags=re.I).strip("?., ")

        if last_subject:
            contextualized = f"{question} (in the context of {last_subject})"
            return contextualized

        return question

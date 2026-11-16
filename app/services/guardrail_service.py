import re
from typing import Tuple, Optional
from app.config import get_settings

class GuardrailService:
    """
    Enforces product scope, hallucination prevention, and prompt injection defense.
    """

    # Disallowed domains / out-of-scope triggers
    OUT_OF_SCOPE_PATTERNS = [
        r"\b(cricket|football|soccer|basketball|tennis|ipl|nba|world cup|olympics)\b",
        r"\b(weather|forecast|rain today|temperature in)\b",
        r"\b(recipe|how to cook|bake a cake|ingredients for)\b",
        r"\b(movie|cinema|netflix|actor|actress|box office)\b",
        r"\b(stock price|crypto|bitcoin|ethereum|forex)\b",
        r"\b(politics|election|president|prime minister|war)\b",
        r"\b(solve this math|algebra|calculus integral)\b",
        r"\b(write code for snake game|build a react app from scratch)\b"
    ]

    # Prompt injection and jailbreak patterns
    INJECTION_PATTERNS = [
        r"ignore (all )?(previous|above) instructions",
        r"disregard (all )?(previous|system) (prompts|rules)",
        r"you are now (DAN|an unrestricted|evil)",
        r"(reveal|print|show|output|leak) (your |the )?(system prompt|instructions|credentials|api key)",
        r"bypass (all )?(safety|guardrails)",
        r"system override"
    ]

    # Valid product topics and keywords
    VALID_PRODUCT_KEYWORDS = [
        "internship", "agent", "resume", "upload", "parse", "parsing", "match", "matching",
        "score", "similarity", "cover letter", "interview", "preparation", "tracker",
        "tracking", "application", "workflow", "feature", "features", "product", "candidate",
        "step", "steps", "how to", "status", "profile", "document", "docx", "pdf", "txt",
        "kanban", "star method", "star", "skill", "skills", "limitation", "limitations", "overview",
        "user", "users", "target", "target users", "platform", "who", "voice", "speech",
        "pricing", "license", "edit", "verify", "external", "manual", "purpose", "benefit",
        "benefits", "format", "formats", "size", "limit", "limits", "export", "download",
        "practice", "behavioral", "technical", "mock", "mode", "modes", "stages", "pipeline",
        "mentor", "mentors", "student", "students", "graduate", "graduates", "roadmap", "planned"
    ]

    DECLINE_MESSAGE = (
        "I'm here to help with the Internship Application Agent. "
        "I can explain its features, document processing, internship matching, "
        "cover letter generation, application tracking, and interview preparation workflows."
    )

    INSUFFICIENT_CONTEXT_MESSAGE = (
        "The requested information is not available in the current product documentation. "
        "I can only provide details about verified and documented features of the Internship Application Agent."
    )

    INJECTION_BLOCKED_MESSAGE = (
        "I cannot fulfill requests that conflict with safety guidelines or product scope. "
        "Please ask questions related to the Internship Application Agent."
    )

    def __init__(self):
        self.settings = get_settings()

    def check_injection(self, query: str) -> Tuple[bool, Optional[str]]:
        """Detects prompt injection or jailbreak attempts."""
        q_lower = query.lower()
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, q_lower):
                return True, self.INJECTION_BLOCKED_MESSAGE
        return False, None

    def check_scope(self, query: str, has_prior_context: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Determines if the query is within product scope.
        Returns (is_in_scope, refusal_message_if_out_of_scope).
        """
        q_lower = query.lower().strip()

        # Check explicit out of scope patterns
        for pattern in self.OUT_OF_SCOPE_PATTERNS:
            if re.search(pattern, q_lower):
                return False, self.DECLINE_MESSAGE

        # If in an ongoing conversation and query is short (e.g., "what about the score?"), allow it
        if has_prior_context and len(q_lower.split()) <= 6:
            return True, None

        # Check for presence of product-relevant terminology
        has_product_word = any(kw in q_lower for kw in self.VALID_PRODUCT_KEYWORDS)
        if has_product_word:
            return True, None

        # Generic conversational greetings
        greetings = ["hi", "hello", "hey", "good morning", "good evening", "help", "who are you"]
        if any(q_lower == g or q_lower.startswith(g + " ") for g in greetings):
            return True, None

        # Default refusal if query shares no relation with the product
        return False, self.DECLINE_MESSAGE

    def validate_groundedness(self, has_relevant_context: bool, top_score: float = 0.0) -> Tuple[bool, Optional[str]]:
        """
        Verifies if retrieval produced sufficient grounded context to answer.
        """
        if not has_relevant_context or top_score < self.settings.SIMILARITY_SCORE_THRESHOLD:
            return False, self.INSUFFICIENT_CONTEXT_MESSAGE
        return True, None

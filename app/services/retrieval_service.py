from typing import List, Dict, Any, Tuple
from app.config import get_settings
from app.services.vector_store import get_vector_store, VectorStoreService

class RetrievalService:
    """
    High-level retrieval coordinator:
    - Queries vector store
    - Filters by similarity threshold
    - Formats retrieved chunks for the prompt context
    - Gathers source citations
    """

    def __init__(self, vector_store: VectorStoreService = None):
        self.vector_store = vector_store or get_vector_store()
        self.settings = get_settings()

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        threshold: float = None
    ) -> Dict[str, Any]:
        """
        Retrieves top_k chunks for the query, applies threshold filtering,
        and formats the context string.
        """
        top_k = top_k or self.settings.RETRIEVAL_TOP_K
        threshold = threshold if threshold is not None else self.settings.SIMILARITY_SCORE_THRESHOLD

        raw_chunks = self.vector_store.retrieve_documents(query=query, top_k=top_k)

        # Filter by threshold
        relevant_chunks = [c for c in raw_chunks if c.get("score", 0.0) >= threshold]

        # Extract unique sources in order of relevance
        sources = []
        for c in relevant_chunks:
            src = c.get("source") or c.get("metadata", {}).get("source")
            if src and src not in sources:
                sources.append(src)

        # Build context text
        formatted_context_parts = []
        for i, c in enumerate(relevant_chunks, 1):
            source = c.get("source", "Documentation")
            text = c.get("text", "").strip()
            score = c.get("score", 0.0)
            formatted_context_parts.append(
                f"[Document {i} - Source: {source} (Relevance Score: {score})]\n{text}"
            )

        context_text = "\n\n".join(formatted_context_parts)
        has_context = len(relevant_chunks) > 0

        return {
            "context_text": context_text,
            "sources": sources,
            "has_relevant_context": has_context,
            "chunks": relevant_chunks,
            "raw_chunks": raw_chunks
        }

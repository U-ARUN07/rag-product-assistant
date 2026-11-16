from typing import List, Dict, Any, Optional
from app.config import get_settings
from app.services.document_loader import Document

# Try importing standard LangChain text splitter; provide fallback if needed
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        RecursiveCharacterTextSplitter = None


class FallbackRecursiveCharacterTextSplitter:
    """Robust recursive character text splitter when langchain package is modularized."""
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100, separators: Optional[List[str]] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        current_sep = self.separators[0]
        splits = text.split(current_sep)
        
        current_chunk = ""
        for part in splits:
            part_str = part + (current_sep if current_sep != "" else "")
            if len(current_chunk) + len(part_str) <= self.chunk_size:
                current_chunk += part_str
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                if len(part_str) > self.chunk_size and len(self.separators) > 1:
                    sub_splitter = FallbackRecursiveCharacterTextSplitter(
                        chunk_size=self.chunk_size,
                        chunk_overlap=self.chunk_overlap,
                        separators=self.separators[1:]
                    )
                    chunks.extend(sub_splitter.split_text(part_str))
                    current_chunk = ""
                else:
                    current_chunk = part_str

        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        return [c for c in chunks if c.strip()]


class ChunkingService:
    """Service that divides documents into semantically coherent overlapping chunks."""

    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        settings = get_settings()
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        if RecursiveCharacterTextSplitter is not None:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""]
            )
        else:
            self.splitter = FallbackRecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Splits a list of documents into chunks while preserving and enriching metadata."""
        chunked_docs: List[Document] = []

        for doc in documents:
            source = doc.metadata.get("source", "unknown")
            text_chunks = self.splitter.split_text(doc.page_content)

            for i, chunk_text in enumerate(text_chunks):
                chunk_metadata = dict(doc.metadata)
                chunk_metadata["chunk_index"] = i
                chunk_metadata["chunk_id"] = f"{source}#chunk_{i}"
                chunk_metadata["total_chunks"] = len(text_chunks)

                chunked_docs.append(Document(page_content=chunk_text, metadata=chunk_metadata))

        return chunked_docs

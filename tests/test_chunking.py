import pytest
from app.services.document_loader import Document
from app.services.chunking_service import ChunkingService

def test_chunking_service_splits_and_preserves_metadata():
    chunker = ChunkingService(chunk_size=300, chunk_overlap=50)

    sample_doc = Document(
        page_content=(
            "The Internship Application Agent helps students find matching internships.\n\n"
            "## Resume Upload\n"
            "Users can upload resumes in PDF, DOCX, or TXT format.\n\n"
            "## Semantic Matching\n"
            "The system uses dense vector embeddings to calculate similarity scores.\n\n"
            "## Cover Letter Generation\n"
            "Tailored cover letters are synthesized based on candidate projects."
        ),
        metadata={"source": "test_sample.md", "title": "Test Sample"}
    )

    chunks = chunker.split_documents([sample_doc])

    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.metadata["source"] == "test_sample.md"
        assert "chunk_id" in chunk.metadata
        assert "chunk_index" in chunk.metadata
        assert "total_chunks" in chunk.metadata
        assert len(chunk.page_content) > 0

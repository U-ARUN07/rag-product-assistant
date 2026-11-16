import pytest
from pathlib import Path
from app.services.document_loader import DocumentLoaderService

def test_document_loader_loads_markdown_files():
    loader = DocumentLoaderService()
    documents = loader.load_documents()

    assert len(documents) > 0, "Knowledge base documents should be loaded."
    
    # Check expected source files exist
    source_names = [doc.metadata.get("source") for doc in documents]
    assert "product_overview.md" in source_names
    assert "product_workflow.md" in source_names
    assert "resume_upload.md" in source_names
    assert "internship_matching.md" in source_names
    assert "cover_letter_generation.md" in source_names
    assert "interview_preparation.md" in source_names
    assert "application_tracking.md" in source_names

    # Verify content and metadata preservation
    for doc in documents:
        assert len(doc.page_content) > 50
        assert "file_path" in doc.metadata
        assert "title" in doc.metadata
        assert doc.metadata["file_extension"] in (".md", ".txt")

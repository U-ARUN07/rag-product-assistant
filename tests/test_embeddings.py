import pytest
from app.services.embedding_service import EmbeddingService

def test_embedding_dimensions_and_consistency():
    svc = EmbeddingService()

    # Query embedding
    q_vec = svc.embed_query("How does internship matching work?")
    assert isinstance(q_vec, list)
    assert len(q_vec) == 384, f"Expected 384 dimensions, got {len(q_vec)}"

    # Batch document embedding
    doc_texts = [
        "Resume upload supports PDF, DOCX, and TXT.",
        "Interview preparation uses the STAR methodology."
    ]
    batch_vecs = svc.embed_documents(doc_texts)
    assert len(batch_vecs) == 2
    assert len(batch_vecs[0]) == 384
    assert len(batch_vecs[1]) == 384

def test_empty_text_embedding_returns_valid_vector():
    svc = EmbeddingService()
    vec = svc.embed_query("")
    assert len(vec) == 384

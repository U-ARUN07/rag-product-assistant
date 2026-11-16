import pytest
from pathlib import Path
from app.services.vector_store import get_vector_store, VectorStoreService

def test_vector_database_retrieval():
    vs = get_vector_store()
    # Load already built database
    collection = vs.load_vector_database()
    assert collection is not None

    query = "How does internship matching work?"
    results = vs.retrieve_documents(query=query, top_k=3)

    assert len(results) > 0
    top_result = results[0]
    assert "text" in top_result
    assert "source" in top_result
    assert "score" in top_result
    assert top_result["score"] >= 0.0

def test_load_vector_database_returns_existing_collection():
    vs = get_vector_store()
    coll = vs.load_vector_database()
    assert coll is not None
    if hasattr(coll, "count"):
        assert coll.count() > 0

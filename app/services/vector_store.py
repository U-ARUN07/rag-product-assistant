import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from app.config import get_settings
from app.services.document_loader import Document, DocumentLoaderService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except ImportError:
    chromadb = None
    ChromaSettings = None


class VectorStoreService:
    """
    ChromaDB-backed vector database service for the knowledge base.
    Persists embeddings locally, supports top-k semantic retrieval,
    and prevents redundant rebuilding across chatbot requests.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        settings = get_settings()
        self.persist_directory = Path(persist_directory or settings.CHROMA_PERSIST_DIRECTORY)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.embedding_service = embedding_service or EmbeddingService()
        self._client = None
        self._collection = None

    def _get_client(self):
        """Initializes and returns the ChromaDB persistent client."""
        if self._client is None and chromadb is not None:
            chroma_settings = ChromaSettings(anonymized_telemetry=False, is_persistent=True) if ChromaSettings else None
            self._client = chromadb.PersistentClient(path=str(self.persist_directory), settings=chroma_settings)
        return self._client

    def load_vector_database(self):
        """Loads an existing vector database without re-indexing."""
        if self._collection is not None:
            return self._collection

        client = self._get_client()
        if client is not None:
            try:
                self._collection = client.get_collection(name=self.collection_name)
                return self._collection
            except Exception:
                # Collection does not exist yet; will need building
                return None
        else:
            fallback_index = self.persist_directory / f"{self.collection_name}_fallback.json"
            if fallback_index.exists():
                return "fallback_loaded"
            return None

    def build_vector_database(self, force_rebuild: bool = False):
        """
        Builds the vector database by loading documents from knowledge_base/,
        chunking them, computing embeddings, and storing them in ChromaDB.
        """
        existing = self.load_vector_database()
        if existing is not None and not force_rebuild:
            if hasattr(existing, "count") and existing.count() > 0:
                print(f"Vector database already exists with {existing.count()} chunks. Skipping rebuild.")
                return existing

        print("Building vector database from knowledge base documents...")
        loader = DocumentLoaderService()
        raw_docs = loader.load_documents()
        if not raw_docs:
            print("Warning: No documents found in knowledge base.")
            return None

        chunker = ChunkingService()
        chunks = chunker.split_documents(raw_docs)
        print(f"Loaded {len(raw_docs)} documents into {len(chunks)} chunks.")

        texts = [c.page_content for c in chunks]
        metadatas = [c.metadata for c in chunks]
        ids = [f"doc_{i}_{c.metadata.get('chunk_id', i)}" for i, c in enumerate(chunks)]

        embeddings = self.embedding_service.embed_documents(texts)

        client = self._get_client()
        if client is not None:
            # Delete old collection if forcing rebuild
            if force_rebuild:
                try:
                    client.delete_collection(name=self.collection_name)
                except Exception:
                    pass

            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            # ChromaDB supports batch adding
            batch_size = 50
            for i in range(0, len(chunks), batch_size):
                self._collection.add(
                    ids=ids[i:i+batch_size],
                    embeddings=embeddings[i:i+batch_size],
                    documents=texts[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size]
                )
            print(f"Successfully indexed {self._collection.count()} chunks into ChromaDB.")
            return self._collection
        else:
            # Fallback local vector store when chromadb is absent
            fallback_data = []
            for i, c in enumerate(chunks):
                fallback_data.append({
                    "id": ids[i],
                    "text": texts[i],
                    "metadata": metadatas[i],
                    "embedding": embeddings[i]
                })
            fallback_index = self.persist_directory / f"{self.collection_name}_fallback.json"
            with open(fallback_index, "w", encoding="utf-8") as f:
                json.dump(fallback_data, f, indent=2)
            print(f"Persisted fallback vector store with {len(fallback_data)} chunks.")
            return "fallback_loaded"

    def rebuild_knowledge_base(self):
        """Forces a clean rebuild of the vector database."""
        return self.build_vector_database(force_rebuild=True)

    def retrieve_documents(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves top-k most semantically relevant chunks for a given query.
        Returns a list of dictionaries with 'text', 'metadata', and 'score'.
        """
        collection = self.load_vector_database()
        if collection is None:
            # Auto-build on first retrieval if not yet built
            collection = self.build_vector_database(force_rebuild=False)

        query_vector = self.embedding_service.embed_query(query)
        client = self._get_client()

        if client is not None and self._collection is not None:
            results = self._collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            retrieved = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for doc_text, meta, dist in zip(docs, metas, distances):
                # Cosine distance to similarity: similarity = 1.0 - (distance / 2) or 1.0 - distance
                similarity = max(0.0, 1.0 - dist)
                retrieved.append({
                    "text": doc_text,
                    "metadata": meta,
                    "score": round(similarity, 4),
                    "source": meta.get("source", "unknown")
                })
            return retrieved
        else:
            # Fallback search using cosine similarity
            fallback_index = self.persist_directory / f"{self.collection_name}_fallback.json"
            if not fallback_index.exists():
                return []
            with open(fallback_index, "r", encoding="utf-8") as f:
                records = json.load(f)

            scored = []
            for r in records:
                sim = self._cosine_similarity(query_vector, r["embedding"])
                scored.append({
                    "text": r["text"],
                    "metadata": r["metadata"],
                    "score": round(sim, 4),
                    "source": r["metadata"].get("source", "unknown")
                })
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:top_k]

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm_a * norm_b)))


# Functional helpers required by specifications
_global_vector_store: Optional[VectorStoreService] = None

def get_vector_store() -> VectorStoreService:
    global _global_vector_store
    if _global_vector_store is None:
        _global_vector_store = VectorStoreService()
    return _global_vector_store

def build_vector_database():
    return get_vector_store().build_vector_database(force_rebuild=False)

def load_vector_database():
    return get_vector_store().load_vector_database()

def retrieve_documents(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    return get_vector_store().retrieve_documents(query=query, top_k=top_k)

def rebuild_knowledge_base():
    return get_vector_store().rebuild_knowledge_base()

#!/usr/bin/env python3
"""
Script to build / rebuild the ChromaDB vector database from knowledge base documents.
Usage:
    python scripts/build_knowledge_base.py [--force]
"""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import get_settings
from app.services.vector_store import get_vector_store

def main():
    parser = argparse.ArgumentParser(description="Build ChromaDB knowledge base index.")
    parser.add_argument("--force", action="store_true", help="Force rebuild even if index exists")
    args = parser.parse_args()

    settings = get_settings()
    print("=" * 60)
    print(f"Building Knowledge Base for {settings.APP_NAME}")
    print(f"Knowledge Base Directory: {settings.KNOWLEDGE_BASE_DIR}")
    print(f"Persist Directory: {settings.CHROMA_PERSIST_DIRECTORY}")
    print(f"Collection Name: {settings.CHROMA_COLLECTION_NAME}")
    print("=" * 60)

    vs = get_vector_store()
    if args.force:
        collection = vs.rebuild_knowledge_base()
    else:
        collection = vs.build_vector_database(force_rebuild=False)

    print("\nKnowledge Base build completed successfully!")
    if hasattr(collection, "count"):
        print(f"Total chunks indexed in ChromaDB: {collection.count()}")

if __name__ == "__main__":
    main()

import os
from pathlib import Path
from typing import List, Dict, Any
from app.config import get_settings

class Document:
    """Lightweight document representation preserving text and metadata."""
    def __init__(self, page_content: str, metadata: Dict[str, Any]):
        self.page_content = page_content
        self.metadata = metadata

    def __repr__(self):
        return f"<Document source='{self.metadata.get('source')}' chars={len(self.page_content)}>"


class DocumentLoaderService:
    """Service responsible for loading documentation from markdown and text files."""

    def __init__(self, knowledge_base_dir: str = None):
        self.knowledge_base_dir = Path(knowledge_base_dir or get_settings().KNOWLEDGE_BASE_DIR)

    def load_documents(self) -> List[Document]:
        """Loads all .md and .txt documents from the knowledge base directory."""
        if not self.knowledge_base_dir.exists():
            raise FileNotFoundError(f"Knowledge base directory does not exist: {self.knowledge_base_dir}")

        documents: List[Document] = []
        supported_extensions = (".md", ".txt", ".markdown")

        for file_path in sorted(self.knowledge_base_dir.glob("*")):
            if file_path.suffix.lower() in supported_extensions and file_path.is_file():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()

                    if not content:
                        continue

                    # Extract first heading as document title if present
                    title = file_path.stem.replace("_", " ").title()
                    for line in content.splitlines():
                        if line.startswith("# "):
                            title = line.replace("# ", "").strip()
                            break

                    metadata = {
                        "source": file_path.name,
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "title": title,
                        "file_extension": file_path.suffix.lower()
                    }

                    documents.append(Document(page_content=content, metadata=metadata))
                except Exception as e:
                    print(f"Error loading document {file_path.name}: {e}")

        return documents

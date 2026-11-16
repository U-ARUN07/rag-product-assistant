from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Base Directory of Project
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "Internship Application Agent - RAG Product Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Provider & Model Settings
    LLM_PROVIDER: str = Field(default="gemini", description="'gemini', 'openai', or 'mock'")
    LLM_MODEL: str = Field(default="gemini-1.5-flash", description="Model name for generative responses")
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API Key")
    GOOGLE_API_KEY: str = Field(default="", description="Alternative alias for Gemini API Key")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API Key if using OpenAI")

    # Embeddings
    EMBEDDING_MODEL_NAME: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace / SentenceTransformers model name"
    )

    # Chunking
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100

    # Vector Database (ChromaDB)
    CHROMA_PERSIST_DIRECTORY: str = str(BASE_DIR / "vector_store")
    CHROMA_COLLECTION_NAME: str = "internship_agent_knowledge"
    RETRIEVAL_TOP_K: int = 4
    SIMILARITY_SCORE_THRESHOLD: float = 0.15

    # Conversational Memory & Database
    SQLITE_DB_PATH: str = str(BASE_DIR / "app" / "database" / "conversations.db")
    MAX_HISTORY_MESSAGES: int = 6

    # Knowledge Base Path
    KNOWLEDGE_BASE_DIR: str = str(BASE_DIR / "knowledge_base")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def active_gemini_key(self) -> str:
        return self.GEMINI_API_KEY or self.GOOGLE_API_KEY


@lru_cache()
def get_settings() -> Settings:
    return Settings()

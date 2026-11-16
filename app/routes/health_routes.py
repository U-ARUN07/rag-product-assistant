from fastapi import APIRouter
from app.config import get_settings
from app.services.vector_store import get_vector_store

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    """Application health status endpoint."""
    settings = get_settings()
    vector_store = get_vector_store()
    db_loaded = vector_store.load_vector_database() is not None

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "vector_store_initialized": db_loaded,
        "llm_provider": settings.LLM_PROVIDER
    }

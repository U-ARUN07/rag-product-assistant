from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routes.chat_routes import router as chat_router
from app.routes.health_routes import router as health_router
from app.database.conversation_db import ConversationDB
from app.services.vector_store import get_vector_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database
    db = ConversationDB()
    db.init_db()

    # Pre-load or initialize vector store
    vs = get_vector_store()
    try:
        vs.load_vector_database()
    except Exception as e:
        print(f"Vector store deferred init: {e}")
    yield

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="RAG-Based Product Assistant Chatbot with Conversational Memory for Internship Application Agent",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(health_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Internship Application Agent - RAG Product Assistant API",
        "documentation": "/docs",
        "health": "/health",
        "chat_endpoint": "/api/v1/chat"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

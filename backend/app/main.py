import sys
from pathlib import Path

# Ensure backend directory is in sys.path so app modules are resolvable from any CWD
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router as api_router
from app.memory.long_term import warmup_embeddings

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rag_memory_agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler: warms up embedding model asynchronously on server startup."""
    logger.info("Initializing RAG Memory Agent backend...")
    # Warm up embeddings in a background thread so server starts instantaneously
    warmup_thread = threading.Thread(target=warmup_embeddings, daemon=True)
    warmup_thread.start()
    logger.info("Embedding warmup dispatched to background thread.")
    yield
    logger.info("Shutting down RAG Memory Agent backend.")


app = FastAPI(
    title="RAG Memory Agent API",
    description="Demo-ready personal research assistant with cross-session vector memory and tool calling.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "app": "RAG Memory Agent",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "provider": settings.llm_provider,
        "model": settings.llm_model,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )

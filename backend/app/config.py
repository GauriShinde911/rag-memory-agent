from pathlib import Path
from typing import Optional
import os

# Disable Chroma telemetry to avoid noisy network warnings
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory: backend/
BASE_DIR = Path(__file__).resolve().parent.parent
# Project root directory: rag-memory-agent/
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    """Application configuration loaded from environment or .env file."""
    # LLM Settings
    llm_provider: str = "gemini"  # "gemini" | "openai"
    llm_model: str = "gemini-2.5-flash"
    google_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Server Settings
    host: str = "127.0.0.1"
    port: int = 8000

    # Persistence
    persist_dir: str = str(PROJECT_ROOT / "data" / "chroma")
    collection_name: str = "assistant_memory"

    # Embedding Model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Safety & Tool Controls
    # Subprocess execution with 5s timeout; NOT a hardened sandbox
    enable_python_executor: bool = True

    # Evaluation Controls
    eval_pause_seconds: float = 1.0

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def is_llm_configured(self) -> bool:
        """Check if the active provider has an API key configured."""
        provider = self.llm_provider.lower().strip()
        if provider == "gemini":
            key = self.google_api_key or os.environ.get("GOOGLE_API_KEY")
            return bool(key and key.strip())
        elif provider == "openai":
            key = self.openai_api_key or os.environ.get("OPENAI_API_KEY")
            return bool(key and key.strip())
        return False


settings = Settings()

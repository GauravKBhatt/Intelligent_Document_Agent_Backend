# config/settings.py - Project settings
import os
from pydantic_settings import BaseSettings
from typing import ClassVar, Set

class Settings(BaseSettings):
    # Embedding and File Processing
    DEFAULT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    ALLOWED_EXTENSIONS: ClassVar[Set[str]] = {".pdf", ".txt"}
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    UPLOAD_DIR: str = "uploads"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Database Configuration
    VECTOR_DB: str = "qdrant"  # or pinecone, weaviate, milvus
    DATABASE_URL: str = "sqlite:///./test.db"

    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Email Configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.example.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", "user@example.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "password")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")

settings = Settings()
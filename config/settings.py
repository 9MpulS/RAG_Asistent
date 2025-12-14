"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "RAG Assistant для студентів СумДУ"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/rag_assistant"
    DB_ECHO: bool = False

    # Grok API (xAI)
    GROK_API_KEY: str
    GROK_MODEL: str = "grok-beta"
    GROK_BASE_URL: str = "https://api.x.ai/v1"
    GROK_TEMPERATURE: float = 0.7
    GROK_MAX_TOKENS: int = 2000

    # Cohere (для embeddings)
    COHERE_API_KEY: str
    EMBEDDING_MODEL: str = "embed-multilingual-v3.0"
    VECTOR_DIMENSIONS: int = 1024  # embed-multilingual-v3.0 має розмірність 1024

    # RAG Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".txt", ".html", ".docx"]

    # Crawl4AI Settings
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_MAX_RETRIES: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings

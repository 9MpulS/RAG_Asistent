"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from src.api.deps import get_db, get_settings
from src.models.schemas import HealthResponse, HealthDetailedResponse
from src.models.database import Document, Chunk
from config.settings import Settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Basic health check endpoint.

    Returns system status.
    """
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    # Check Grok API (простий тест наявності ключа)
    grok_status = "ok" if settings.GROK_API_KEY else "not configured"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        grok_api=grok_status
    )


@router.get("/health/detailed", response_model=HealthDetailedResponse)
def health_check_detailed(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Detailed health check endpoint.

    Returns detailed system status with statistics.
    """
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    # Check Grok API
    grok_status = "ok" if settings.GROK_API_KEY else "not configured"

    # Get statistics
    documents_count = db.scalar(select(func.count()).select_from(Document)) or 0
    chunks_count = db.scalar(select(func.count()).select_from(Chunk)) or 0

    from sqlalchemy import select
    return HealthDetailedResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        grok_api=grok_status,
        documents_count=documents_count,
        chunks_count=chunks_count,
        embedding_model=settings.EMBEDDING_MODEL
    )

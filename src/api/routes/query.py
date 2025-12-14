"""Query endpoints for RAG."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.deps import get_db
from src.models.schemas import QueryRequest, QueryResponse
from src.services.query_service import get_query_service

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Process user query through RAG pipeline.

    Args:
        request: Query request with user query
        db: Database session

    Returns:
        Query response with answer and sources
    """
    try:
        query_service = get_query_service(db)
        response = await query_service.process_query(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

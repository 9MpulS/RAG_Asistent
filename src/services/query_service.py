"""Query service for processing RAG queries."""

from sqlalchemy.orm import Session
from src.models.schemas import QueryRequest, QueryResponse
from src.rag.pipeline import get_rag_pipeline


class QueryService:
    """Service for processing user queries through RAG pipeline."""

    def __init__(self, db: Session):
        """
        Initialize query service.

        Args:
            db: Database session
        """
        self.db = db
        self.rag_pipeline = get_rag_pipeline(db)

    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """
        Process user query through RAG pipeline.

        Args:
            request: Query request with user query and parameters

        Returns:
            Query response with answer and sources
        """
        response = await self.rag_pipeline.process_query(
            query=request.query,
            top_k=request.top_k
        )

        return response


def get_query_service(db: Session) -> QueryService:
    """Get query service instance."""
    return QueryService(db)

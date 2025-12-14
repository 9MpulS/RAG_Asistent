"""Vector retrieval service using pgvector."""

from typing import List
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from src.models.database import Chunk
from src.embeddings.embedder import get_embedding_service
from config.settings import get_settings

settings = get_settings()


class VectorRetriever:
    """Service for retrieving relevant chunks using vector similarity."""

    def __init__(self, db: Session):
        """
        Initialize retriever.

        Args:
            db: Database session
        """
        self.db = db
        self.embedding_service = get_embedding_service()

    def search_by_text(
        self,
        query: str,
        top_k: int | None = None,
        similarity_threshold: float | None = None
    ) -> List[Chunk]:
        """
        Search for relevant chunks using text query.

        Args:
            query: Search query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of relevant chunks sorted by similarity
        """
        if top_k is None:
            top_k = settings.TOP_K
        if similarity_threshold is None:
            similarity_threshold = settings.SIMILARITY_THRESHOLD

        # Create query embedding (використовуємо input_type="search_query")
        query_embedding = self.embedding_service.create_query_embedding(query)

        return self.search_by_embedding(query_embedding, top_k, similarity_threshold)

    def search_by_embedding(
        self,
        query_embedding: List[float],
        top_k: int | None = None,
        similarity_threshold: float | None = None
    ) -> List[Chunk]:
        """
        Search for relevant chunks using embedding vector.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of relevant chunks sorted by similarity
        """
        if top_k is None:
            top_k = settings.TOP_K
        if similarity_threshold is None:
            similarity_threshold = settings.SIMILARITY_THRESHOLD

        # Convert embedding to string format for pgvector
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        # SQL query with vector similarity
        query = text("""
            SELECT
                c.id,
                c.document_id,
                c.content,
                c.chunk_index,
                c.article_number,
                c.metadata,
                c.created_at,
                1 - (c.embedding <=> :query_embedding::vector) AS similarity
            FROM chunks c
            WHERE c.embedding IS NOT NULL
            AND (1 - (c.embedding <=> :query_embedding::vector)) >= :threshold
            ORDER BY c.embedding <=> :query_embedding::vector
            LIMIT :top_k
        """)

        # Execute query
        result = self.db.execute(
            query,
            {
                "query_embedding": embedding_str,
                "threshold": similarity_threshold,
                "top_k": top_k
            }
        )

        # Fetch chunks
        rows = result.fetchall()

        # Convert to Chunk objects
        chunks = []
        for row in rows:
            chunk = self.db.query(Chunk).filter(Chunk.id == row[0]).first()
            if chunk:
                chunks.append(chunk)

        return chunks


def get_retriever(db: Session) -> VectorRetriever:
    """Get vector retriever instance."""
    return VectorRetriever(db)

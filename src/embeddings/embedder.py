"""Embeddings generation service."""

from typing import List
import cohere
from config.settings import get_settings

settings = get_settings()


class EmbeddingService:
    """Service for creating text embeddings using Cohere API."""

    def __init__(self):
        """Initialize Cohere client."""
        self.client = cohere.Client(api_key=settings.COHERE_API_KEY)
        self.model = settings.EMBEDDING_MODEL

    def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        response = self.client.embed(
            texts=[text.strip()],
            model=self.model,
            input_type="search_document"  # для документів
        )
        return response.embeddings[0]

    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts in a batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts
        valid_texts = [t.strip() for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("All texts are empty")

        response = self.client.embed(
            texts=valid_texts,
            model=self.model,
            input_type="search_document"  # для документів
        )

        return response.embeddings

    def create_query_embedding(self, query: str) -> List[float]:
        """
        Create embedding for search query.

        Args:
            query: Query text

        Returns:
            List of floats representing the embedding vector
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        response = self.client.embed(
            texts=[query.strip()],
            model=self.model,
            input_type="search_query"  # для запитів
        )
        return response.embeddings[0]


# Global instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

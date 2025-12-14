"""RAG Pipeline orchestrator."""

from typing import List
from sqlalchemy.orm import Session
from src.models.schemas import QueryResponse, Source
from src.models.database import Chunk
from src.rag.retriever import get_retriever
from src.rag.generator import get_generator
from src.sgr.reasoner import get_sgr_reasoner
from src.utils.text_utils import truncate_text


class RAGPipeline:
    """Orchestrator for the full RAG process."""

    def __init__(self, db: Session):
        """
        Initialize RAG pipeline.

        Args:
            db: Database session
        """
        self.db = db
        self.retriever = get_retriever(db)
        self.generator = get_generator()
        self.reasoner = get_sgr_reasoner()

    async def process_query(self, query: str, top_k: int = 5) -> QueryResponse:
        """
        Process user query through full RAG pipeline.

        Steps:
        1. SGR: Understand query
        2. Retrieval: Find relevant chunks
        3. SGR: Structure context
        4. Generation: Create answer
        5. Format sources

        Args:
            query: User query
            top_k: Number of chunks to retrieve

        Returns:
            QueryResponse with answer and sources
        """
        # Step 1: SGR - Understand query
        query_understanding = await self.reasoner.understand_query(query)

        # Step 2: Retrieval - Find relevant chunks
        chunks = self.retriever.search_by_text(query, top_k=top_k)

        if not chunks:
            return QueryResponse(
                answer="На жаль, я не знайшов релевантної інформації в документах.",
                sources=[],
                reasoning_path="Не знайдено релевантних документів"
            )

        # Step 3: SGR - Structure context
        context_structure = self.reasoner.structure_context(chunks, query_understanding)

        # Step 4: Generation - Create answer using Grok
        answer = self.generator.generate_answer(query, chunks)

        # Step 5: Format sources
        sources = self._format_sources(chunks)

        return QueryResponse(
            answer=answer,
            sources=sources,
            reasoning_path=context_structure.reasoning_path
        )

    def _format_sources(self, chunks: List[Chunk]) -> List[Source]:
        """
        Format chunks into citation sources.

        Args:
            chunks: List of chunks

        Returns:
            List of formatted sources
        """
        sources = []
        for chunk in chunks:
            if chunk.document:
                source = Source(
                    document_title=chunk.document.title,
                    document_number=chunk.document.document_number,
                    article=chunk.article_number,
                    excerpt=truncate_text(chunk.content, max_length=200)
                )
                sources.append(source)

        return sources


def get_rag_pipeline(db: Session) -> RAGPipeline:
    """Get RAG pipeline instance."""
    return RAGPipeline(db)

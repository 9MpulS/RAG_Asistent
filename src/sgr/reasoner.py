"""Schema-Guided Reasoning logic using Pydantic AI."""

from typing import List
from pydantic_ai import Agent
from src.sgr.schemas import QueryUnderstanding, ContextStructure
from src.models.database import Chunk
from config.settings import get_settings

settings = get_settings()


class SGRReasoner:
    """Schema-Guided Reasoning engine using Pydantic AI."""

    def __init__(self):
        """Initialize SGR reasoner with Grok model."""
        # Agent for query understanding
        self.query_agent = Agent(
            model=f"openai:{settings.GROK_MODEL}",
            result_type=QueryUnderstanding,
            system_prompt=(
                "Ти - експерт з аналізу запитів студентів університету. "
                "Твоя задача - зрозуміти намір користувача та виділити ключові терміни. "
                "Визнач тип документа, який може містити відповідь (положення, наказ, інструкція). "
                "Відповідай українською мовою."
            )
        )

    async def understand_query(self, query: str) -> QueryUnderstanding:
        """
        Analyze and understand user query using SGR.

        Args:
            query: User query text

        Returns:
            QueryUnderstanding with intent, key terms, and document type
        """
        result = await self.query_agent.run(
            f"Проаналізуй запит студента: '{query}'"
        )
        return result.data

    def structure_context(
        self,
        chunks: List[Chunk],
        query_understanding: QueryUnderstanding
    ) -> ContextStructure:
        """
        Structure retrieved chunks based on query understanding.

        Args:
            chunks: Retrieved chunks from vector search
            query_understanding: Understanding of the query

        Returns:
            ContextStructure with ranked chunks and reasoning path
        """
        # Simple heuristic-based ranking for MVP
        # В більш складній версії можна використати ще один Agent

        from src.sgr.schemas import ChunkRelevance

        chunk_relevances = []
        for i, chunk in enumerate(chunks):
            # Проста евристика: чи містить чанк ключові терміни
            relevance = 0.5  # базова релевантність
            content_lower = chunk.content.lower()

            # Підвищуємо релевантність якщо є ключові терміни
            for term in query_understanding.key_terms:
                if term.lower() in content_lower:
                    relevance += 0.1

            # Обмежуємо до 1.0
            relevance = min(1.0, relevance)

            chunk_relevances.append(
                ChunkRelevance(
                    chunk_id=chunk.id,
                    relevance_score=relevance,
                    reasoning=f"Чанк містить релевантну інформацію для запиту"
                )
            )

        # Сортуємо за релевантністю
        chunk_relevances.sort(key=lambda x: x.relevance_score, reverse=True)

        # Формуємо reasoning path
        reasoning_path = (
            f"На основі розуміння запиту (намір: {query_understanding.intent}) "
            f"та ключових термінів {query_understanding.key_terms}, "
            f"відібрано {len(chunk_relevances)} релевантних фрагментів документів."
        )

        return ContextStructure(
            relevant_chunks=chunk_relevances,
            reasoning_path=reasoning_path,
            confidence=query_understanding.confidence
        )


# Global instance
_sgr_reasoner: SGRReasoner | None = None


def get_sgr_reasoner() -> SGRReasoner:
    """Get global SGR reasoner instance."""
    global _sgr_reasoner
    if _sgr_reasoner is None:
        _sgr_reasoner = SGRReasoner()
    return _sgr_reasoner

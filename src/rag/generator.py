"""Answer generation service using Grok LLM."""

from typing import List
from pydantic_ai import Agent
from openai import OpenAI
from src.models.database import Chunk
from config.settings import get_settings

settings = get_settings()


class AnswerGenerator:
    """Service for generating answers using Grok LLM."""

    def __init__(self):
        """Initialize generator with Grok client."""
        # Використовуємо OpenAI-сумісний API для Grok
        self.client = OpenAI(
            api_key=settings.GROK_API_KEY,
            base_url=settings.GROK_BASE_URL
        )
        self.model = settings.GROK_MODEL

    def create_prompt(self, query: str, chunks: List[Chunk]) -> str:
        """
        Create prompt for LLM with context from chunks.

        Args:
            query: User query
            chunks: Retrieved relevant chunks

        Returns:
            Formatted prompt
        """
        # Формуємо контекст з чанків
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            doc_title = chunk.document.title if chunk.document else "Невідомий документ"
            doc_number = chunk.document.document_number or "б/н"
            article = chunk.article_number or ""

            context_parts.append(
                f"[Джерело {i}: '{doc_title}' №{doc_number} {article}]\n"
                f"{chunk.content}\n"
            )

        context = "\n".join(context_parts)

        prompt = f"""Ти - асистент для студентів Сумського державного університету.
Твоя задача - відповідати на запитання студентів на основі нормативних документів університету.

КОНТЕКСТ З ДОКУМЕНТІВ:
{context}

ЗАПИТ СТУДЕНТА:
{query}

ІНСТРУКЦІЇ:
1. Відповідай чітко та по суті, використовуючи ТІЛЬКИ інформацію з наданого контексту
2. Якщо в контексті немає відповіді на запитання, чесно скажи про це
3. Обов'язково вказуй джерела у форматі: "Джерело 1 'Назва документа' ст. X"
4. Відповідай українською мовою
5. Будь ввічливим та професійним

ВІДПОВІДЬ:"""

        return prompt

    def generate_answer(self, query: str, chunks: List[Chunk]) -> str:
        """
        Generate answer using Grok LLM.

        Args:
            query: User query
            chunks: Retrieved relevant chunks

        Returns:
            Generated answer
        """
        if not chunks:
            return "На жаль, я не знайшов релевантної інформації в документах для відповіді на ваш запит."

        prompt = self.create_prompt(query, chunks)

        # Call Grok API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=settings.GROK_TEMPERATURE,
            max_tokens=settings.GROK_MAX_TOKENS
        )

        answer = response.choices[0].message.content.strip()
        return answer


# Global instance
_generator: AnswerGenerator | None = None


def get_generator() -> AnswerGenerator:
    """Get global answer generator instance."""
    global _generator
    if _generator is None:
        _generator = AnswerGenerator()
    return _generator

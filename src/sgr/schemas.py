"""Pydantic schemas for Schema-Guided Reasoning (SGR)."""

from typing import List, Optional
from pydantic import BaseModel, Field


class QueryUnderstanding(BaseModel):
    """Schema for understanding user query intent."""

    intent: str = Field(..., description="Намір користувача (питання, пошук процедури, тощо)")
    key_terms: List[str] = Field(
        default_factory=list,
        description="Ключові терміни з запиту"
    )
    expected_document_type: Optional[str] = Field(
        None,
        description="Очікуваний тип документа (положення, наказ, інструкція)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Впевненість в розумінні запиту"
    )


class ChunkRelevance(BaseModel):
    """Relevance score for a retrieved chunk."""

    chunk_id: int = Field(..., description="ID чанку")
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Оцінка релевантності"
    )
    reasoning: str = Field(..., description="Пояснення релевантності")


class ContextStructure(BaseModel):
    """Schema for structuring retrieved context."""

    relevant_chunks: List[ChunkRelevance] = Field(
        default_factory=list,
        description="Відсортовані за релевантністю чанки"
    )
    reasoning_path: str = Field(
        ...,
        description="Шлях міркувань для побудови відповіді"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Загальна впевненість в контексті"
    )


class AnswerStructure(BaseModel):
    """Schema for structured answer generation."""

    answer_text: str = Field(..., description="Текст відповіді")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Впевненість у відповіді"
    )
    sources_used: List[int] = Field(
        default_factory=list,
        description="ID чанків, використаних для відповіді"
    )
    reasoning: str = Field(
        ...,
        description="Пояснення логіки побудови відповіді"
    )

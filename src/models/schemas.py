"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, field_validator


# ===== Query Schemas =====

class QueryRequest(BaseModel):
    """Request schema for RAG query."""
    query: str = Field(..., min_length=3, max_length=1000, description="Запит користувача")
    top_k: int = Field(5, ge=1, le=20, description="Кількість результатів для пошуку")


class Source(BaseModel):
    """Source citation schema."""
    document_title: str = Field(..., description="Назва документа")
    document_number: Optional[str] = Field(None, description="Номер документа")
    article: Optional[str] = Field(None, description="Номер статті")
    excerpt: str = Field(..., description="Витяг з тексту")


class QueryResponse(BaseModel):
    """Response schema for RAG query."""
    answer: str = Field(..., description="Згенерована відповідь")
    sources: List[Source] = Field(default_factory=list, description="Джерела для відповіді")
    reasoning_path: Optional[str] = Field(None, description="SGR шлях міркувань")


# ===== Document Schemas =====

class DocumentBase(BaseModel):
    """Base document schema."""
    title: str = Field(..., min_length=3, max_length=500)
    document_number: Optional[str] = Field(None, max_length=50)


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    url: Optional[str] = Field(None, description="URL для парсингу")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('URL повинен починатися з http:// або https://')
        return v


class DocumentUpdate(BaseModel):
    """Schema for updating document metadata."""
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    document_number: Optional[str] = Field(None, max_length=50)


class DocumentResponse(DocumentBase):
    """Response schema for document."""
    id: int
    url: Optional[str] = None
    file_path: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    chunks_count: int = Field(0, description="Кількість чанків в документі")

    model_config = {"from_attributes": True}


class DocumentDetail(DocumentResponse):
    """Detailed document response with chunks preview."""
    chunks_preview: List[str] = Field(
        default_factory=list,
        description="Перші 3 чанки для попереднього перегляду"
    )


class DocumentList(BaseModel):
    """Paginated list of documents."""
    items: List[DocumentResponse]
    total: int
    skip: int
    limit: int


# ===== Chunk Schemas =====

class ChunkResponse(BaseModel):
    """Response schema for chunk."""
    id: int
    document_id: int
    content: str
    chunk_index: int
    article_number: Optional[str] = None

    model_config = {"from_attributes": True}


# ===== Health Schemas =====

class HealthResponse(BaseModel):
    """Basic health check response."""
    status: str = Field(..., description="Статус системи")
    database: str = Field(..., description="Статус підключення до БД")
    grok_api: str = Field(..., description="Статус Grok API")


class HealthDetailedResponse(HealthResponse):
    """Detailed health check response."""
    documents_count: int = Field(..., description="Кількість документів в БД")
    chunks_count: int = Field(..., description="Кількість чанків в БД")
    embedding_model: str = Field(..., description="Назва embedding моделі")


# ===== Common Response Schemas =====

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: Optional[str] = None


class DeleteResponse(BaseModel):
    """Response for delete operations."""
    status: str = Field("deleted", description="Статус операції")
    deleted_chunks: int = Field(0, description="Кількість видалених чанків")

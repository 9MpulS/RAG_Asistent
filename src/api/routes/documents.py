"""Document CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.api.deps import get_db
from src.models.schemas import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentDetail,
    DocumentList,
    MessageResponse,
    DeleteResponse
)
from src.services.document_service import get_document_service
from src.models.database import Chunk
from typing import Optional

router = APIRouter()


@router.get("/documents", response_model=DocumentList)
def list_documents(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    List all documents with pagination.

    Args:
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        db: Database session

    Returns:
        Paginated list of documents
    """
    doc_service = get_document_service(db)
    documents, total = doc_service.list_documents(skip=skip, limit=limit)

    # Add chunks count for each document
    items = []
    for doc in documents:
        chunks_count = db.query(func.count(Chunk.id)).filter(
            Chunk.document_id == doc.id
        ).scalar() or 0

        doc_response = DocumentResponse(
            id=doc.id,
            title=doc.title,
            document_number=doc.document_number,
            url=doc.url,
            file_path=doc.file_path,
            status=doc.status.value,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            chunks_count=chunks_count
        )
        items.append(doc_response)

    return DocumentList(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Get document details by ID.

    Args:
        document_id: Document ID
        db: Database session

    Returns:
        Document details with chunks preview
    """
    doc_service = get_document_service(db)
    document = doc_service.get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get chunks count and preview
    chunks = db.query(Chunk).filter(
        Chunk.document_id == document_id
    ).order_by(Chunk.chunk_index).limit(3).all()

    chunks_count = db.query(func.count(Chunk.id)).filter(
        Chunk.document_id == document_id
    ).scalar() or 0

    chunks_preview = [chunk.content[:200] + "..." for chunk in chunks]

    return DocumentDetail(
        id=document.id,
        title=document.title,
        document_number=document.document_number,
        url=document.url,
        file_path=document.file_path,
        status=document.status.value,
        created_at=document.created_at,
        updated_at=document.updated_at,
        chunks_count=chunks_count,
        chunks_preview=chunks_preview
    )


@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def create_document(
    url: Optional[str] = Form(None),
    title: str = Form(...),
    document_number: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Create a new document from URL or file upload.

    Args:
        url: URL to crawl (if provided)
        title: Document title
        document_number: Optional document number
        file: Uploaded file (if provided)
        db: Database session

    Returns:
        Created document
    """
    doc_service = get_document_service(db)

    try:
        if url:
            # Create from URL
            document = await doc_service.create_from_url(url=url, title=title)
        elif file:
            # Create from file
            document = await doc_service.create_from_file(
                file=file,
                title=title,
                document_number=document_number
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'url' or 'file' must be provided"
            )

        return DocumentResponse(
            id=document.id,
            title=document.title,
            document_number=document.document_number,
            url=document.url,
            file_path=document.file_path,
            status=document.status.value,
            created_at=document.created_at,
            updated_at=document.updated_at,
            chunks_count=0  # Processing, chunks will be added
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.put("/documents/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update document metadata.

    Args:
        document_id: Document ID
        update_data: Updated fields
        db: Database session

    Returns:
        Updated document
    """
    doc_service = get_document_service(db)
    document = doc_service.update_document(document_id, update_data)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks_count = db.query(func.count(Chunk.id)).filter(
        Chunk.document_id == document.id
    ).scalar() or 0

    return DocumentResponse(
        id=document.id,
        title=document.title,
        document_number=document.document_number,
        url=document.url,
        file_path=document.file_path,
        status=document.status.value,
        created_at=document.created_at,
        updated_at=document.updated_at,
        chunks_count=chunks_count
    )


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete document and all its chunks.

    Args:
        document_id: Document ID
        db: Database session

    Returns:
        Deletion status
    """
    doc_service = get_document_service(db)
    success, chunks_count = doc_service.delete_document(document_id)

    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return DeleteResponse(
        status="deleted",
        deleted_chunks=chunks_count
    )


@router.post("/documents/{document_id}/reprocess", response_model=MessageResponse)
async def reprocess_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Reprocess document: regenerate chunks and embeddings.

    Args:
        document_id: Document ID
        db: Database session

    Returns:
        Processing status message
    """
    doc_service = get_document_service(db)

    try:
        document = await doc_service.reprocess_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return MessageResponse(
            message="Document reprocessing started",
            detail=f"Document '{document.title}' is being reprocessed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reprocess document: {str(e)}"
        )

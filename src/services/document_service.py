"""Document service for CRUD operations."""

from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.models.database import Document, Chunk, DocumentStatus
from src.models.schemas import DocumentCreate, DocumentUpdate, DocumentResponse
from src.services.crawler_service import get_crawler_service
from src.utils.text_utils import chunk_text, extract_article_number
from src.embeddings.embedder import get_embedding_service
import pypdf
import os


class DocumentService:
    """Service for managing documents."""

    def __init__(self, db: Session):
        """
        Initialize document service.

        Args:
            db: Database session
        """
        self.db = db
        self.crawler = get_crawler_service()
        self.embedding_service = get_embedding_service()

    async def create_from_url(self, url: str, title: str) -> Document:
        """
        Create document by crawling URL.

        Args:
            url: URL to crawl
            title: Document title

        Returns:
            Created document
        """
        # Create document record
        document = Document(
            title=title,
            url=url,
            status=DocumentStatus.PROCESSING
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        try:
            # Crawl URL
            crawled_data = await self.crawler.crawl_url(url)

            # Update metadata
            if 'document_number' in crawled_data['metadata']:
                document.document_number = crawled_data['metadata']['document_number']

            # Process content
            await self._process_document_content(document, crawled_data['content'])

            # Mark as completed
            document.status = DocumentStatus.COMPLETED
            self.db.commit()

        except Exception as e:
            document.status = DocumentStatus.FAILED
            self.db.commit()
            raise Exception(f"Failed to process document: {str(e)}")

        return document

    async def create_from_file(
        self,
        file: UploadFile,
        title: str,
        document_number: Optional[str] = None
    ) -> Document:
        """
        Create document from uploaded file.

        Args:
            file: Uploaded file
            title: Document title
            document_number: Optional document number

        Returns:
            Created document
        """
        # Save file
        file_path = f"data/documents/{file.filename}"
        os.makedirs("data/documents", exist_ok=True)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Create document record
        document = Document(
            title=title,
            document_number=document_number,
            file_path=file_path,
            status=DocumentStatus.PROCESSING
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        try:
            # Extract text from file
            if file.filename.endswith('.pdf'):
                text = self._extract_text_from_pdf(file_path)
            elif file.filename.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                raise ValueError(f"Unsupported file type: {file.filename}")

            # Process content
            await self._process_document_content(document, text)

            # Mark as completed
            document.status = DocumentStatus.COMPLETED
            self.db.commit()

        except Exception as e:
            document.status = DocumentStatus.FAILED
            self.db.commit()
            raise Exception(f"Failed to process document: {str(e)}")

        return document

    async def _process_document_content(self, document: Document, content: str) -> None:
        """
        Process document content: chunk and create embeddings.

        Args:
            document: Document instance
            content: Document text content
        """
        # Split into chunks
        text_chunks = chunk_text(content)

        # Create chunks with embeddings
        chunks_data = []
        for i, chunk_content in enumerate(text_chunks):
            # Extract article number if present
            article = extract_article_number(chunk_content)

            # Create embedding
            embedding = self.embedding_service.create_embedding(chunk_content)

            chunk = Chunk(
                document_id=document.id,
                content=chunk_content,
                chunk_index=i,
                article_number=article,
                embedding=embedding
            )
            chunks_data.append(chunk)

        # Bulk insert chunks
        self.db.bulk_save_objects(chunks_data)
        self.db.commit()

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text

    def get_document(self, document_id: int) -> Optional[Document]:
        """Get document by ID."""
        return self.db.query(Document).filter(Document.id == document_id).first()

    def list_documents(self, skip: int = 0, limit: int = 20) -> tuple[List[Document], int]:
        """
        List documents with pagination.

        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            Tuple of (documents list, total count)
        """
        query = select(Document).order_by(Document.created_at.desc())
        total = self.db.scalar(select(func.count()).select_from(Document))

        documents = self.db.execute(
            query.offset(skip).limit(limit)
        ).scalars().all()

        return list(documents), total or 0

    def update_document(
        self,
        document_id: int,
        update_data: DocumentUpdate
    ) -> Optional[Document]:
        """Update document metadata."""
        document = self.get_document(document_id)
        if not document:
            return None

        if update_data.title is not None:
            document.title = update_data.title
        if update_data.document_number is not None:
            document.document_number = update_data.document_number

        self.db.commit()
        self.db.refresh(document)
        return document

    def delete_document(self, document_id: int) -> tuple[bool, int]:
        """
        Delete document and all its chunks.

        Returns:
            Tuple of (success, number of deleted chunks)
        """
        document = self.get_document(document_id)
        if not document:
            return False, 0

        # Count chunks before deletion
        chunks_count = self.db.query(Chunk).filter(Chunk.document_id == document_id).count()

        # Delete document (chunks will be deleted by cascade)
        self.db.delete(document)
        self.db.commit()

        return True, chunks_count

    async def reprocess_document(self, document_id: int) -> Optional[Document]:
        """Reprocess document: regenerate chunks and embeddings."""
        document = self.get_document(document_id)
        if not document:
            return None

        # Delete existing chunks
        self.db.query(Chunk).filter(Chunk.document_id == document_id).delete()
        self.db.commit()

        # Mark as processing
        document.status = DocumentStatus.PROCESSING
        self.db.commit()

        try:
            if document.url:
                # Re-crawl URL
                crawled_data = await self.crawler.crawl_url(document.url)
                content = crawled_data['content']
            elif document.file_path:
                # Re-read file
                if document.file_path.endswith('.pdf'):
                    content = self._extract_text_from_pdf(document.file_path)
                else:
                    with open(document.file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
            else:
                raise ValueError("Document has no URL or file path")

            # Reprocess content
            await self._process_document_content(document, content)

            # Mark as completed
            document.status = DocumentStatus.COMPLETED
            self.db.commit()

        except Exception as e:
            document.status = DocumentStatus.FAILED
            self.db.commit()
            raise Exception(f"Failed to reprocess document: {str(e)}")

        return document


def get_document_service(db: Session) -> DocumentService:
    """Get document service instance."""
    return DocumentService(db)

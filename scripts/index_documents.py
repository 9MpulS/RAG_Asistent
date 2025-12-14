"""Script to index all documents from data/documents folder."""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.db.session import SessionLocal
from src.services.document_service import get_document_service
from config.settings import get_settings

settings = get_settings()


async def index_all_documents():
    """Index all PDF and TXT documents from data/documents folder."""

    documents_folder = project_root / "data" / "documents"

    if not documents_folder.exists():
        print(f"[ERROR] Folder {documents_folder} does not exist!")
        return

    # Find all supported files
    pdf_files = list(documents_folder.glob("*.pdf"))
    txt_files = list(documents_folder.glob("*.txt"))
    all_files = pdf_files + txt_files

    # Filter out .gitkeep
    all_files = [f for f in all_files if f.name != ".gitkeep"]

    if not all_files:
        print("[INFO] No documents found in data/documents/")
        print(f"[INFO] Please add PDF or TXT files to: {documents_folder}")
        return

    print("=" * 60)
    print("DOCUMENT INDEXING")
    print("=" * 60)
    print(f"\nFound {len(all_files)} documents:")
    for i, file in enumerate(all_files, 1):
        print(f"  {i}. {file.name}")

    print(f"\nDatabase: {settings.DATABASE_URL}")
    print(f"Embedding model: {settings.EMBEDDING_MODEL}")
    print()

    # Process each file
    db = SessionLocal()
    doc_service = get_document_service(db)

    successful = 0
    failed = 0

    for i, file_path in enumerate(all_files, 1):
        print(f"\n[{i}/{len(all_files)}] Processing: {file_path.name}")
        print("-" * 60)

        try:
            # Create mock UploadFile
            from fastapi import UploadFile
            from io import BytesIO

            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Create UploadFile object
            upload_file = UploadFile(
                filename=file_path.name,
                file=BytesIO(file_content)
            )

            # Extract title from filename (remove extension)
            title = file_path.stem

            # Process document
            print(f"  - Creating document record...")
            document = await doc_service.create_from_file(
                file=upload_file,
                title=title,
                document_number=None  # Can be extracted from filename if needed
            )

            print(f"  [OK] Document created: ID={document.id}")
            print(f"  [OK] Title: {document.title}")
            print(f"  [OK] Status: {document.status.value}")

            successful += 1

        except Exception as e:
            print(f"  [ERROR] Failed to process {file_path.name}: {e}")
            failed += 1

    db.close()

    # Summary
    print("\n" + "=" * 60)
    print("INDEXING SUMMARY")
    print("=" * 60)
    print(f"Total files: {len(all_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print()

    if successful > 0:
        print("[OK] Indexing completed!")
        print("\nYou can now query the documents using:")
        print("  curl -X POST http://localhost:8000/api/query \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{\"query\": \"your question here\"}'")


async def reindex_all_documents():
    """Reprocess all existing documents in the database."""

    print("=" * 60)
    print("DOCUMENT REINDEXING")
    print("=" * 60)
    print("\n[WARNING] This will reprocess ALL documents in the database!")
    print("[WARNING] Chunks and embeddings will be regenerated.\n")

    response = input("Continue? (yes/NO): ")

    if response.lower() != 'yes':
        print("[X] Reindexing cancelled")
        return

    db = SessionLocal()
    doc_service = get_document_service(db)

    # Get all documents
    documents, total = doc_service.list_documents(skip=0, limit=1000)

    if total == 0:
        print("[INFO] No documents found in database")
        db.close()
        return

    print(f"\nFound {total} documents in database")
    print()

    successful = 0
    failed = 0

    for i, doc in enumerate(documents, 1):
        print(f"\n[{i}/{total}] Reprocessing: {doc.title}")
        print("-" * 60)

        try:
            document = await doc_service.reprocess_document(doc.id)
            print(f"  [OK] Document reprocessed: ID={document.id}")
            print(f"  [OK] Status: {document.status.value}")
            successful += 1

        except Exception as e:
            print(f"  [ERROR] Failed to reprocess document {doc.id}: {e}")
            failed += 1

    db.close()

    # Summary
    print("\n" + "=" * 60)
    print("REINDEXING SUMMARY")
    print("=" * 60)
    print(f"Total documents: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print("\n[OK] Reindexing completed!")


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Index documents from data/documents folder")
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Reprocess all existing documents in the database"
    )

    args = parser.parse_args()

    if args.reindex:
        asyncio.run(reindex_all_documents())
    else:
        asyncio.run(index_all_documents())


if __name__ == "__main__":
    main()

"""Script to initialize the database with tables and pgvector extension."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.db.session import init_db, drop_all_tables
from config.settings import get_settings

settings = get_settings()


def main(auto_confirm=False):
    """Initialize database."""
    print("=" * 60)
    print("DATABASE INITIALIZATION")
    print("=" * 60)
    print(f"\nDatabase URL: {settings.DATABASE_URL}\n")

    # Ask for confirmation
    if not auto_confirm:
        response = input("Initialize database? This will create tables and enable pgvector. (y/n): ")
        if response.lower() != 'y':
            print("[X] Initialization cancelled")
            return
    else:
        print("Auto-confirming initialization...")

    try:
        # Initialize database
        init_db()
        print("\n[OK] Database initialization completed successfully!")
        print("\nCreated tables:")
        print("  - documents")
        print("  - chunks")
        print("\nEnabled extensions:")
        print("  - pgvector")

    except Exception as e:
        print(f"\n[ERROR] Error during initialization: {e}")
        sys.exit(1)


def drop_database():
    """Drop all database tables (DANGER!)."""
    print("=" * 60)
    print("[WARNING] DROP ALL TABLES")
    print("=" * 60)
    print("\n[WARNING] This will delete ALL data!\n")

    response = input("Are you sure you want to drop all tables? (yes/NO): ")

    if response.lower() != 'yes':
        print("[X] Drop cancelled")
        return

    try:
        drop_all_tables()
        print("\n[OK] All tables dropped successfully!")

    except Exception as e:
        print(f"\n[ERROR] Error during drop: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop all tables (DANGER!)"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Auto-confirm initialization without prompting"
    )

    args = parser.parse_args()

    if args.drop:
        drop_database()
    else:
        main(auto_confirm=args.yes)

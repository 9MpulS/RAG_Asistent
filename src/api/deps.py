"""FastAPI dependencies."""

from typing import Generator
from sqlalchemy.orm import Session
from src.db.session import get_db
from config.settings import Settings, get_settings

# Export get_db dependency
__all__ = ["get_db", "get_settings"]

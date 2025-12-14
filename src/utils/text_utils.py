"""Text processing utilities."""

import re
from typing import List, Optional
import tiktoken
from config.settings import get_settings

settings = get_settings()


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens in
        model: Model name for tokenizer

    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None
) -> List[str]:
    """
    Split text into chunks with overlap.

    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk in tokens
        chunk_overlap: Number of tokens to overlap between chunks

    Returns:
        List of text chunks
    """
    if chunk_size is None:
        chunk_size = settings.CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = settings.CHUNK_OVERLAP

    # Clean text
    text = clean_text(text)

    # Split into sentences (простий підхід)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)

        if current_tokens + sentence_tokens > chunk_size and current_chunk:
            # Save current chunk
            chunks.append(' '.join(current_chunk))

            # Start new chunk with overlap
            overlap_text = ' '.join(current_chunk)
            overlap_tokens = count_tokens(overlap_text)

            while overlap_tokens > chunk_overlap and len(current_chunk) > 1:
                current_chunk.pop(0)
                overlap_text = ' '.join(current_chunk)
                overlap_tokens = count_tokens(overlap_text)

            current_tokens = overlap_tokens

        current_chunk.append(sentence)
        current_tokens += sentence_tokens

    # Add last chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def clean_text(text: str) -> str:
    """
    Clean and normalize text.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters but keep Ukrainian letters
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\"\'«»]', '', text)

    # Strip
    text = text.strip()

    return text


def extract_article_number(text: str) -> Optional[str]:
    """
    Extract article number from text.

    Args:
        text: Text to search in

    Returns:
        Article number if found, None otherwise
    """
    # Patterns для пошуку статей
    patterns = [
        r'(?:ст\.|стаття)\s*(\d+)',
        r'(?:п\.|пункт)\s*(\d+)',
        r'(?:розділ)\s*(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)

    return None


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text to maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - 3] + "..."

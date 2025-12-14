"""Web crawler service using Crawl4AI for parsing normative.sumdu.edu.ua."""

from typing import Dict, Optional
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from bs4 import BeautifulSoup
from config.settings import get_settings

settings = get_settings()


class CrawlerService:
    """Service for crawling documents from normative.sumdu.edu.ua using Crawl4AI."""

    def __init__(self):
        """Initialize crawler service."""
        self.timeout = settings.CRAWLER_TIMEOUT
        self.max_retries = settings.CRAWLER_MAX_RETRIES

    async def crawl_url(self, url: str) -> Dict[str, any]:
        """
        Crawl URL and extract content using Crawl4AI.

        Args:
            url: URL to crawl

        Returns:
            Dictionary with content, title, and metadata

        Raises:
            Exception: If crawling fails
        """
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=url,
                bypass_cache=True,
                word_count_threshold=10,
                remove_overlay_elements=True,
            )

            if not result.success:
                raise Exception(f"Failed to crawl URL: {url}. Error: {result.error_message}")

            # Extract content
            content = result.markdown or result.cleaned_html or result.html

            # Extract metadata
            metadata = self.extract_metadata(result.html)

            # Clean content
            cleaned_content = self.clean_html_content(content)

            return {
                "content": cleaned_content,
                "title": metadata.get("title", "Untitled Document"),
                "metadata": metadata,
                "url": url
            }

    def extract_metadata(self, html_content: str) -> Dict[str, any]:
        """
        Extract metadata from HTML content.

        Args:
            html_content: Raw HTML content

        Returns:
            Dictionary with metadata
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        metadata = {}

        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()

        # Extract document number (patterns for normative.sumdu.edu.ua)
        # Example: searching for "№ 2133" or similar patterns
        text = soup.get_text()

        import re
        doc_number_match = re.search(r'№\s*(\d+)', text)
        if doc_number_match:
            metadata['document_number'] = doc_number_match.group(1)

        # Extract date if present
        date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', text)
        if date_match:
            metadata['date'] = date_match.group(1)

        return metadata

    def clean_html_content(self, content: str) -> str:
        """
        Clean HTML content to plain text.

        Args:
            content: HTML or markdown content

        Returns:
            Cleaned text
        """
        # If content is already markdown, return it
        if not content.startswith('<'):
            return content

        soup = BeautifulSoup(content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text


# Global instance
_crawler_service: CrawlerService | None = None


def get_crawler_service() -> CrawlerService:
    """Get global crawler service instance."""
    global _crawler_service
    if _crawler_service is None:
        _crawler_service = CrawlerService()
    return _crawler_service

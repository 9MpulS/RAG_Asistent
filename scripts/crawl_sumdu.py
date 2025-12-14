"""Script to crawl documents from normative.sumdu.edu.ua using Crawl4AI."""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.crawler_service import get_crawler_service


async def test_crawl(url: str):
    """
    Test crawling a single URL.

    Args:
        url: URL to crawl
    """
    print("=" * 60)
    print("CRAWL4AI TEST")
    print("=" * 60)
    print(f"\nURL: {url}\n")

    crawler = get_crawler_service()

    try:
        print("🔄 Crawling...")
        result = await crawler.crawl_url(url)

        print("\n✓ Crawling successful!")
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"\nTitle: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"\nMetadata:")
        for key, value in result['metadata'].items():
            print(f"  - {key}: {value}")
        print(f"\nContent length: {len(result['content'])} characters")
        print(f"\nContent preview (first 500 chars):")
        print("-" * 60)
        print(result['content'][:500])
        print("-" * 60)

        # Save to file
        output_file = "data/documents/crawled_test.txt"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Title: {result['title']}\n")
            f.write(f"URL: {result['url']}\n")
            f.write(f"Metadata: {result['metadata']}\n\n")
            f.write(result['content'])

        print(f"\n✓ Content saved to: {output_file}")

    except Exception as e:
        print(f"\n❌ Error during crawling: {e}")
        sys.exit(1)


async def crawl_document_list():
    """Crawl list of documents from normative.sumdu.edu.ua main page."""
    print("=" * 60)
    print("CRAWL DOCUMENT LIST")
    print("=" * 60)
    print("\n⚠️  This feature is not yet implemented in MVP")
    print("Please use test_crawl with specific URLs for now.\n")


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Crawl documents from normative.sumdu.edu.ua"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="URL to crawl (for testing)"
    )
    parser.add_argument(
        "--crawl-all",
        action="store_true",
        help="Crawl all documents from main page (not implemented yet)"
    )

    args = parser.parse_args()

    if args.url:
        asyncio.run(test_crawl(args.url))
    elif args.crawl_all:
        asyncio.run(crawl_document_list())
    else:
        print("Usage:")
        print("  python scripts/crawl_sumdu.py --url <URL>")
        print("  python scripts/crawl_sumdu.py --crawl-all")
        print("\nExample:")
        print('  python scripts/crawl_sumdu.py --url "https://normative.sumdu.edu.ua/index.php?task=getfile&tmpl=component&id=7406"')


if __name__ == "__main__":
    main()


from modules.bookscrapper import GoodreadsBookScraper


def search_book(search_query, release_date=None):
    """
    Search for a book across multiple APIs and scraping sources
    """
    try:
        scraper = GoodreadsBookScraper()
        result = scraper.search_and_get_info(search_query)
        return result
    except Exception as e:
        print(f"❌ Error processing '{search_query}': {e}")
        return None

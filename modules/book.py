import re

import aiohttp

from urllib.parse import quote
from bs4 import BeautifulSoup

def process_open_library(data):
    """
    Process Open Library API response
    """
    if not data.get('docs') or len(data['docs']) == 0:
        return None
    book = data['docs'][0]

    # Extract author names
    authors = []
    for author in book.get('author_name', []):
        authors.append({"name": author})

    # Extract cover image
    cover_id = book.get('cover_i')
    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None

    # Extract publication date
    publish_date = book.get('first_publish_year') or book.get('publish_year', [None])[0]
    publish_date_str = str(publish_date) + "-01-01" if publish_date else None

    # Extract subjects/genres
    subjects = []
    for subject in book.get('subject', [])[:5]:  # Limit to 5 subjects
        subjects.append({"name": subject})

    return {
        "title": book.get('title', ''),
        "authors": authors,
        "publisher": book.get('publisher', [''])[0] if book.get('publisher') else '',
        "publish_date": publish_date_str,
        "cover_url": cover_url,
        "subjects": subjects,
        "rating": 0,  # Open Library doesn't provide ratings
        "description": '',  # Open Library search doesn't provide descriptions
        "number_of_pages": book.get('number_of_pages_median', 0),
        "isbn": book.get('isbn', [''])[0] if book.get('isbn') else ''
    }

def process_google_books(data):
    """
    Process Google Books API response
    """
    if not data.get('items') or len(data['items']) == 0:
        return None

    book = data['items'][0]['volumeInfo']

    # Extract authors
    authors = []
    for author in book.get('authors', []):
        authors.append({"name": author})

    # Extract cover image
    cover_url = book.get('imageLinks', {}).get('thumbnail', '')

    # Extract publication date
    publish_date = book.get('publishedDate', '')
    if publish_date and len(publish_date) == 4:  # If only year is provided
        publish_date += "-01-01"

    # Extract categories/genres
    categories = []
    for category in book.get('categories', []):
        categories.append({"name": category})

    return {
        "title": book.get('title', ''),
        "authors": authors,
        "publisher": book.get('publisher', ''),
        "publish_date": publish_date,
        "cover_url": cover_url,
        "subjects": categories,
        "rating": book.get('averageRating', 0),
        "description": book.get('description', ''),
        "number_of_pages": book.get('pageCount', 0),
        "isbn": book.get('industryIdentifiers', [{}])[0].get('identifier', '') if book.get(
            'industryIdentifiers') else ''
    }

async def fetch_goodreads_book(session, title):
    """
    Scrape Goodreads for book information
    """
    search_url = f"https://www.goodreads.com/search?q={quote(title)}"

    async with session.get(search_url) as response:
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')

        # Find the first book result
        book_result = soup.select_one('.bookTitle')
        if not book_result:
            return None

        book_url = "https://www.goodreads.com" + book_result['href']

        # Get book details page
        async with session.get(book_url) as book_response:
            book_html = await book_response.text()
            book_soup = BeautifulSoup(book_html, 'html.parser')

            # Extract title
            title_elem = book_soup.select_one('h1#bookTitle')
            title = title_elem.text.strip() if title_elem else ''

            # Extract authors
            author_elems = book_soup.select('a.authorName span')
            authors = [{"name": author.text.strip()} for author in author_elems]

            # Extract cover image
            cover_elem = book_soup.select_one('#coverImage')
            cover_url = cover_elem['src'] if cover_elem else ''

            # Extract publication date
            pub_date_elem = book_soup.select_one('div[itemprop="datePublished"]')
            pub_date = ''
            if pub_date_elem:
                pub_date_text = pub_date_elem.text.strip()
                # Try to extract a year
                year_match = re.search(r'\d{4}', pub_date_text)
                if year_match:
                    pub_date = year_match.group(0) + "-01-01"

            # Extract genres/subjects
            genre_elems = book_soup.select('a.actionLinkLite.bookPageGenreLink')
            subjects = [{"name": genre.text.strip()} for genre in genre_elems[:5]]  # Limit to 5 genres

            # Extract rating
            rating_elem = book_soup.select_one('span[itemprop="ratingValue"]')
            rating = float(rating_elem.text.strip()) if rating_elem else 0

            # Extract description
            desc_elem = book_soup.select_one('div#description span:nth-of-type(2)')
            if not desc_elem:
                desc_elem = book_soup.select_one('div#description span')
            description = desc_elem.text.strip() if desc_elem else ''

            # Extract number of pages
            pages_elem = book_soup.select_one('span[itemprop="numberOfPages"]')
            pages = 0
            if pages_elem:
                pages_text = pages_elem.text.strip()
                pages_match = re.search(r'\d+', pages_text)
                if pages_match:
                    pages = int(pages_match.group(0))

            # Extract ISBN
            isbn_elem = book_soup.select_one('span[itemprop="isbn"]')
            isbn = isbn_elem.text.strip() if isbn_elem else ''

            return {
                "title": title,
                "authors": authors,
                "publisher": '',  # Goodreads doesn't always show publisher prominently
                "publish_date": pub_date,
                "cover_url": cover_url,
                "subjects": subjects,
                "rating": rating,
                "description": description,
                "number_of_pages": pages,
                "isbn": isbn
            }

async def search_book(title):
    """
    Search for a book across multiple APIs and scraping sources
    """
    async with aiohttp.ClientSession() as session:

        # Next try Google Books
        google_books_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{quote(title)}"
        # If you have an API key: &key={GOOGLE_BOOKS_API_KEY}
        async with session.get(google_books_url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('totalItems', 0) > 0:
                    processed_data = process_google_books(data)
                    if processed_data:
                        return {"source": "Google Books", "data": processed_data}

        # Try Open Library first
        open_lib_url = f"https://openlibrary.org/search.json?title={quote(title)}"
        async with session.get(open_lib_url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('numFound', 0) > 0:
                    processed_data = process_open_library(data)
                    if processed_data:
                        return {"source": "Open Library", "data": processed_data}

        # Fall back to Goodreads scraping
        try:
            goodreads_data = await fetch_goodreads_book(session, title)
            if goodreads_data:
                return {"source": "Goodreads (scraped)", "data": goodreads_data}
        except Exception as e:
            print(f"Error scraping Goodreads: {str(e)}")

    return None
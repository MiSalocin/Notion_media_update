import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random

class GoodreadsBookScraper:
    def __init__(self):
        # Using a desktop browser User-Agent to avoid detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64;x64)AppleWebKit/'
                          '537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        }
        
    def search_book(self, query):
        """Search for a book on Goodreads and return the URL of the first result."""
        search_url = f"https://www.goodreads.com/search?q={query.replace(' ', '+')}"
        response = requests.get(search_url, headers=self.headers)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        book_link = soup.select_one('a.bookTitle')
        
        if book_link:
            return f"https://www.goodreads.com{book_link['href']}"
        return None

    def get_book_info(self, book_url):

        """Scrape book information from a Goodreads book page."""
        response = requests.get(book_url, headers=self.headers)
        
        if response.status_code != 200:
            return {"error": f"Failed to access page: {response.status_code}"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        book_info = {
            "name":        None,
            "first_publication_year": None,
            "writer":      None,
            "summary":     None,
            "is_released": True,  # Default assumption
            "genres":      [],
            "pages":       None,
            "rating":      None,
            "url":         book_url,
            "cover_url":   None
        }
        
        # Get book title
        title_element = soup.select_one('h1.Text__title1')
        if title_element:
            book_info["name"] = title_element.text.strip()
        
        # Get author
        author_element = soup.select_one('span.ContributorLink__name')
        if author_element:
            book_info["writer"] = author_element.text.strip()
        
        # Get publication year
        pub_info = soup.select_one('[data-testid="publicationInfo"]')
        if pub_info:
            pub_text = pub_info.text.strip()
            pub_text = pub_text.replace("Expected publication ", "").replace("First published ","")
            book_info["first_publication_year"] = pub_text
            
        # Get summary
        summary_element = soup.select_one('div.TruncatedContent__text div.DetailsLayoutRightParagraph__widthConstrained')
        if summary_element:
            summary_element = summary_element.text.strip()
            if summary_element[:3] == "TBA":
                summary_element = summary_element[3:]
            book_info["summary"] = summary_element
        
        # Get genres
        genre_elements = soup.select('span.BookPageMetadataSection__genreButton a.Button')
        if genre_elements:
            book_info["genres"] = [genre.text.strip() for genre in genre_elements]
        
        # Get number of pages
        book_details = soup.select_one('[data-testid="pagesFormat"]')
        if book_details:
            page_match = re.search(r'(\d+) pages', book_details.text)
            if page_match:
                book_info["number_of_pages"] = int(page_match.group(1))
        
        # Get rating
        rating_element = soup.select_one('div.RatingStatistics__rating')
        if rating_element:
            try:
                book_info["rating"] = float(rating_element.text.strip())
            except ValueError:
                pass
        
        # Check if the book is not yet released
        not_released_indicator = soup.find(string=re.compile(r'Expected publication', re.IGNORECASE))
        if not_released_indicator:
            book_info["is_released"] = False

        # Get cover URL
        cover_url = soup.select_one('.ResponsiveImage, [role="presentation"]')
        if cover_url and 'src' in cover_url.attrs:
            book_info["cover"] = cover_url['src']

        return book_info

    def search_and_get_info(self, book_title):
        """Search for a book and get its information."""
        book_url = self.search_book(book_title)
        if not book_url:
            return {"error": f"Could not find book: {book_title}"}
        
        # Random delay to avoid being blocked
        time.sleep(random.uniform(1, 3))
        return self.get_book_info(book_url)
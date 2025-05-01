import re

from urllib.parse import quote
from datetime import datetime

from difflib import SequenceMatcher
from modules.config import *


def calculate_title_similarity(title1, title2):
    """
    Calculate the similarity between two titles using a combination of techniques

    Args:
        title1: First title
        title2: Second title

    Returns:
        A similarity score between 0 and 1, where 1 is a perfect match
    """


    # Normalize titles for better comparison
    def normalize(title):
        # Convert to lowercase and remove special characters
        norm = re.sub(r'[^\w\s]', '', title.lower())
        # Remove extra spaces
        norm = re.sub(r'\s+', ' ', norm).strip()
        return norm

    title1_norm = normalize(title1)
    title2_norm = normalize(title2)

    # Check for an exact match first
    if title1_norm == title2_norm:
        return 1.0

    # Use a sequence matcher for fuzzy matching
    ratio = SequenceMatcher(None, title1_norm, title2_norm).ratio()

    # Give bonus for containment
    if title1_norm in title2_norm or title2_norm in title1_norm:
        ratio = (ratio + 0.3) / 1.3  # Weighted average favoring ratio

    return ratio

def calculate_date_similarity(date1_str, date2_str):
    """
    Calculate how similar two dates are (smaller value = more similar)
    Returns the absolute difference in days between two dates
    """
    if not date1_str or not date2_str:
        return float('inf')  # Return infinity if either date is missing

    try:
        date1 = datetime.strptime(date1_str[:10], "%Y-%m-%d")  # Extract just the date part
        date2 = datetime.strptime(date2_str[:10], "%Y-%m-%d")
        return abs((date1 - date2).days)
    except ValueError:
        return float('inf')  # Return infinity if date parsing fails


def choose_best_result(results, target_title, target_release_date=None):
    """
    Choose the best result based on popularity or release date proximity

    Args:
        results: List of search results from TMDB
        target_title: The title we're searching for
        target_release_date: Optional release date to match against

    Returns:
        The best matching result
    """
    if not results:
        return None

    # If we only have one result, return it
    if len(results) == 1:
        return results[0]

    # If we have a target release date, find the result closest to that date
    if target_release_date:
        best_match = list()

        # Calculate scores for each result
        for item in results:

            release_date = (item["release_date"]   if "release_date"   in item
                       else item["first_air_date"] if "first_air_date" in item
                       else None)
            if not release_date:
                continue

            item_title = item.get("title", item.get("name", ""))
            title_score = calculate_title_similarity(target_title, item_title)

            date_score = 0
            if target_release_date:
                release_date = (item.get("release_date") or
                                item.get("first_air_date"))
                if release_date:
                    # Convert day difference to a 0-1 score (using a decay function)
                    days_diff = calculate_date_similarity(target_release_date, release_date)
                    # Maximum difference we care about (a year)
                    max_diff = 365
                    date_score = max(0, 1 - min(days_diff, max_diff) / max_diff)

            # Get the popularity score (already normalized by TMDB)
            popularity = item.get("popularity", 0) / 100.0  # Normalize to 0-1 range
            popularity_score = min(1.0, popularity)  # Cap at 1.0

            # Calculate weighted final score
            # Title is most important (weight: 0.7)
            # Date is second (weight: 0.2)
            # Popularity is least important (weight: 0.1)
            final_score = (0.5 * title_score) + (0.4 * date_score) + (0.1 * popularity_score)

            # Check if this is the best match so far
            if final_score > best_match[0]:
                best_match = [final_score, item]

        if best_match:
            return best_match[1]
    # Otherwise, return the first result
    return results[0]


def search_movies_and_series(search_query, media_type, release_date):

    search_url = ("https://api.themoviedb.org/3/search/"
                  f"{'tv' if media_type == 'TV Series' else 'movie'}"
                  f"?query={quote(search_query, safe='')}"
                  "&include_adult=true"
                  "&language=en-US"
                  "&page=1")

    search_response = requests.get(search_url, headers=tmdb_headers)
    search_results = search_response.json().get("results", [])
    
    if not search_results:
        print(f"No valid result for '{search_query}'.")
        return None

    # Choose the best result based on popularity or release date
    best_result = choose_best_result(search_results, search_query, release_date)
    if not best_result and best_result is None:
        print(f"No valid result for '{search_query}'.")
        return None

    # === PROCESS CHOSEN RESULT ===
    item_id = best_result.get("id")
    tmdb_media_type = best_result.get("media_type")

    # Map Notion media types to TMDB media types
    if media_type == "Movie" or (media_type is None and tmdb_media_type == "movie"):
        url = f"https://api.themoviedb.org/3/movie/{item_id}?append_to_response=credits,watch/providers"
        response = requests.get(url, headers=tmdb_headers, timeout=10)
        return response.json()

    elif media_type == "TV Series" or (media_type is None and tmdb_media_type == "tv"):
        url = f"https://api.themoviedb.org/3/tv/{item_id}?append_to_response=credits,watch/providers"
        response = requests.get(url, headers=tmdb_headers, timeout=10)
        
        return response.json()
    return None

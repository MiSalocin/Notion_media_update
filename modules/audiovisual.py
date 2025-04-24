import requests

from urllib.parse import quote
from datetime import datetime

from modules.config import *

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
    # print(f"- {target_title}")
    if not results:
        return None

    # If we only have one result, return it
    if len(results) == 1:
        return results[0]

    # If we have a target release date, find the result closest to that date
    if target_release_date:
        best_match = None
        smallest_date_diff = float('inf')

        for item in results:
            release_date = item["release_date"] if "release_date" in item else item["first_air_date"]

            date_diff = calculate_date_similarity(target_release_date, release_date)

            if date_diff < smallest_date_diff:
                smallest_date_diff = date_diff
                best_match = item

        if best_match:
            return best_match
    # Otherwise, return the most popular result
    return max(results, key=lambda x: x.get("popularity", 0))


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
        return

    # Choose the best result based on popularity or release date
    best_result = choose_best_result(search_results, search_query, release_date)

    if not best_result and best_result is None:
        print(f"No valid result for '{search_query}'.")
        return

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

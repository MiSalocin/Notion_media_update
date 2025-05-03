import json
from urllib.parse import quote
from modules.config import *

def search_movies_and_series(search_query, media_type, release_date=None):

    # Search URL for TMDB
    url = ("https://api.themoviedb.org/3/search/"
                  f"{'tv' if media_type == 'TV Series' else 'movie'}"
                  "?append_to_response=credits,watch/provider"
                  f"&query={quote(search_query, safe='')}"
                  "&include_adult=true"
                  "&language=en-US"
                  "&page=1")

    # Search TMDB and check for results
    response = requests.get(url, headers=tmdb_headers)
    results = response.json().get("results", [])
    if not results:
        print(f"No valid result for '{search_query}'.")
        return None

    # Choose the best result based on title, popularity or release date and get its ID
    item_id = choose_best_result(results, search_query, release_date).get("id")

    # Get extra info from the result
    if media_type == "Movie":
        url = f"https://api.themoviedb.org/3/movie/{item_id}?append_to_response=credits,watch/providers"
    elif media_type == "TV Series":
        url = f"https://api.themoviedb.org/3/tv/{item_id}?append_to_response=credits,watch/providers"

    response = requests.get(url, headers=tmdb_headers, timeout=10)
    return response.json()

from urllib.parse import quote
from modules.config import *

def search_movies_and_series(search_query, media_type, release_date=None):

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

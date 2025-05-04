import json
from urllib.parse import quote
from modules.config import *

valid_streaming = ["Netflix", "Disney Plus", "Amazon Prime Video", "Max", "Apple TV+", "HBO Max"]
languages = ["pt-BR", "en-US"]


def search_movies_and_series(search_query, media_type, release_date=None):
    results = []
    url = ""
    for lang in languages:    
        # Search URL for TMDB
        url = ("https://api.themoviedb.org/3/search/"
                    f"{'tv' if media_type == 'TV Series' else 'movie'}"
                    "?append_to_response=credits,watch/provider"
                    f"&query={quote(search_query, safe='')}"
                    f"&language={lang}"
                    "&include_adult=true"
                    "&page=1")

        # Search TMDB and check for results
        response = requests.get(url, headers=tmdb_headers)
        response = response.json().get("results", [])
        if not response:
            continue
        for result in response:
            result["language"] = lang
            results.append(result)
    if not results:
        print(f"No valid result for '{search_query}'.")
        return None

    # Choose the best result based on title, popularity or release date and get its ID
    best_choice = choose_best_result(results, search_query, release_date)
    # Get extra info from the result
    if media_type == "Movie":
        url = f"https://api.themoviedb.org/3/movie/{best_choice.get("id")}?append_to_response=credits,watch/providers&language={best_choice.get("language")}"
    elif media_type == "TV Series":
        url = f"https://api.themoviedb.org/3/tv/{best_choice.get("id")}?append_to_response=credits,watch/providers&language={best_choice.get("language")}"
    response = requests.get(url, headers=tmdb_headers, timeout=10)
    return response.json()

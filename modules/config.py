# API Keys and other secret codes
import os
import numpy as np
import re

from difflib import SequenceMatcher
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()
WATCH_REGION         = "BR"
MAX_WORKERS          = 10
PAGE_ID              = os.getenv("PAGE_ID")
DATABASE_ID          = os.getenv("DATABASE_ID")
NOTION_TOKEN         = os.getenv("NOTION_TOKEN")
RAWG_API_KEY         = os.getenv("RAWG_API_KEY")
TMDB_API_KEY         = os.getenv("TMDB_API_KEY")
IGDB_CLIENT_ID       = os.getenv("IGDB_CLIENT_ID")
IGDB_CLIENT_SECRET   = os.getenv("IGDB_CLIENT_SECRET")
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

valid_streaming = ["Netflix", "Disney Plus", "Amazon Prime Video", "Max", "Apple TV+", "HBO Max"]

# Configure headers for the APIs
notion_headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}
tmdb_headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_API_KEY}"
}
igdb_headers = {
    "Client-ID": IGDB_CLIENT_ID,
    "Authorization": None
}
igdb_token = None


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
    best_match = [0, None]

    pop_ratio = 1
    for result in results:
        if result.get("total_rating_count"): pop_ratio = result.get("total_rating_count")\
                                                if result.get("total_rating_count") > pop_ratio else pop_ratio
    # Calculate scores for each result
    for item in results:

        item_title = item.get("title", item.get("name", ""))
        title_score = calculate_title_similarity(target_title, item_title)

        date_score = 0
        if target_release_date:
            release_date = (item.get("release_date") or
                            item.get("first_air_date") or
                            item.get("first_release_date") or
                            item.get("released"))

            if release_date:
                days_diff = calculate_date_similarity(release_date, target_release_date)
                max_diff = 1095
                date_score = max(0, 1 - min(days_diff, max_diff) / max_diff)

        # Get the popularity score (already normalized by TMDB)
        popularity = item.get("popularity", 0) / 100.0 if item.get("pop")\
                else item.get("total_rating_count") if item.get("total_rating_count")\
                else 0

        popularity_score = min(1.0, float(popularity)/pop_ratio)  # Cap at 1.0

        final_score = (0.5 * title_score) + (0.3 * date_score) + (0.2 * popularity_score)
        # Check if this is the best match so far
        if final_score > best_match[0]:
            best_match = [final_score, item]

    if best_match:
        return best_match[1]

    # Otherwise, return the first result
    return results[0]

def calculate_date_similarity(date1_str, date2_str):
    """
    Calculate how similar two dates are (smaller value = more similar)
    Returns the absolute difference in days between two dates
    """
    if not date1_str or not date2_str:
        return float('inf')  # Return infinity if either date is missing

    try:
        if isinstance(date1_str, int) or (isinstance(date1_str, str) and date1_str.isdigit()):
            date1 = datetime.fromtimestamp(int(date1_str))
        else: date1 = datetime.strptime(str(date1_str)[:10], "%Y-%m-%d")

        date2 = datetime.strptime(date2_str[:10], "%Y-%m-%d")
        return abs((date1 - date2).days)
    except ValueError:
        return float('inf')  # Return infinity if date parsing fails

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

def to_notion(data, media_type, page_id):
    """
    Convert data to Notion properties without making API calls.

    Args:
        data: The data from what you want to upload to Notion
        media_type: The type of the data, e.g., "Book" or "Movie"
        page_id: ID of an existing Notion page to update
    """
    properties = {"Type": {"select": {"name": media_type}}}
    title = ""
    poster = None
    emoji = ""
    cover = None

    if media_type == "Game":
        emoji        = "🕹️"
        title        = data.get("title", "")
        developers   = data.get("developers", [])
        release_date = data.get("release_date", "")
        cover        = data.get("background", "")
        bg_url       = data.get("cover", "")
        genres       = data.get("genres", [])
        rating       = data.get("rating", 0)
        description  = data.get("description", "")
        year         = release_date[:4] if release_date else ""
        platforms    = data.get("platforms", "")
        publishers   = data.get("publishers", [])
        status       = data.get("status", "")

        # Add game properties
        properties["Name"]                = {"title": [{"text": {"content": title}}]}
        properties["Year"]                = {"rich_text": [{"text": {"content": year}}]}
        properties["Status"]              = {"select": None} if not status else {"select": {"name": status}}
        properties["Image"]               = {"files": []} if not bg_url else {"files":[{"type": "external", "name": "Cover","external": {"url": bg_url}}]}
        properties["Director/Publisher"]  = {"multi_select": publishers or []}
        properties["Writer/Developer"]    = {"multi_select": developers}
        properties["Genre"]               = {"multi_select": genres}
        properties["Synopsis"]            = {"rich_text": []} if not description else {"rich_text": [{"text": {"content": description[:2000]}}]}
        properties["Release date"]        = {"date": None} if not release_date else {"date": {"start": release_date}}
        properties["Global Rating"]       = {"number": np.round(float(rating),1)}
        properties["Update"]              = {"select": {"name": "No"}}
        properties["Streaming/Platforms"] = {"multi_select": platforms or []}

    # Audiovisual
    if media_type == "TV Series" or media_type == "Movie":
        emoji = "🎞️" if media_type == "Movie" else "🎬"
        title = data.get("title") if media_type == "Movie" else data.get("name", "")

        if data.get("poster_path"):
            cover = f"https://image.tmdb.org/t/p/original{data.get('poster_path')}"
            poster = f"https://image.tmdb.org/t/p/original{data.get('poster_path')}"
        if data.get("backdrop_path"):
            cover = f"https://image.tmdb.org/t/p/original{data.get('backdrop_path')}"

        genres        = data.get("genres", [])
        status        = data.get("status")
        synopsis      = data.get("overview")
        release_date  = data.get("release_date") if media_type == "Movie" else data.get("first_air_date")
        global_rating = data.get("vote_average", 0)
        year          = release_date[:4] if release_date else ""
        credit        = data.get("credits", {})
        crew          = credit.get("crew", [])

        writers   = []
        directors = []

        for member in crew:
            if member.get("job") == "Screenplay" or member.get("job") == "Writer":
                writers.append({"name": member["name"]})
            if member.get("job") == "Director":
                directors.append({"name": member["name"]})

        # Get streaming providers
        providers_data = data.get("watch/providers", {})
        streaming = []
        try:
            country_data = providers_data["results"].get(WATCH_REGION, {})
            flatrate = country_data.get("flatrate", [])
            for provider in flatrate:
                if provider["provider_name"] in valid_streaming: streaming.append({"name": provider["provider_name"]})
        except Exception as e:
            streaming = [{"name": "Not available"}]
            print(f"Error getting streaming providers: {e}")
        for d in genres: d.pop('id', None)  # `None` prevents error if the key doesn't exist

        # Add shared properties
        properties["Update"]              = {"select": {"name": "No"}}
        properties["Name"]                = {"title": [{"text": {"content": title or ""}}]}
        properties["Year"]                = {"rich_text": [{"text": {"content": year or ""}}]}
        properties["Image"]               = {"files": []} if not poster else { "files": [{"type": "external", "name": "Cover", "external": {"url": poster}}]}
        properties["Status"]              = {"select": None} if not status else {"select": {"name": status}}
        properties["Genre"]               = {"multi_select": genres or []}
        properties["Writer/Developer"]    = {"multi_select": writers or []}
        properties["Director/Publisher"]  = {"multi_select": directors or []}
        properties["Synopsis"]            = {"rich_text": []} if not synopsis else {"rich_text": [{"text": {"content": synopsis}}]}
        properties["Streaming/Platforms"] = {"multi_select": streaming or []}
        properties["Release date"]        = {"date": None} if not release_date else {"date": {"start": release_date}}
        properties["Global Rating"]       = {"number": np.round(global_rating,1) or 0}

        # TV Series specific fields
        if media_type == "TV Series":
            emoji        = "🎬"
            episodes     = data.get("number_of_episodes", 0)
            seasons      = data.get("number_of_seasons", 0)
            next_episode = data.get("next_episode_to_air", {})
            last_episode = data.get("last_episode_to_air", {})
            properties["Seasons"]        = {"number": seasons or 0}
            properties["Episodes/pages"] = {"number": episodes or 0}

            if last_episode:
                season           = last_episode.get("season_number", 0)
                episode          = last_episode.get("episode_number", 0)
                ep_name          = last_episode.get("name", "")
                last_episode_str = f"S{season:02}, E{episode:02}: {ep_name}"
                properties["Last episode"] = {"rich_text": [{"text": {"content": last_episode_str}}]}

            if next_episode:
                properties["Upcoming episode"] = {"rich_text": [{"text": {"content": next_episode.get("name", "")}}]}
                properties["Next air date"]    = {"date": {"start": next_episode.get("air_date", "")}}

    cover = cover if cover else poster if poster else None
    payload = {"properties": properties,
               "cover": {"type": "external", "external": {"url": cover}} if cover else None}

    # If we have a page ID, update that page
    update_url = f"https://api.notion.com/v1/pages/{page_id}"
    update_response = requests.patch(update_url, headers=notion_headers, json=payload)
    if update_response.status_code == 200:
        print(f"{emoji}🔄 '{title}' updated in Notion.")
    else:
        requests.patch(update_url, headers=notion_headers,
                                         json={"properties": {"Update": {"select": {"name": "Yes"}}}})
        print(f"{emoji}❌ Error updating '{title}': {json.dumps(update_response.json(), indent=4)}")

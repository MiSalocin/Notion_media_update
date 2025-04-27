# API Keys and other secret codes
import os

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

def to_notion(data, media_type, page_id=None):
    """
    Upload book data to Notion database

    Args:
        data: The data from what you want to upload to Notion
        media_type: The type of the data, e.g., "Book" or "Movie"
        page_id: Optional ID of an existing Notion page to update
    """

    properties = {"Type": {"select": {"name": media_type}}}
    title = ""
    poster = cover_url = None

    emoji = ""
    if media_type == "Book":
        emoji = "📖"
        title = data.get("title", "")
        authors = data.get("authors", [])
        publish_date = data.get("publish_date", "")
        cover_url = data.get("cover_url", "")
        subjects = data.get("subjects", [])
        rating = data.get("rating", 0)
        description = data.get("description", "")
        pages = data.get("number_of_pages", 0)

        # Get year from publish date
        year = publish_date[:4] if publish_date else ""

        # Add book properties
        properties["Name"] = {"title": [{"text": {"content": title}}]}
        properties["Year"] = {"rich_text": [{"text": {"content": year}}]}
        properties["Image"] = {"files": []} if not cover_url else {
            "files": [{"type": "external", "name": "Cover", "external": {"url": cover_url}}]}
        properties["Writer"] = {"multi_select": authors}
        properties["Genre"] = {"multi_select": subjects}
        properties["Synopsis"] = {"rich_text": []} if not description else {
            "rich_text": [{"text": {"content": description[:2000]}}]}  # Limit to 2000 chars
        properties["Release date"] = {"date": None} if not publish_date else {"date": {"start": publish_date}}
        properties["Global Rating"] = {"number": rating}
        properties["Episodes/pages"] = {"number": pages}
    if media_type == "Game":
        emoji = "🕹️"
        title = data.get("title", "")
        developers = data.get("developers", [])
        release_date = data.get("release_date", "")
        background_url = data.get("background_url", "")
        cover_url = data.get("cover_url", "")
        genres = data.get("genres", [])
        rating = data.get("rating", 0)
        description = data.get("description", "")

        # Get year from release date
        year = release_date[:4] if release_date else ""

        # Add game properties
        properties["Name"] = {"title": [{"text": {"content": title}}]}
        properties["Year"] = {"rich_text": [{"text": {"content": year}}]}
        properties["Image"] = {"files": []} if not background_url else {
            "files": [{"type": "external", "name": "Cover", "external": {"url": background_url}}]}
        properties["Writer"] = {"multi_select": developers}
        properties["Genre"] = {"multi_select": genres}
        properties["Synopsis"] = {"rich_text": []} if not description else {
            "rich_text": [{"text": {"content": description[:2000]}}]}  # Limit to 2000 chars
        properties["Release date"] = {"date": None} if not release_date else {"date": {"start": release_date}}
        properties["Global Rating"] = {"number": rating}
    if media_type == "TV Series" or media_type == "Movie":
        emoji = "🎬"
        title = data.get("title") if media_type == "Movie" else data.get("name")
        # cover = f"https://image.tmdb.org/t/p/original{data.get('backdrop_path')}" if data.get("backdrop_path") else None
        poster = f"https://image.tmdb.org/t/p/original{data.get('poster_path')}" if data.get("poster_path") else None
        genres = data.get("genres", [])
        status = data.get("status")
        synopsis = data.get("overview")
        release_date = data.get("release_date") if media_type == "Movie" else data.get("first_air_date")
        global_rating = data.get("vote_average", 0)
        year = release_date[:4] if release_date else ""


        # Extract credits data
        credit = data.get("credits", {})
        crew = credit.get("crew", [])

        # Extract writers and directors by filtering the crew
        writers = []
        directors = []
        for member in crew:
            job = member.get("job")
            if job == "Writer":
                writers.append({"name": member["name"]})
            elif job == "Director":
                directors.append({"name": member["name"]})

        # Get streaming providers
        providers_data = data.get("watch/providers", {})
        streaming = []
        try:
            country_data = providers_data["results"].get(WATCH_REGION, {})
            flatrate = country_data.get("flatrate", [])
            for provider in flatrate: streaming.append({"name": provider["provider_name"]})
        except:
            streaming = [{"name": "Not available"}]
        for d in genres: d.pop('id', None)  # `None` prevents error if key doesn't exist

        # Add shared properties
        properties["Name"] = {"title": [{"text": {"content": title or ""}}]}
        properties["Year"] = {"rich_text": [{"text": {"content": year or ""}}]}
        properties["Image"] = {"files": []} if not poster else {
            "files": [{"type": "external", "name": "Cover", "external": {"url": poster}}]}
        properties["Status"] = {"select": None} if not status else {"select": {"name": status}}
        properties["Genre"] = {"multi_select": genres or []}
        properties["Writer"] = {"multi_select": writers or []}
        properties["Director"] = {"multi_select": directors or []}
        properties["Synopsis"] = {"rich_text": []} if not synopsis else {"rich_text": [{"text": {"content": synopsis}}]}
        properties["Streaming"] = {"multi_select": streaming or []}
        properties["Release date"] = {"date": None} if not release_date else {"date": {"start": release_date}}
        properties["Global Rating"] = {"number": global_rating or 0}

        # TV Series specific fields
        if media_type == "TV Series":
            episodes = data.get("number_of_episodes", 0)
            seasons = data.get("number_of_seasons", 0)
            next_episode = data.get("next_episode_to_air", {})
            last_episode = data.get("last_episode_to_air", {})

            properties["Seasons"] = {"number": seasons or 0}
            properties["Episodes/pages"] = {"number": episodes or 0}

            if last_episode:
                season = last_episode.get("season_number", 0)
                episode = last_episode.get("episode_number", 0)
                ep_name = last_episode.get("name", "")
                last_episode_str = f"S{season:02}, E{episode:02}: {ep_name}"
                properties["Last episode"] = {"rich_text": [{"text": {"content": last_episode_str}}]}
            else:
                properties["Last episode"] = {"rich_text": []}

            if next_episode:
                properties["Upcoming episode"] = {"rich_text": [{"text": {"content": next_episode.get("name", "")}}]}
                properties["Next air date"] = {"date": {"start": next_episode.get("air_date", "")}}
            else:
                properties["Upcoming episode"] = {"rich_text": []}
                properties["Next air date"] = {"date": None}

    payload = {"properties": properties}
    if cover_url:   payload["cover"] = {"type": "external", "external": {"url": cover_url}}
    if poster:      payload["cover"] = {"type": "external", "external": {"url": poster}}

    # If we have a page ID, update that page
    if page_id:
        update_url = f"https://api.notion.com/v1/pages/{page_id}"
        update_response = requests.patch(update_url, headers=notion_headers, json=payload)
        if update_response.status_code == 200:
            print(f"{emoji}🔄 '{title}' updated in Notion.")
        else:
            print(f"{emoji}❌ Error updating '{title}': {update_response.text}")
    else:
        # Otherwise search for a page with the same title
        query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        query_payload = {"filter": {"property": "Name","title": {"equals": title}}}

        query_response = requests.post(query_url, headers=notion_headers, json=query_payload)
        results = query_response.json().get("results", [])

        if results:
            page_id = results[0]["id"]
            update_url = f"https://api.notion.com/v1/pages/{page_id}"
            update_response = requests.patch(update_url, headers=notion_headers, json=payload)
            if update_response.status_code == 200:
                print(f"{emoji}🔄 '{title}' updated in Notion.")
            else:
                print(f"{emoji}❌ Error updating '{title}': {update_response.text}")
        else:
            # Create a new page if no matching page was found
            create_url = "https://api.notion.com/v1/pages"
            create_payload = {
                "parent": {"database_id": DATABASE_ID},
                "properties": properties
            }
            create_response = requests.post(create_url, headers=notion_headers, json=create_payload)
            if create_response.status_code in [200, 201]:
                print(f"{emoji}✅ '{title}' added to notion.")
            else:
                print(f"{emoji}❌ Error adding '{title}': {create_response.text}")
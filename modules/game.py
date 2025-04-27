import aiohttp
from urllib.parse import quote
from modules.config import *

import asyncio
from datetime import datetime

igdb_token = None

def get_igdb_access_token():
    """
    Obtain access token for IGDB API (Twitch)
    """
    url = f"https://id.twitch.tv/oauth2/token?client_id={IGDB_CLIENT_ID}&client_secret={IGDB_CLIENT_SECRET}&grant_type=client_credentials"
    response = requests.post(url)
    data = response.json()
    return data.get("access_token")

async def search_igdb_game(title):
    """
    Search for a game using the IGDB API
    """

    global igdb_token, igdb_headers

    # Get token if there's none
    if not igdb_token:
        igdb_token = get_igdb_access_token()
        igdb_headers["Authorization"] = f"Bearer {igdb_token}"

    # Construct the search for IGDB
    query = (f'search "{title}"; fields name, summary, storyline, cover.url, first_release_date, rating,'
             f'aggregated_rating, genres.name, platforms.name, involved_companies.company.name,'
             f'involved_companies.developer, involved_companies.publisher, age_ratings.rating, age_ratings.category;')

    url = "https://api.igdb.com/v4/games"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=igdb_headers, data=query) as response:
            if response.status == 200:
                data = await response.json()
                if data and len(data) > 0:
                    return process_igdb_game(data[0])
    return None

def process_igdb_game(game_data):
    """
    Process IGDB API response for a game
    """
    # Extract publishers/devs
    publishers = []
    developers = []

    if game_data.get('involved_companies'):
        for company in game_data['involved_companies']:
            company_name = company.get('company', {}).get('name', '')
            if company_name:
                if company.get('developer'):
                    developers.append({"name": company_name})
                if company.get('publisher'):
                    publishers.append({"name": company_name})

    # Extract platforms
    platforms = []
    for platform in game_data.get('platforms', []):
        if platform.get('name'):
            platforms.append({"name": platform['name']})

    # Extract genres
    genres = []
    for genre in game_data.get('genres', []):
        if genre.get('name'):
            genres.append({"name": genre['name']})

    # Extract release dates and convert from timestamp Unix to ISO
    release_date = None
    if game_data.get('first_release_date'):
        release_date = datetime.fromtimestamp(game_data['first_release_date']).strftime('%Y-%m-%d')

    # Choose storyline over summary if available
    description = game_data.get('storyline') or game_data.get('summary', '')

    # Process cover URL
    cover_url = None
    if game_data.get('cover', {}).get('url'):
        cover_url = game_data['cover']['url']
        if cover_url.startswith('//'):
            cover_url = f"https:{cover_url}".replace('t_thumb', 't_cover_big')

    alternative_images = []

    # Check for box art in artworks
    box_art = None
    if game_data.get('artworks'):
        for artwork in game_data['artworks']:
            artwork_url = artwork.get('url')
            if artwork_url:
                # Convert relative URLs to absolute and increase image size
                if artwork_url.startswith('//'):
                    artwork_url = f"https:{artwork_url}".replace('t_thumb', 't_1080p')
                alternative_images.append(artwork_url)

                # Look for box art in artwork names or tags
                artwork_name = artwork.get('name', '').lower()
                if artwork_name and ('box' in artwork_name or 'cover' in artwork_name or 'poster' in artwork_name):
                    box_art = artwork_url

    # Check for screenshots if no box art found
    if not box_art and game_data.get('screenshots'):
        for screenshot in game_data['screenshots']:
            screenshot_url = screenshot.get('url')
            if screenshot_url:
                # Convert relative URLs to absolute and increase image size
                if screenshot_url.startswith('//'):
                    screenshot_url = f"https:{screenshot_url}".replace('t_thumb', 't_1080p')
                alternative_images.append(screenshot_url)

    # Use the first screenshot as background image if available
    background_image = None
    if alternative_images:
        background_image = alternative_images[0]

    # Prioritize box art if found, otherwise use cover, then fall back to first alternative image
    final_cover_url = box_art or cover_url or background_image

    return {
        "title": game_data.get('name', ''),
        "developers": developers,
        "publishers": publishers,
        "release_date": release_date,
        "cover_url": final_cover_url,
        "backdrop_url": background_image,
        "genres": genres,
        "platforms": platforms,
        "rating": game_data.get('rating') / 10 if game_data.get('rating') else 0,
        "metacritic": game_data.get('aggregated_rating'),
        "description": description
    }

def process_rawg_game(game_data):
    """
    Process RAWG API response for a game
    """
    # Extract publishers/devs.
    publishers = []
    for pub in game_data.get('publishers', []): publishers.append({"name": pub["name"]})

    developers = []
    for dev in game_data.get('developers', []): developers.append({"name": dev["name"]})

    # Extract platforms
    platforms = []
    for platform in game_data.get('platforms', []):
        if platform.get('platform'): platforms.append({"name": platform['platform']['name']})

    # Extract genres
    genres = []
    for genre in game_data.get('genres', []):
        genres.append({"name": genre["name"]})

    # Extract release dates
    release_date = game_data.get('released')

    # Check for cover image in different possible locations
    cover_url = None

    # Try to find cover image in screenshots if available
    if game_data.get('screenshots') and len(game_data['screenshots']) > 0:
        for screenshot in game_data['screenshots']:
            # Look for images that might be covers (usually with "cover" in the filename)
            image_url = screenshot.get('image')
            if image_url and ('cover' in image_url.lower() or 'box' in image_url.lower()):
                cover_url = image_url
                break

    # If no cover found in screenshots, check for a different image source
    if not cover_url and game_data.get('images'):
        for image in game_data['images']:
            if image.get('type') == 'cover' or 'cover' in image.get('name', '').lower():
                cover_url = image.get('image')
                break

    # If still no cover found, look for box art or official art
    if not cover_url and game_data.get('stores'):
        for store in game_data['stores']:
            store_info = store.get('store', {})
            if store_info.get('image_background') and 'cover' in store_info.get('slug', ''):
                cover_url = store_info.get('image_background')
                break

    # Fall back to background image if no cover found
    if not cover_url:
        cover_url = game_data.get('background_image')

    return {
        "title": game_data.get('name', ''),
        "developers": developers,
        "publishers": publishers,
        "release_date": release_date,
        "cover_url": cover_url,
        "background_url": game_data.get('background_image'),
        "genres": genres,
        "platforms": platforms,
        "rating": game_data.get('rating', 0),
        "metacritic": game_data.get('metacritic'),
        "description": game_data.get('description_raw', '')
    }

def search_game(search_query):
    try:
        game_data = asyncio.run(search_igdb_game(search_query))
        if game_data:
            return game_data
    except Exception as e:
        print(f"Error searching IGDB: {str(e)}")
    try:
        rawg_url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={quote(search_query)}&page_size=1"
        rawg_response = requests.get(rawg_url, timeout=10)
        rawg_data = rawg_response.json()

        if rawg_data.get("results") and len(rawg_data["results"]) > 0:
            game_id = rawg_data["results"][0]["id"]
            detail_url = f"https://api.rawg.io/api/games/{game_id}?key={RAWG_API_KEY}"
            detail_response = requests.get(detail_url, timeout=10)
            game_details = detail_response.json()

            game_data = process_rawg_game(game_details)
            return game_data
    except Exception as e:
        print(f"Error searching RAWG: {str(e)}")

    # Or IGDB

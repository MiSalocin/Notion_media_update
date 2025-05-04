from urllib.parse import quote
from modules.config import *

from datetime import datetime

igdb_token = None

def search_igdb_game(title, release_date=None):
    """
    Search for a game using the IGDB API
    """

    global igdb_token, igdb_headers

    # Get a token if there's none
    if not igdb_token:
        url = (f"https://id.twitch.tv/oauth2/token?client_id={IGDB_CLIENT_ID}"
               f"&client_secret={IGDB_CLIENT_SECRET}"
               f"&grant_type=client_credentials")
        response = requests.post(url)
        igdb_token = response.json().get("access_token")
        igdb_headers["Authorization"] = f"Bearer {igdb_token}"

    # Construct the search for IGDB
    query = (f'search "{title}";'
             f'fields total_rating,'
                    f'total_rating_count,'
                    f'name,'
                    f'summary,'
                    f'rating,'
                    f'cover.url,'
                    f'storyline,'
                    f'genres.name,'
                    f'artworks.url,'
                    f'platforms.name,'
                    f'aggregated_rating,'
                    f'first_release_date,'
                    f'involved_companies.developer,'
                    f'involved_companies.publisher,'
                    f'involved_companies.company.name;')

    url = "https://api.igdb.com/v4/games"
    response = requests.post(url, headers=igdb_headers, data=query)

    if response.status_code == 200:
        data = response.json()
        if data:
            data = choose_best_result(data, title, release_date)
            return process_igdb_game(data)

    return None

def process_igdb_game(data):
    """
    Process IGDB API response for a game
    """

    genres      = [{"name": genre['name']}
                   for genre in data.get('genres', [])]

    platforms   = [{"name": platform['name']}
                   for platform in data.get('platforms', [])]

    developers  = [{"name": company.get('company', {}).get('name')}
                   for company in data.get('involved_companies', [])
                   if company.get('developer') and company.get('company', {}).get('name')]

    publishers  = [{"name": company.get('company', {}).get('name')}
                   for company in data.get('involved_companies', [])
                   if company.get('publisher') and company.get('company', {}).get('name')]
    release_date = 0
    status = "Unknown"
    if data.get('first_release_date'):
        release_date = datetime.fromtimestamp(data['first_release_date'])
        if release_date > datetime.now():
            status = "Upcoming"
        elif release_date < datetime.now():
            status = "Released"

    release_date = release_date.strftime('%Y-%m-%d')
    description = data.get('storyline') or data.get('summary', '')

    # Process cover URL
    bg_img = None
    cover = None

    if data.get('cover', {}).get('url'):
        cover = data['cover']['url']
        if cover.startswith('//'):
            cover = f"https:{cover}".replace('t_thumb', 't_1080p')


    # Check for box art in artworks
    if data.get('artworks'):
        bg_img = data['artworks'][0]['url']
        if bg_img.startswith('//'):
            bg_img = f"https:{bg_img}".replace('t_thumb', 't_1080p')

        if not cover:
            for artwork in data['artworks']:
                artwork_url = artwork.get('url')
                if artwork_url:
                    if artwork_url.startswith('//'):
                        artwork_url = f"https:{artwork_url}".replace('t_thumb', 't_1080p')

                    artwork_name = artwork.get('name', '').lower()
                    if (not cover and artwork_name and
                            ('box'    in artwork_name or
                             'cover'  in artwork_name or
                             'poster' in artwork_name)):
                        cover = artwork_url

    # Check for screenshots if no box art found
    if not bg_img and data.get('screenshots'):
        for screenshot in data['screenshots']:
            screenshot_url = screenshot.get('url')
            if screenshot_url:
                # Convert relative URLs to absolute and increase image size
                if screenshot_url.startswith('//'):
                    screenshot_url = f"https:{screenshot_url}".replace('t_thumb', 't_1080p')
                bg_img = screenshot_url

    return {
        "status":           status,
        "genres":           genres,
        "title":            data.get('name', ''),
        "rating":           data.get('rating') / 10 if data.get('rating') else 0,
        "cover":            cover,
        "platforms":        platforms,
        "developers":       developers,
        "publishers":       publishers,
        "description":      description,
        "release_date":     release_date,
        "background":       bg_img,
    }

def process_rawg_game(game_data):
    """
    Process RAWG API response for a game
    """
    publishers = [{"name": pub["name"]} for pub in game_data.get('publishers', [])]
    developers = [{"name": dev["name"]} for dev in game_data.get('developers', [])]
    platforms  = [{"name": platform['platform']['name']} for platform in game_data.get('platforms', [])]
    genres     = [{"name": genre["name"]} for genre in game_data.get('genres', [])]

    cover = None

    # Try to find the cover image in screenshots if available
    if game_data.get('screenshots') and len(game_data['screenshots']) > 0:
        for screenshot in game_data['screenshots']:
            # Look for images that might be covers (usually with "cover" in the filename)
            image_url = screenshot.get('image')
            if image_url and ('cover' in image_url.lower() or 'box' in image_url.lower()):
                cover = image_url
                break

    # If no cover found in screenshots, check for a different image source
    elif game_data.get('images'):
        for image in game_data['images']:
            if image.get('type') == 'cover' or 'cover' in image.get('name', '').lower():
                cover = image.get('image')
                break

    # If still no cover found, look for box art or official art
    elif game_data.get('stores'):
        for store in game_data['stores']:
            store_info = store.get('store', {})
            if store_info.get('image_background') and 'cover' in store_info.get('slug', ''):
                cover = store_info.get('image_background')
                break

    # Fall back to background image if no cover found
    if not cover:
        cover = game_data.get('background_image')

    return {
        "title":          game_data.get('name', ''),
        "rating":         game_data.get('rating', 0)*2,
        "genres":         genres,
        "cover":          cover,
        "platforms":      platforms,
        "developers":     developers,
        "publishers":     publishers,
        "release_date":   game_data.get('released'),
        "description":    game_data.get('description_raw', ''),
        "background":     game_data.get('background_image', ''),
    }

def search_game(search_query, release_date=None):
    try:
        game_data = search_igdb_game(search_query, release_date)
        if game_data:
            return game_data
    except Exception as e:
        print(f"Error searching IGDB: {str(e)}, searching RAWG...")
    print("Game not found in IGDB, searching RAWG...")


    try:
        rawg_url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={quote(search_query)}&page_size=10"
        rawg_response = requests.get(rawg_url, timeout=10)
        rawg_data = rawg_response.json()

        if rawg_data.get("results") and len(rawg_data["results"]) > 0:
            game_data = choose_best_result(rawg_data["results"], search_query, release_date)
            game_id = game_data["id"]
            detail_url = f"https://api.rawg.io/api/games/{game_id}?key={RAWG_API_KEY}"
            detail_response = requests.get(detail_url, timeout=10)
            game_details = detail_response.json()

            game_data = process_rawg_game(game_details)
            return game_data
        return None
    except Exception as e:
        print(f"Error searching RAWG: {str(e)}")
        return None


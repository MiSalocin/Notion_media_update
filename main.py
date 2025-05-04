import time
import concurrent.futures

from modules.audiovisual import *
from modules.book import search_book
from modules.game import *

def get_all_notion_entries():
    """
    Return the titles, types, and release dates of all notion entries
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    all_entries = []
    start_cursor = None

    while True:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor

        response = requests.post(url, headers=notion_headers, json=payload, timeout=10)
        data = response.json()
        results = data.get("results", [])

        for page in results:
            title_prop          = page["properties"].get("Name", {})            .get("title", [])
            type_prop           = page["properties"].get("Type", {})            .get("select", {})
            release_date_prop   = page["properties"].get("Release date", {})    .get("date", {})
            update              = page["properties"].get("Update",{})           .get("select",{})
            status              = page["properties"].get("Status",{})           .get("select",{})
            next_air_date       = page["properties"].get("Next air date", {})   .get("date", {})
            page_id             = page["id"]

            if type_prop and status:
                if  status.get("name") not in ["Released", "Ended", "Canceled"]:
                    update = True
            elif type_prop and not status:
                update = True

            if update and (type(update) != bool):
                update = update.get("name")
                if update == "Yes":
                    update = True
                else:
                    update = False
            else:
                update = True
            if title_prop and update:
                name = title_prop[0]["text"]["content"]
                media_type = type_prop.get("name") if type_prop else None
                release_date = release_date_prop.get("start") if release_date_prop else None
                all_entries.append({
                    "title": name,
                    "type": media_type,
                    "release_date": release_date,
                    "page_id": page_id
                })

        if data.get("has_more"):
            start_cursor = data["next_cursor"]
        else:
            break

    return all_entries


def search(search_query, media_type=None, release_date=None, page_id=None):
    """
    Search for media in TMDB, books in multiple sources, or games in RAWG/IGDB and upload to Notion
    
    Args:
        search_query: The query string to search for
        media_type: The type of media to search for ('Movie', 'Tv Series', 'Book', or 'Game')
        release_date: Optional release date to help select the right version
        page_id: Optional ID of an existing Notion page to update
    """
    try:
        if media_type == "Game":
            result = search_game(search_query)
        elif media_type == "Movie" or media_type == "TV Series" :
            result = search_movies_and_series(search_query, media_type, release_date)
        elif media_type == "Book":
            result = search_book(search_query)
        else:
            print(f"{media_type} not supported.")
            result = None

        if result:
            to_notion(result, media_type, page_id)
            return None
        return None

    except Exception as e:
        print(f"❌ Error processing '{search_query}': {e}")
        return None

def main():
    start_time = time.time()
    entries = get_all_notion_entries()
    print(f"Found {len(entries)} entries in Notion\'s database.")
    
    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Create a list of futures (tasks to be executed in parallel)
        futures = [executor.submit(search, entry["title"], entry["type"], entry["release_date"], entry["page_id"]) 
                  for entry in entries]

        # Process results as they complete
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            try:
                future.result()  # Get the result of the future (or exception if one was raised)
            except Exception as e:
                print(f"Error processing entry: {e}")

    elapsed_time = time.time() - start_time
    print(f"All entries processed in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()

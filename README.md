# Notion media updater

This python project has as a goal read a notion database, retrieve its contents, and, based on the data written on in
it, fill some useful information.

Currently, it's configured to look for **TV series, movies, games, and ~~books~~**
The sources are:
- **Movies and TV shows:** [TMDB](https://www.themoviedb.org/)
- **Games:** [IGDB](https://www.igdb.com/) and [RAWG](https://rawg.io/)
- ~~**Books:** [Olen Library](https://openlibrary.org/),
[Google books](https://books.google.com/?) and [GoodReads](https://www.goodreads.com/)\*~~

## ToDo:

- [X] Implement and test APIs
  - [X] TV and movies
  - [X] Games
  - [ ] ~~Books~~
- [ ] Improve data search
  - [X] TV and movies
  - [ ] Games
  - [ ] ~~Books~~
- [X] Create a Notion model
- [ ] Prepare model
- [ ] Make the fields optional
- [ ] Optimize and limit API calls
- [ ] Upload local reviews to Letterboxd
- [ ] ~~Publish Notion connectio~~
- [ ] ~~Automate adding databases~~


Some of these tasks are way harder to implement than I thought, and I don't have the recourses to do them right now.
For now, this will only be a local project that you need to input the API keys and else to use.

## How to use (may change)

1. Make a copy of [this](about:blank) database
2. Create a private notion integration in [this](https://www.notion.so/my-integrations) link
3. Connect your integration as a connection to the copied database.
4. Create and fill the ```.env``` file as described below
5. Run ```database.py```
6. Done

## Environment variables

There are some things that need to be done before using this code, you will need to get the following keys in these
websites:
- [TMDB](https://www.themoviedb.org/login?to=read_me&redirect=%2Freference%2Fintro%2Fgetting-started)
- [IGDB](https://api-docs.igdb.com/#getting-started)
- [RAWG](https://rawg.io/apidocs)

Then, you will need to create a file named ```.env``` in the same folder that this is downloaded, and fill the file
as shown below

```
RAWG_API_KEY = "RAWG key here"
IGDB_CLIENT_ID = "IGDB client key here"
IGDB_CLIENT_SECRET = "IGDB client secret here"
TMDB_API_KEY = "TMDB key here" 

NOTION_TOKEN = "ntn_XXXXXXXXXXXXXXX"
PAGE_ID = "Page ID here"
DATABASE_ID = "your ID here"
```

## Notes

For now, this is only a local side-project, the Notion's connection is not public, and it's my first time really
meddling with APIs and even Notion at all. If anybody more experienced wants to help of even use this to improve
this code, you are welcome, but I'll keep trying to make this work

Most of the implementations are not in their best shape yet, but the books
one is almost completely broken, if you want to use it, I can't recommend
enough for you to BACK UP YOUR DATABASE before trying iy (even though, if you're
able to get the API keys to activate it, you probably have more knowledge in
this than me:P)     

(A lot of this code was developed by Claude AI, but I rewrote most of it and pieced it together, I may try to
remake it without Claude's)

## About book support

Games, movies, and series are easy to search as they don't have a lot of different versions, but the same book
can have thousands of versions.

Because of this, books like Percy Jackson and The lightning thief return A LOT of results, with the first release not
even showing depending on how it was searched. Some of the results are were:
- The Lightning Thief
- Percy Jackson and the Olympians: The Lightning Thief
- Percy Jackson and the Olympians: The Lightning Thief (Book 1)
- Percy Jackson and the Olympians: The Lightning Thief (Graphic Novel)
- Percy Jackson and the Olympians: The Lightning Thief (Book 1) (Graphic Novel)
- ...

Because of this, and demands from college, the search for books is not in the best shape, so I decided to
remove it for now.

The code is open and won't be deleted, and you are invited to try finding a way that makes everyone happy and has
good results.
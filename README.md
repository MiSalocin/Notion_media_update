# Notion media updater

This python project has as objective read an notion database, retrieve it's
contents, and, based on the data written on in it, fill some useful information.

Currently, it's configured to look for **TV series, movies, games and ~~books~~**
The sources are:
- **Movies and TV shows:** [TMDB](https://www.themoviedb.org/)
- **Games:** [IGDB](https://www.igdb.com/) and [RAWG](https://rawg.io/)
- ~~**Books:** [Olen Library](https://openlibrary.org/),
[Google books](https://books.google.com/?) and [GoodReads](https://www.goodreads.com/)\*~~

## ToDo:

- [ ] Implement and test APIs
  - [X] TV and movies
  - [X] Games
  - [ ] ~~Books~~
- [ ] Improve data search
  - [X] TV and movies
  - [ ] Games
  - [ ] ~~Books~~
- [ ] Create Notion model
- [ ] Publish Notion connection
- [ ] Automate adding databases
- [ ] Prepare model, connection and form
- [ ] Make it public
- [ ] Make the fields optional
- [ ] Optimize and limit API calls
- [ ] Upload local reviews to Letterboxd


## How to use (may change)

1. Make a copy of [this](about:blank) database
2. Create a private notion integration in [this](https://www.notion.so/my-integrations) link
3. Connect your integration as a connection to the copied database.
4. Create and fill the ```.env``` file as described below
5. Run ```database.py```
6. Done

## Environment variables

There are some things that need to be done before using this code, you will need to get the following keys in these websites:
- [TMDB](https://www.themoviedb.org/login?to=read_me&redirect=%2Freference%2Fintro%2Fgetting-started)
- [IGDB](https://api-docs.igdb.com/#getting-started)
- [RAWG](https://rawg.io/apidocs)

Then, you will need to create a file named ```.env``` in the same folder that this is downloaded, and fill the file as shown below

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

For now, this is only a local side-project, the Notion's connection is not public and it's my first time really meddling with APIs and even Notion at all. If anybody more experienced want to help of even use this to improve this code, you are  welcome, but I'll keep trying to make this work

Most of the implementations are not in their best shape yet, but the books
one is almost completely broken, if you want to use it, I can't recommend
enough for you to BACK UP YOUR DATABASE before trying iy (even though, if you're
able to get the API keys to activate it, you probably have more knowledge in
this than me :P)     

## About book support

Games, movies and series are not that hard, they don't have a lot of different versions, but the same book can have thousands of versions and even re-releases as graphic novels, with or without the name of the series and the rest

Because of this, books like Percy Jackson and The lightning thief return A LOT of results, with the first release not even showing depending on how it was searched. 

For that reason and, you know, collage, I will end the inclusion of books, but the code is open and won't be deleted, and you are invited to try finding a way that makes everyone happy and has good results.
# Notion media updater

This python project has as objective read an notion database, retrieve it's
contents, and, based on the data written on in it, fill some useful information.

Currently, it's configured to look for **TV series, movies, games and books**
The sources are:
- **Movies and TV shows:** [TMDB](https://www.themoviedb.org/)
- **Games:** [IGDB](https://www.igdb.com/) and [RAWG](https://rawg.io/)
- **Books:** [Olen Library](https://openlibrary.org/),
[Google books](https://books.google.com/?) and [GoodReads](https://www.goodreads.com/)\*

## Todo:
- [ ] Implement and test APIs
  - [X] TV and Movies
  - [X] Games
  - [ ] Books
- [ ] Add search by date feature
  - [X] TMDB
  - [ ] Games
  - [ ] Books

## Notes

For now, this is only a local side-project, the Notion's connection is not
public and it's my first time really meddling with APIs and even Notion at all.
If anybody more experienced want to help of even use this to improve this
code, you are  welcome, but I'll keep trying to make this work

Most of the implementations are not in their best shape yet, but the books
one is almost completely broken, if you want to use it, I can't recommend
enough for you to BACK UP YOUR DATABASE before trying iy (even though, if you're
able to get the API keys to activate it, you probably have more knowledge in
this than me :P)     